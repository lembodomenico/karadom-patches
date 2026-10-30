# 226 - editor tempi completo con i MIDI
import os
import re
import shutil
from tkinter import filedialog, messagebox

import mido

import moduli.karaoke_editor as _ke
KaraokeTimestampEditor = _ke.__dict__.setdefault('_orig226', _ke.KaraokeTimestampEditor)
from moduli.syncro_text import _split_syllables

_VER = 2


class _Suono:
    """Play nell'editor con il BASS gia' acceso da KaraDom e il suo banco suoni."""
    def __init__(self):
        import ctypes as C
        self.C = C
        self.ok = False
        self.stream = 0
        self.font = 0
        try:
            from moduli import bass_engine as be
            eng = be.get_bass_engine()
            if not eng.initialized:
                eng.initialize()
            d = be._lib._dll_dir or be._lib.find_dll_dir()
            self.bass = C.WinDLL(os.path.join(d, 'bass.dll'))
            self.midi = C.WinDLL(os.path.join(d, 'bassmidi.dll'))
        except Exception as e:
            print('[226] audio non disponibile: %s' % e)
            return
        D, Q = C.c_uint32, C.c_uint64
        self.midi.BASS_MIDI_FontInit.restype = D
        self.midi.BASS_MIDI_FontInit.argtypes = [C.c_wchar_p, D]
        self.midi.BASS_MIDI_StreamCreateFile.restype = D
        self.midi.BASS_MIDI_StreamCreateFile.argtypes = [C.c_int, C.c_wchar_p, Q, Q, D, D]
        self.midi.BASS_MIDI_StreamSetFonts.argtypes = [D, C.c_void_p, D]
        self.bass.BASS_ChannelPlay.argtypes = [D, C.c_int]
        self.bass.BASS_ChannelStop.argtypes = [D]
        self.bass.BASS_StreamFree.argtypes = [D]
        self.bass.BASS_ChannelIsActive.argtypes = [D]
        self.bass.BASS_ChannelIsActive.restype = D
        self.bass.BASS_ChannelGetPosition.restype = Q
        self.bass.BASS_ChannelGetPosition.argtypes = [D, D]
        self.font = getattr(eng, '_font', 0) or 0
        if not self.font:
            sf = getattr(eng, 'soundfont_path', None)
            if sf and os.path.exists(sf):
                self.font = self.midi.BASS_MIDI_FontInit(sf, 0x80000000) or 0
        self.ok = True

    def play_file(self, percorso):
        if not self.ok:
            return False
        C = self.C
        self.stop()
        self.stream = self.midi.BASS_MIDI_StreamCreateFile(0, percorso, 0, 0, 0x80000000, 0)
        if not self.stream:
            return False
        if self.font:
            class FONT(C.Structure):
                _fields_ = [("font", C.c_uint32), ("preset", C.c_int), ("bank", C.c_int)]
            fonts = (FONT * 1)(FONT(self.font, -1, 0))
            self.midi.BASS_MIDI_StreamSetFonts(self.stream, fonts, 1)
        self.bass.BASS_ChannelPlay(self.stream, 0)
        return True

    def stop(self):
        if self.stream:
            try:
                self.bass.BASS_ChannelStop(self.stream)
                self.bass.BASS_StreamFree(self.stream)
            except Exception:
                pass
            self.stream = 0

    def is_playing(self):
        if not self.stream:
            return False
        try:
            return self.bass.BASS_ChannelIsActive(self.stream) == 1
        except Exception:
            return False

    def tick_pos(self):
        if not self.stream:
            return 0
        try:
            return int(self.bass.BASS_ChannelGetPosition(self.stream, 2))
        except Exception:
            return 0


EST_MIDI = ('.mid', '.midi', '.kar')


# ---------- tempi: tick <-> ms con la tempo map ----------
def _mappa_tempi(mid):
    cambi = []
    for t in mid.tracks:
        tick = 0
        for e in t:
            tick += e.time
            if e.type == 'set_tempo':
                cambi.append((tick, e.tempo))
    cambi.sort()
    if not cambi or cambi[0][0] > 0:
        cambi.insert(0, (0, 500000))
    tpb = mid.ticks_per_beat or 480
    seg = []                                  # (tick, ms_inizio, us_per_beat)
    ms = 0.0
    for i, (tk, tp) in enumerate(cambi):
        if i:
            ptk, _, ptp = seg[-1]
            ms += (tk - ptk) * ptp / tpb / 1000.0
        seg.append((tk, ms, tp))
    return seg, tpb


def tick2ms(seg, tpb, tick):
    s = seg[0]
    for x in seg:
        if x[0] <= tick:
            s = x
        else:
            break
    return int(round(s[1] + (tick - s[0]) * s[2] / tpb / 1000.0))


def ms2tick(seg, tpb, ms):
    s = seg[0]
    for x in seg:
        if x[1] <= ms:
            s = x
        else:
            break
    return max(0, int(round(s[0] + (ms - s[1]) * 1000.0 * tpb / s[2])))


# ---------- testo nel MIDI ----------
def _sorgente_testo(mid):
    """(tipo, indice traccia): dove sta il testo da editare.
    Soft Karaoke (TEXT nella traccia con '@K' / 'Words') vince sui lyrics."""
    conta = {}
    for ti, t in enumerate(mid.tracks):
        kar = any(e.type == 'text' and e.text.startswith('@K') for e in t)
        for e in t:
            if e.type in ('lyrics', 'text') and e.text and not e.text.startswith('@') \
                    and not e.text.startswith('%'):
                k = (e.type, ti)
                conta[k] = conta.get(k, 0) + (1000 if (kar and e.type == 'text') else 1)
    if not conta:
        return None
    return max(conta, key=conta.get)


def _da_midi(testo, tipo):
    """testo dell'evento MIDI -> testo stile SYLT ('\\n' davanti = a capo)."""
    x = testo.replace('\x00', '')
    if tipo == 'text':
        if x[:1] in ('/', '\\'):
            return '\n' + x[1:]
        return x
    # lyrics: l'a capo puo' essere in coda alla sillaba precedente o in testa
    capo = x[:1] in ('\r', '\n', '/', '\\')
    x = x.lstrip('\r\n/\\')
    return ('\n' if capo else '') + x


def voci_da_midi(mid):
    """[[testo, ms], ...], (tipo, traccia) del testo del MIDI ([] e None se non c'e')."""
    src = _sorgente_testo(mid)
    if not src:
        return [], None
    tipo, ti = src
    seg, tpb = _mappa_tempi(mid)
    voci = []
    capi = 0                     # a capo in attesa: 2+ = righe vuote (strofa nuova)
    tick = 0
    for e in mid.tracks[ti]:
        tick += e.time
        if e.type != tipo or not e.text or e.text.startswith('@') or e.text.startswith('%'):
            continue
        s = e.text.replace('\x00', '').replace('\r\n', '\r')
        dopo = 0
        if tipo == 'text':       # Soft Karaoke: '/' a capo, '\' strofa nuova
            if s[:1] == '\\':
                capi, s = capi + 2, s[1:]
            elif s[:1] == '/':
                capi, s = capi + 1, s[1:]
        else:                    # Lyrics: '\r' davanti, dietro o da solo (MLive)
            while s[:1] in ('\r', '\n', '/', '\\') and s:
                capi, s = capi + 1, s[1:]
            while s[-1:] in ('\r', '\n') and s:
                dopo, s = dopo + 1, s[:-1]
        if not s.strip():                      # evento solo "a capo"
            capi += dopo
            continue
        voci.append(['\n' * capi + s, tick2ms(seg, tpb, tick)])
        capi = dopo
    return voci, src


# ---------- testo da TXT / LRC ----------
_RE_RIGA = re.compile(r'\[(\d+):(\d+(?:[.:]\d+)?)\]')
_RE_PAROLA = re.compile(r'<(\d+):(\d+(?:[.:]\d+)?)>')
_RE_META = re.compile(r'^\[[a-zA-Z#]+:.*\]$')


def _ms(m, sec):
    return int(round((int(m) * 60 + float(sec.replace(':', '.'))) * 1000))


def leggi_testo(percorso):
    """TXT o LRC -> righe [(ms_riga|None, [(ms_parola|None, parola), ...]), ...]"""
    raw = open(percorso, 'rb').read()
    testo = None
    for enc in ('utf-8-sig', 'cp1252', 'latin-1'):
        try:
            testo = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    righe = []
    vuote = 0                                          # righe vuote = stacco di strofa
    for r in testo.splitlines():
        r = r.strip()
        if not r:
            vuote += 1 if righe else 0
            continue
        if _RE_META.match(r):
            continue
        tempi = []
        while True:                                    # [00:12.34][01:02.00] testo (ritornelli)
            m = _RE_RIGA.match(r)
            if not m:
                break
            tempi.append(_ms(m.group(1), m.group(2)))
            r = r[m.end():].lstrip()
        parole, t = [], None
        for pezzo in re.split(r'(<\d+:\d+(?:[.:]\d+)?>)', r):
            m = _RE_PAROLA.fullmatch(pezzo)
            if m:
                t = _ms(m.group(1), m.group(2))
                continue
            for w in pezzo.split():
                parole.append((t, w))
                t = None
        if not parole:
            continue
        for tr in (tempi or [None]):
            righe.append((tr, parole, min(vuote, 1)))
        vuote = 0
    if any(x[0] is not None for x in righe):
        righe.sort(key=lambda x: (x[0] is None, x[0] or 0))
    return righe


def righe_a_sillabe(righe):
    """Sillabe come le fa KaraDom (a capo davanti alla 1a sillaba della riga,
    spazio a fine parola).
    TXT (senza tempi): sillabe a 300 ms una dall'altra, da rifare col 'Tempo qui'.
    LRC: dentro la riga si spalmano fino alla riga dopo (max 350 ms a sillaba);
    LRC 'enhanced' (<mm:ss.xx> per parola): ogni parola parte al suo tempo."""
    voci = []
    cursore = 1000
    for i, riga in enumerate(righe):
        t0, parole = riga[0], riga[1]
        vuote = riga[2] if len(riga) > 2 else 0
        sill = []
        for wi, (tw, w) in enumerate(parole):
            ss = _split_syllables(w) or [w]
            for si, x in enumerate(ss):
                fine = si == len(ss) - 1
                sill.append([x + (' ' if fine and wi < len(parole) - 1 else ''), tw if si == 0 else None])
        if voci:
            sill[0][0] = '\n' * (1 + vuote) + sill[0][0]
        if t0 is None and sill[0][1] is None:
            for k, x in enumerate(sill):
                x[1] = cursore + 300 * k
        else:
            if sill[0][1] is None:
                sill[0][1] = t0
            prossima = next((r[0] for r in righe[i + 1:] if r[0] is not None), None)
            fine = prossima if prossima is not None else sill[0][1] + 350 * (len(sill) + 1)
            ancore = [k for k, x in enumerate(sill) if x[1] is not None]
            for a, b in zip(ancore, ancore[1:] + [None]):
                ta = sill[a][1]
                if b is not None:
                    passo = (sill[b][1] - ta) / (b - a)
                    n = b
                else:
                    n = len(sill)
                    passo = min(350.0, (fine - ta) / (n - a + 1)) if n - a > 1 else 0
                for k in range(a + 1, n):
                    sill[k][1] = int(ta + passo * (k - a))
        cursore = sill[-1][1] + 900
        voci.extend(sill)
    prima = -1
    for v in voci:                                    # tempi sempre in avanti
        v[1] = max(int(v[1]), prima + 1)
        prima = v[1]
    return voci


class _Lettore(KaraokeTimestampEditor):
    """Solo per LEGGERE il testo di un altro MP3 (SYLT / WL5), senza finestra."""
    def __init__(self):
        self.id3_frames, self.sylt_entries = [], []
        self.sylt_header = self.audio_data = None
        self.id3_version, self.id3_flags = (3, 0), 0
        self.wl5_prefix = self.wl5_suffix = b''


def voci_da_file(percorso):
    """Testo con tempi da qualunque formato: MIDI/KAR, MP3 SYLT/WL5, LRC, TXT."""
    est = os.path.splitext(percorso)[1].lower()
    if est in EST_MIDI:
        return voci_da_midi(mido.MidiFile(percorso, clip=True))[0]
    if est == '.mp3':
        raw = open(percorso, 'rb').read()
        lt = _Lettore()
        if b'<WL5SYNCT>' in raw:
            lt._parse_wl5(raw)
        else:
            lt._parse_id3(raw)
        return [list(x) for x in lt.sylt_entries]
    return righe_a_sillabe(leggi_testo(percorso))


class EditorTempiMidi(KaraokeTimestampEditor):
    _open_instance = None

    def _on_close(self):
        try:
            self.stop_midi()
        except Exception:
            pass
        if EditorTempiMidi._open_instance is self:
            EditorTempiMidi._open_instance = None
        super()._on_close()

    def __init__(self, root, filepath=None, on_save_callback=None):
        self.midi = None
        self.midi_src = None
        self.player = None
        self._play_after = None
        self._riga_suona = None
        super().__init__(root, filepath=filepath, on_save_callback=on_save_callback)
        EditorTempiMidi._open_instance = self
        self.root.title("Editor Testo / Tempi — MIDI / KAR (anche MP3 SYLT)")
        self._integra_midi()

    # ---------- integrazione MIDI nella finestra di KaraDom ----------
    def _integra_midi(self):
        import tkinter as tk
        from moduli.ui_scale import S, F
        C = self.colors
        cambi = {
            "🎤 SYLT Editor": "🎤 Editor Testo / Tempi",
            "Editor timestamp karaoke MP3": "parole e tempi (TS) dei MIDI / KAR — anche MP3 SYLT",
            "💾 SALVA MP3": "💾 SALVA",
            "(Invio per applicare, salva con SALVA MP3)": "(Invio per applicare, poi SALVA)",
        }

        def giro(w):
            for c in w.winfo_children():
                try:
                    t = c.cget('text')
                    if t in cambi:
                        c.config(text=cambi[t])
                except Exception:
                    pass
                if isinstance(c, tk.OptionMenu):
                    c['menu'].insert_command(0, label="MIDI / KAR",
                                             command=tk._setit(self.format_var, "MIDI / KAR",
                                                               self._on_format_change))
                giro(c)
        giro(self.root)
        self.format_var.set("MIDI / KAR")
        if not self.current_file:
            self.status_var.set("Pronto — Apri un MIDI / KAR (o un MP3 con SYLT)")
            self.file_label.config(text="📁 Clicca per aprire un MIDI / KAR")

        # barra di ascolto: Play del MIDI, sillaba che si colora, tempo a orecchio
        bar = tk.Frame(self.root, bg=C['bg_medium'])
        bar.pack(fill='x', padx=S(20), pady=(0, 5), after=self.file_frame)

        def bt(txt, cmd, col):
            b = tk.Button(bar, text=txt, command=cmd, bg=col, fg='white', relief='flat',
                          font=F('Segoe UI', 11, 'bold'), padx=S(12), pady=S(4), cursor='hand2',
                          activebackground=C['accent_hover'], activeforeground='white')
            b.pack(side='left', padx=S(4), pady=S(5))
            return b
        bt("▶ Play", self.play_midi, '#2f9e44')
        bt("▶ Dalla sillaba", lambda: self.play_midi(dalla_sel=True), '#2b8a3e')
        bt("■ Stop", self.stop_midi, '#c92a2a')
        bt("⏱ Tempo qui  (F5 / Spazio)", self.tempo_qui, C['accent'])
        bt("📄 Inserisci testo  (TXT / LRC / MP3 / MID)", self.inserisci_testo, '#1f4068')
        self.lbl_pos = tk.Label(bar, text="0:00.000", bg=C['bg_medium'], fg='white',
                                font=F('Consolas', 16, 'bold'))
        self.lbl_pos.pack(side='left', padx=S(16))
        tk.Label(bar, text="Mentre suona: seleziona la sillaba e premi F5/Spazio "
                           "quando va cantata → prende il tempo e passa alla successiva",
                 bg=C['bg_medium'], fg='white', font=F('Segoe UI', 10)).pack(side='left', padx=S(8))
        self.tree.tag_configure('suona', background='#f0a500', foreground='#000000')
        self.root.bind('<F5>', lambda e: self.tempo_qui())
        self.tree.bind('<space>', lambda e: (self.tempo_qui(), 'break')[1])

    def inserisci_testo(self, fp=None):
        """Mette il testo da un TXT o LRC, oppure lo COPIA (coi tempi) da un altro
        MP3 SYLT/WL5 o MID/KAR. Sostituisce il testo attuale (annullabile con Ctrl+Z)."""
        if not self.current_file:
            messagebox.showinfo("Inserisci testo", "Apri prima il file a cui mettere il testo.")
            return
        if not fp:
            fp = filedialog.askopenfilename(
                title="Testo da inserire",
                filetypes=[("Testo / LRC / MP3 / MIDI", "*.txt *.lrc *.mp3 *.mid *.midi *.kar"),
                           ("TXT / LRC", "*.txt *.lrc"), ("MP3", "*.mp3"),
                           ("MIDI / KAR", "*.mid *.midi *.kar"), ("Tutti", "*.*")])
        if not fp:
            return
        try:
            voci = voci_da_file(fp)
        except Exception as e:
            messagebox.showerror("Inserisci testo", f"File non leggibile:\n{e}")
            return
        if not voci:
            messagebox.showwarning("Inserisci testo", "In quel file non c'e' testo.")
            return
        if self.sylt_entries and not messagebox.askyesno(
                "Inserisci testo", f"Sostituire le {len(self.sylt_entries)} sillabe attuali "
                                   f"con le {len(voci)} di '{os.path.basename(fp)}'?\n(Ctrl+Z per tornare indietro)"):
            return
        self._push_undo()
        self.sylt_entries = voci
        self.modified = True
        if self.file_format == 'midi':
            self._testo_inserito = True          # al salvataggio: formato MLive
        self._refresh_tree()
        self._update_info()
        senza_tempi = False
        if fp.lower().endswith(('.txt', '.lrc')):
            senza_tempi = not _RE_RIGA.search(open(fp, 'rb').read().decode('latin-1'))
        if senza_tempi:
            self.status_var.set(f"Testo inserito: {len(voci)} sillabe SENZA tempi → Play, seleziona la 1ª "
                                f"sillaba e batti F5/Spazio a tempo. Poi SALVA.")
        else:
            self.status_var.set(f"Testo inserito da {os.path.basename(fp)}: {len(voci)} sillabe coi tempi. "
                                f"Controlla col Play, poi SALVA.")

    def play_midi(self, dalla_sel=False):
        """Play per TUTTI i formati: MIDI/KAR con BASSMIDI, MP3 (SYLT/WL5SYNCT) con BASS."""
        if not self.current_file:
            messagebox.showinfo("Play", "Apri prima un file (MIDI / KAR o MP3).")
            return
        self.stop_midi()
        if self.player is None:
            self.player = _Suono()
        if not self.player.ok:
            messagebox.showwarning("Play", "Audio MIDI di KaraDom non disponibile.")
            return
        import ctypes as Cc
        b = self.player.bass
        D, Q = Cc.c_uint32, Cc.c_uint64
        b.BASS_ChannelSetPosition.argtypes = [D, Q, D]
        da_ms = 0
        if dalla_sel:
            sel = self.tree.selection()
            if sel:
                da_ms = max(0, self.sylt_entries[int(sel[0])][1] - 1500)   # 1,5 s prima
        if self.file_format == 'midi':
            if not self.player.play_file(self.current_file):
                messagebox.showwarning("Play", "Riproduzione non partita (SoundFont?).")
                return
            self._seg = _mappa_tempi(self.midi)
            if da_ms:
                seg, tpb = self._seg
                b.BASS_ChannelSetPosition(self.player.stream, ms2tick(seg, tpb, da_ms), 2)  # POS_MIDI_TICK
        else:
            # MP3 (SYLT / WL5SYNCT): stream audio normale
            b.BASS_StreamCreateFile.restype = D
            b.BASS_StreamCreateFile.argtypes = [Cc.c_int, Cc.c_wchar_p, Q, Q, D]
            b.BASS_ChannelBytes2Seconds.restype = Cc.c_double
            b.BASS_ChannelBytes2Seconds.argtypes = [D, Q]
            b.BASS_ChannelSeconds2Bytes.restype = Q
            b.BASS_ChannelSeconds2Bytes.argtypes = [D, Cc.c_double]
            st = b.BASS_StreamCreateFile(0, self.current_file, 0, 0, 0x80000000)   # BASS_UNICODE
            if not st:
                messagebox.showwarning("Play", "MP3 non riproducibile.")
                return
            self.player.stream = st
            if da_ms:
                b.BASS_ChannelSetPosition(st, b.BASS_ChannelSeconds2Bytes(st, da_ms / 1000.0), 0)
            b.BASS_ChannelPlay(st, 0)
        self._giro_play()

    def stop_midi(self):
        if self._play_after:
            try:
                self.root.after_cancel(self._play_after)
            except Exception:
                pass
            self._play_after = None
        if self.player:
            self.player.stop()
        self._colora_riga(None)

    def pos_ms(self):
        if not self.player or not self.player.stream:
            return None
        if self.file_format == 'midi':
            seg, tpb = self._seg
            return tick2ms(seg, tpb, self.player.tick_pos())
        b = self.player.bass
        st = self.player.stream
        return int(b.BASS_ChannelBytes2Seconds(st, b.BASS_ChannelGetPosition(st, 0)) * 1000)

    def _colora_riga(self, idx):
        if idx == self._riga_suona:
            return
        if self._riga_suona is not None and self.tree.exists(str(self._riga_suona)):
            i = self._riga_suona
            self.tree.item(str(i), tags=('even' if i % 2 == 0 else 'odd',))
        self._riga_suona = idx
        if idx is not None and self.tree.exists(str(idx)):
            self.tree.item(str(idx), tags=('suona',))
            self._centra(str(idx))

    def _centra(self, iid):
        """[30-10-2026] La riga resta al CENTRO della lista: con see() finiva sul bordo e non si vedeva."""
        tv = self.tree
        try:
            n = len(tv.get_children())
            if not n:
                return
            i = tv.index(iid)
            tv.update_idletasks()
            top, bot = tv.yview()
            vis = max(1, int(round((bot - top) * n)))
            primo = max(0, min(i - vis // 2, n - vis))
            tv.yview_moveto(primo / n)
        except Exception:
            tv.see(iid)

    def _giro_play(self):
        if not self.player or not self.player.is_playing():
            self.stop_midi()
            return
        ms = self.pos_ms() or 0
        self.lbl_pos.config(text=self._fmt_time(ms))
        idx = None
        for i, (_, ts) in enumerate(self.sylt_entries):
            if ts <= ms:
                idx = i
            else:
                break
        self._colora_riga(idx)
        self._play_after = self.root.after(40, self._giro_play)

    def tempo_qui(self):
        """La sillaba selezionata prende il tempo di adesso; si passa alla successiva."""
        ms = self.pos_ms()
        sel = self.tree.selection()
        if ms is None or not sel:
            self.status_var.set("Per il tempo a orecchio: Play, seleziona la sillaba, poi F5 / Spazio")
            return
        i = int(sel[0])
        self._push_undo()
        self.sylt_entries[i][1] = int(ms)
        self.modified = True
        t = self.sylt_entries[i][0].replace('\n', '↵').replace('\r', '')
        self.tree.item(str(i), values=(i + 1, t, int(ms), self._fmt_time(int(ms))))
        if i + 1 < len(self.sylt_entries):
            self.tree.selection_set(str(i + 1))
            self.tree.focus(str(i + 1))
            self._centra(str(i + 1))
        self.status_var.set(f"Sillaba {i + 1} '{t.strip()}' → {self._fmt_time(int(ms))}")

    def _update_info(self):
        super()._update_info()
        if self.file_format == 'midi' and self.sylt_entries:
            self.lbl_duration.config(text="MIDI: %s  (testo: %s)" % (
                self._fmt_time(self._mp3_dur()), self._fmt_time(self.sylt_entries[-1][1])))

    # apertura: MIDI, oppure MP3 come in KaraDom
    def browse_file(self):
        fp = filedialog.askopenfilename(
            title="Apri MIDI / KAR / MP3",
            filetypes=[("MIDI / KAR / MP3", "*.mid *.midi *.kar *.mp3"),
                       ("MIDI / KAR", "*.mid *.midi *.kar"), ("MP3", "*.mp3"), ("Tutti", "*.*")])
        if fp:
            self.load_file(fp)

    def load_file(self, filepath):
        if not filepath.lower().endswith(EST_MIDI):
            self.midi = None
            self.stop_midi()
            try:
                with open(filepath, 'rb') as f:
                    wl5 = b'<WL5SYNCT>' in f.read()
            except OSError:
                wl5 = False
            self.format_var.set("WL5SYNCT" if wl5 else "SYLT")
            with open(filepath, 'rb') as f:
                raw = f.read()
            if not wl5 and not (raw[:3] == b'ID3' and b'SYLT' in raw[:100000]):
                # MP3 ancora senza testo: si apre vuoto, il testo si mette con 'Inserisci testo'
                self.mp3_data, self.id3_frames, self.sylt_header = raw, [], None
                self.sylt_entries, self.wl5_prefix, self.wl5_suffix = [], b'', b''
                self.undo_stack.clear()
                self.redo_stack.clear()
                self._parse_id3(raw)
                self.file_format, self.current_file, self.modified = 'sylt', filepath, False
                self.file_label.config(text=f"📁 {os.path.basename(filepath)} [MP3 — senza testo]",
                                       fg=self.colors['success'])
                self._refresh_tree()
                self._update_info()
                self.status_var.set("MP3 senza testo: usa '📄 Inserisci testo' per metterlo")
                return
            return super().load_file(filepath)
        self.stop_midi()
        self.format_var.set("MIDI / KAR")
        try:
            mid = mido.MidiFile(filepath, clip=True)
        except Exception as e:
            messagebox.showerror("Errore", f"MIDI non leggibile:\n{e}")
            return
        voci, src = voci_da_midi(mid)
        if not src:
            self.status_var.set("MIDI senza testo: usa '📄 Inserisci testo' per metterlo")
        self.midi, self.midi_src = mid, src
        self._testo_inserito = False
        self.sylt_entries = voci
        self.mp3_data = self.audio_data = None
        self.file_format = 'midi'
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.modified = False
        self.current_file = filepath
        tipo_l = ('senza testo' if not src else
                  'KAR (Soft Karaoke)' if src[0] == 'text' else 'Lyrics')
        self.file_label.config(text=f"📁 {os.path.basename(filepath)} [MIDI — {tipo_l}]",
                               fg=self.colors['success'])
        self._refresh_tree()
        self._update_info()
        if src:
            self.status_var.set(f"Caricato: {filepath} ({len(voci)} sillabe, MIDI {tipo_l}, traccia {src[1] + 1})")

    def _mp3_dur(self):
        if self.file_format == 'midi' and self.midi is not None:
            try:
                return int(self.midi.length * 1000)
            except Exception:
                return 0
        return super()._mp3_dur()

    def save_file_as(self):
        if self.file_format != 'midi':
            return super().save_file_as()
        self._apply_pending_edit()
        est = os.path.splitext(self.current_file)[1] if self.current_file else '.mid'
        fp = filedialog.asksaveasfilename(
            title="Salva MIDI", defaultextension=est,
            filetypes=[("MIDI / KAR", "*.mid *.kar *.midi")],
            initialfile=os.path.basename(self.current_file) if self.current_file else "output.mid")
        if fp:
            self._save_to(fp)

    def _save_sylt(self, filepath):
        # _save_to di KaraDom chiama _save_sylt per tutto cio' che non e' WL5
        if self.file_format == 'midi':
            return self._salva_midi(filepath)
        return super()._save_sylt(filepath)

    def _salva_midi(self, filepath):
        """Riscrive SOLO gli eventi di testo. La struttura del MIDI resta intatta:
        stesso tipo, stesse tracce, stessi eventi (note, tempi, sysex...).
          - testo INSERITO/copiato (o MIDI che non l'aveva): stile MLive
            (riferimento 'Giorgia - Come saprei_(MLive).mid'): LYRIC FF 05,
            sillabe MAIUSCOLE, spazio a fine parola, a capo = LYRIC a se' '\\r'
            (2+ di fila = riga vuota), nella traccia dove stava il testo
            (o nella prima se non ce n'era);
          - testo GIA' presente e solo corretto (anche aggiungendo/togliendo
            sillabe o righe): resta nel SUO stile; gli a capo separati restano
            separati e, riga per riga, ai tick di prima."""
        mid = self.midi
        seg, tpb = _mappa_tempi(mid)
        if os.path.abspath(filepath) == os.path.abspath(self.current_file or ''):
            b, e = os.path.splitext(filepath)
            orig = b + '.orig' + e
            if os.path.exists(filepath) and not os.path.exists(orig):
                shutil.copy2(filepath, orig)
        nuovo_testo = getattr(self, '_testo_inserito', False) or not self.midi_src
        tipo_v, ti = self.midi_src if self.midi_src else (None, 0)

        def e_testo(e):
            if e.type == 'lyrics':
                return tipo_v == 'lyrics' or nuovo_testo
            if e.type == 'text' and e.text and tipo_v == 'text':
                # testo nuovo: via tutto il Soft Karaoke vecchio, firma @K compresa
                return nuovo_testo or not e.text.startswith('@')
            return False

        if nuovo_testo:                             # testo nuovo: via quello vecchio da TUTTE le tracce
            for tj, t in enumerate(mid.tracks):
                if tj == ti:
                    continue
                nt, att = mido.MidiTrack(), 0
                for e in t:
                    if e.type == 'lyrics' or (e.type == 'text' and tipo_v == 'text'
                                              and e.text.startswith('@')):     # solo intestazioni karaoke
                        att += e.time
                        continue
                    nt.append(e.copy(time=e.time + att))
                    att = 0
                mid.tracks[tj] = nt

        # traccia del testo: eventi assoluti senza il vecchio testo
        # gruppi_vecchi = a capo "da soli" (stile MLive), un gruppo per fine riga:
        # i '\r' di fila (riga vuota) stanno a tick diversi ma sono UNA fine riga
        assoluti, gruppi_vecchi, tick, era_capo = [], [], 0, False
        for e in mid.tracks[ti]:
            tick += e.time
            if e_testo(e):
                if e.type == 'lyrics':
                    solo_capo = '\r' in e.text and not e.text.replace(chr(0), '').strip(' \r\n')
                    if solo_capo:
                        if era_capo:
                            gruppi_vecchi[-1].append(tick)
                        else:
                            gruppi_vecchi.append([tick])
                    era_capo = solo_capo
                continue
            if e.type != 'end_of_track':
                assoluti.append((tick, 0, e))
        fine_traccia = tick

        voci = sorted(self.sylt_entries, key=lambda v: v[1])
        if nuovo_testo:
            tipo, stile = 'lyrics', 'solo'
        else:
            tipo = tipo_v
            stile = 'solo' if (tipo == 'lyrics' and gruppi_vecchi) else 'coda'

        nuovi, riga = [], 0                         # riga = primo gruppo vecchio non ancora usato
        for i, (txt, ms) in enumerate(voci):
            corpo = txt.lstrip('\n').replace('\r', '')
            if nuovo_testo:
                corpo = corpo.upper()
            tk = ms2tick(seg, tpb, ms)
            succ = voci[i + 1][0] if i + 1 < len(voci) else ''
            n_capi = len(succ) - len(succ.lstrip('\n'))
            if i + 1 == len(voci) and stile == 'solo':
                n_capi = 1                                   # chiusura dell'ultima riga
            if tipo == 'text':
                capo_txt = len(txt) - len(txt.lstrip('\n'))
                pre = ('\\' if capo_txt >= 2 else '/') if capo_txt else ''
                nuovi.append((tk, 1, mido.MetaMessage('text', text=pre + corpo)))
                continue
            if stile == 'coda':
                nuovi.append((tk, 1, mido.MetaMessage('lyrics', text=corpo + '\r' * n_capi)))
                continue
            if corpo:
                nuovi.append((tk, 1, mido.MetaMessage('lyrics', text=corpo)))
            if n_capi:
                dopo = ms2tick(seg, tpb, voci[i + 1][1]) if i + 1 < len(voci) else max(tk, fine_traccia)
                t_capo = tk + max(0, dopo - tk) // 4          # come MLive: ~1/4 della pausa
                tempi = [t_capo] * n_capi
                if not nuovo_testo:                           # riga che c'era gia': stessi tick
                    while riga < len(gruppi_vecchi) and gruppi_vecchi[riga][0] < tk:
                        riga += 1                             # gruppi di righe tolte
                    if riga < len(gruppi_vecchi) and gruppi_vecchi[riga][0] <= max(dopo, tk):
                        g = gruppi_vecchi[riga]
                        tempi = g if len(g) == n_capi else [g[0]] * n_capi
                        riga += 1
                for t_c in tempi:
                    nuovi.append((t_c, 2, mido.MetaMessage('lyrics', text='\r')))

        tutti = sorted(assoluti + nuovi, key=lambda x: (x[0], x[1]))
        ultimo = max([x[0] for x in tutti] + [fine_traccia, 0])
        tr = mido.MidiTrack()
        prima = 0
        for tk, _, e in tutti:
            tr.append(e.copy(time=tk - prima))
            prima = tk
        tr.append(mido.MetaMessage('end_of_track', time=ultimo - prima))
        mid.tracks[ti] = tr
        self.midi_src = (tipo, ti)
        self._testo_inserito = False
        tmp = filepath + '.tmp'
        mid.save(tmp)
        if os.path.exists(filepath) and not os.access(filepath, os.W_OK):
            os.chmod(filepath, 0o666)          # molti MIDI scaricati sono "sola lettura"
        try:
            os.replace(tmp, filepath)
        except OSError:
            try:
                os.remove(tmp)
            except OSError:
                pass
            raise

    def convert_to_other_format(self):
        if self.file_format == 'midi':
            messagebox.showinfo("Info", "La conversione SYLT/WL5 vale solo per gli MP3.")
            return
        return super().convert_to_other_format()


def _file_del_brano():
    """Il menu di KaraDom passa al'editor solo gli MP3: il MIDI in corso si prende da qui."""
    import sys
    f = sys._getframe(2)
    for _ in range(4):
        if f is None:
            break
        sistema = f.f_locals.get('system')
        if sistema is not None:
            fp = getattr(sistema, 'current_file', None) or getattr(sistema, '_original_file', None)
            if fp and fp.lower().endswith(EST_MIDI):
                return fp
            return None
        f = f.f_back
    return None


def _apri_singola(cls, parent, filepath=None, on_save_callback=None):
    if not filepath:
        try:
            filepath = _file_del_brano()
        except Exception:
            filepath = None
    return _BASE_APRI.__func__(cls, parent, filepath=filepath, on_save_callback=on_save_callback)


_BASE_APRI = KaraokeTimestampEditor.__dict__['open_singleton']
EditorTempiMidi.open_singleton = classmethod(_apri_singola)



def _titolare():
    """[26-10-2026] Solo sui PC del titolare (licenza Domenico Lembo), come 239/242/245-249."""
    try:
        from moduli.licensing import load_license
        d = load_license() or {}
        return (str(d.get('nome', '')).strip().lower(),
                str(d.get('cognome', '')).strip().lower()) == ('domenico', 'lembo')
    except Exception:
        return False


def apply():
    if not _titolare():
        return False
    try:
        import moduli.karaoke_editor as ke
    except Exception:
        return False
    if getattr(ke, '_ver226', None) == _VER:
        return True
    ke.KaraokeTimestampEditor = EditorTempiMidi
    ke._ver226 = _VER
    print('[226] editor tempi: versione completa con MIDI / KAR')
    return True


def revert():
    return False


try:
    apply()
except Exception:
    pass
