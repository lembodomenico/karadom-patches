# 228 - Editor testi: COPIA / CONVERTI da qualsiasi formato a qualsiasi formato, anche tra file
# Utente 18-10: "nell'editor dei testi metti un bottone con il quale posso copiare da qualsiasi
# formato a qualsiasi formato e tra file".
#   DA:  il testo nell'editor | un altro file (MP3 SYLT/WL5SYNCT, MIDI/KAR, LRC, SRT, TXT) | gli appunti
#   A:   l'editor | gli appunti | un file nuovo (LRC a sillabe, LRC a righe, SRT, TXT)
#        | DENTRO un altro MP3 (SYLT o WL5SYNCT) | DENTRO un altro MIDI/KAR
# Si costruisce sopra l'editor che c'e' (con la 226 eredita MIDI/KAR e Play). Il file di arrivo,
# se esisteva, si salva una volta in <nome>.orig.<est> (come fa la 226 coi MIDI).
import os
import re
import shutil
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

import moduli.karaoke_editor as ke

_VER = 2          # v2 (18-10): un bottone solo 'Copia su altro file' (utente: 'falla facile')

# --- traduzioni (la chiave e' l'italiano, come moduli/lang/en.json) ---
_EN = {
    "📋 Copia su altro file": "📋 Copy to another file",
    "Questo e' il file aperto nell'editor: usa SALVA.": "This is the file open in the editor: use SAVE.",
    "Fatto: {m} sillabe copiate in {f} (copia del file com'era: {o})": "Done: {m} syllables copied into {f} (copy of the original file: {o})",
    "Copia / Converti testo e tempi": "Copy / Convert lyrics and timings",
    "DA": "FROM", "A": "TO",
    "Il testo nell'editor": "The lyrics in the editor",
    "Un altro file (MP3, MIDI/KAR, LRC, SRT, TXT)": "Another file (MP3, MIDI/KAR, LRC, SRT, TXT)",
    "Gli appunti di Windows": "The Windows clipboard",
    "L'editor (sostituisce il testo, poi SALVA)": "The editor (replaces the lyrics, then SAVE)",
    "Gli appunti (per incollarlo altrove)": "The clipboard (to paste it elsewhere)",
    "Un file nuovo": "A new file",
    "Dentro un altro MP3 — SYLT": "Inside another MP3 — SYLT",
    "Dentro un altro MP3 — WL5SYNCT": "Inside another MP3 — WL5SYNCT",
    "Dentro un altro MIDI / KAR": "Inside another MIDI / KAR",
    "Formato (appunti e file nuovo):": "Format (clipboard and new file):",
    "LRC a sillabe (.lrc)": "LRC with syllables (.lrc)", "LRC a righe (.lrc)": "LRC by line (.lrc)",
    "SRT sottotitoli (.srt)": "SRT subtitles (.srt)", "Testo semplice (.txt)": "Plain text (.txt)",
    "Esegui": "Run", "Chiudi": "Close",
    "Copia / Converti": "Copy / Convert",
    "Il testo dell'editor e' vuoto: apri prima un file.": "The editor is empty: open a file first.",
    "DA e A sono la stessa cosa: scegli un'altra destinazione.": "FROM and TO are the same: choose another destination.",
    "File da cui copiare": "File to copy from",
    "Nel file non c'e' testo.": "There are no lyrics in that file.",
    "File non leggibile:\n{e}": "File not readable:\n{e}",
    "Gli appunti sono vuoti.": "The clipboard is empty.",
    "Il MIDI / KAR si legge e si scrive solo con l'editor MIDI di KaraDom (patch 226).":
        "MIDI / KAR needs the KaraDom MIDI editor (patch 226).",
    "Sostituire le {n} sillabe dell'editor con le {m} nuove?\n(Ctrl+Z per tornare indietro)":
        "Replace the {n} syllables in the editor with the {m} new ones?\n(Ctrl+Z to undo)",
    "Fatto: {m} sillabe nell'editor. Controlla col Play, poi SALVA.":
        "Done: {m} syllables in the editor. Check with Play, then SAVE.",
    "Fatto: {m} sillabe copiate negli appunti ({fmt}).": "Done: {m} syllables copied to the clipboard ({fmt}).",
    "Salva come": "Save as",
    "File in cui mettere il testo": "File to put the lyrics into",
    "Fatto: testo scritto in\n{fp}": "Done: lyrics written to\n{fp}",
    "Fatto: testo messo dentro\n{fp}\n\n(copia del file com'era: {orig})": "Done: lyrics put inside\n{fp}\n\n(copy of the original file: {orig})",
    "Errore:\n{e}": "Error:\n{e}",
    "⚠ La sorgente non ha tempi: le sillabe sono a 300 ms l'una, da rifare col Tempo qui.":
        "⚠ The source has no timings: syllables are 300 ms apart, redo them with 'Time here'.",
    "Questo e' il file aperto nell'editor: usa 'L'editor' e poi SALVA.":
        "This is the file open in the editor: use 'The editor' and then SAVE.",
}


def _(s):
    try:
        import moduli.i18n as i18n
        if getattr(i18n, '_current_language', 'it') == 'en':
            return _EN.get(s, s)
        return i18n._(s)
    except Exception:
        return s


try:
    from moduli.syncro_text import _split_syllables
except Exception:                                   # pragma: no cover
    def _split_syllables(w):
        return [w]

FORMATI = [("LRC a sillabe (.lrc)", 'lrc_sill', '.lrc'), ("LRC a righe (.lrc)", 'lrc', '.lrc'),
           ("SRT sottotitoli (.srt)", 'srt', '.srt'), ("Testo semplice (.txt)", 'txt', '.txt')]
EST_MIDI = ('.mid', '.midi', '.kar')


def _m226():
    """Il modulo della 226 (MIDI/KAR), se installata."""
    for c in type.mro(ke.KaraokeTimestampEditor):
        m = sys.modules.get(getattr(c, '__module__', ''))
        if m is not None and hasattr(m, 'voci_da_midi') and hasattr(m, '_mappa_tempi'):
            return m
    return None


# ---------------- scrittura: voci [[testo, ms]] stile SYLT -> formati di testo ----------------
def _mmss(ms):
    cs = int(round(max(0, ms) / 10.0))
    return "%02d:%02d.%02d" % (cs // 6000, (cs // 100) % 60, cs % 100)


def _hms(ms):
    ms = int(max(0, ms))
    return "%02d:%02d:%02d,%03d" % (ms // 3600000, (ms // 60000) % 60, (ms // 1000) % 60, ms % 1000)


def righe_da_voci(voci):
    """[{'ms', 'stacco', 'sill': [(ms, testo)]}]: '\\n' davanti = riga nuova, 2+ = strofa nuova."""
    righe, attesa = [], 0
    for testo, ms in voci:
        testo = (testo or '').replace('\r', '')
        n = len(testo) - len(testo.lstrip('\n'))
        corpo = testo.lstrip('\n')
        attesa += n
        if '\n' in corpo:                            # a capo in coda alla sillaba
            dopo = len(corpo) - len(corpo.rstrip('\n'))
            corpo = corpo.rstrip('\n')
        else:
            dopo = 0
        if corpo.strip() == '' and not corpo:
            continue
        if not righe or attesa:
            righe.append({'ms': int(ms), 'stacco': attesa >= 2 and bool(righe), 'sill': []})
            attesa = 0
        righe[-1]['sill'].append((int(ms), corpo))
        attesa += dopo
    return righe


def _testo_riga(r):
    return re.sub(r'\s+', ' ', ''.join(s for _, s in r['sill'])).strip()


def scrivi(voci, fmt):
    righe = righe_da_voci(voci)
    out = []
    if fmt == 'srt':
        for i, r in enumerate(righe):
            fine = righe[i + 1]['ms'] if i + 1 < len(righe) else r['ms'] + 4000
            if fine - r['ms'] > 8000:
                fine = r['ms'] + 4000
            out += [str(i + 1), "%s --> %s" % (_hms(r['ms']), _hms(max(r['ms'] + 300, fine - 50))),
                    _testo_riga(r), '']
        return '\n'.join(out)
    for r in righe:
        if r['stacco']:
            out.append('')
        if fmt == 'txt':
            out.append(_testo_riga(r))
        elif fmt == 'lrc':
            out.append('[%s]%s' % (_mmss(r['ms']), _testo_riga(r)))
        else:
            out.append('[%s]' % _mmss(r['ms']) + ''.join('<%s>%s' % (_mmss(ms), s) for ms, s in r['sill']).rstrip())
    return '\n'.join(out) + '\n'


# ---------------- lettura: qualunque formato -> voci ----------------
_RE_RIGA = re.compile(r'\[(\d+):(\d+(?:[.:]\d+)?)\]')
_RE_PAROLA = re.compile(r'<(\d+):(\d+(?:[.:]\d+)?)>')
_RE_META = re.compile(r'^\[[a-zA-Z#]+:.*\]$')
_RE_SRT = re.compile(r'(\d+):(\d\d):(\d\d)[,.](\d{1,3})\s*-->')


def _ms(m, sec):
    return int(round((int(m) * 60 + float(sec.replace(':', '.'))) * 1000))


def _da_srt(testo):
    """SRT -> LRC a righe (poi passa per la lettura LRC)."""
    out = []
    for b in re.split(r'\n\s*\n', testo.replace('\r', '')):
        r = [x for x in b.split('\n') if x.strip()]
        k = next((i for i, x in enumerate(r) if '-->' in x), None)
        if k is None:
            continue
        m = _RE_SRT.search(r[k])
        ms = ((int(m.group(1)) * 60 + int(m.group(2))) * 60 + int(m.group(3))) * 1000 + int(m.group(4).ljust(3, '0')) if m else 0
        for j, x in enumerate(r[k + 1:]):
            x = re.sub(r'<[^>]*>', '', x).strip()
            if x:
                out.append('[%s]%s' % (_mmss(ms + 10 * j), x))
    return '\n'.join(out)


def _e_srt(testo):
    return bool(re.search(r'^\s*\d+\s*\r?\n\s*\d+:\d\d:\d\d[,.]\d{1,3}\s*-->', testo, re.M))


def leggi_testo(testo):
    """TXT / LRC (anche a sillabe) -> righe [(ms_riga|None, [(ms|None, parola)], stacco)]"""
    if _e_srt(testo):
        testo = _da_srt(testo)
    righe, vuote = [], 0
    for r in testo.splitlines():
        r = r.strip()
        if not r:
            vuote += 1 if righe else 0
            continue
        if _RE_META.match(r):
            continue
        tempi = []
        while True:
            m = _RE_RIGA.match(r)
            if not m:
                break
            tempi.append(_ms(m.group(1), m.group(2)))
            r = r[m.end():].lstrip()
        if _RE_PAROLA.search(r):
            # LRC a sillabe: ogni pezzo fra due tempi e' una sillaba di KaraDom, si tiene COM'E'
            # (spazi compresi) -> SYLT -> LRC -> SYLT torna identico
            pezzi, t = [], None
            for pezzo in re.split(r'(<\d+:\d+(?:[.:]\d+)?>)', r):
                m = _RE_PAROLA.fullmatch(pezzo)
                if m:
                    t = _ms(m.group(1), m.group(2))
                elif pezzo:
                    pezzi.append((t, pezzo))
                    t = None
            if pezzi:
                for tr in (tempi or [None]):
                    righe.append((tr, pezzi, min(vuote, 1), True))
                vuote = 0
            continue
        parole, t, attacca = [], None, False
        for pezzo in re.split(r'(<\d+:\d+(?:[.:]\d+)?>)', r):
            m = _RE_PAROLA.fullmatch(pezzo)
            if m:
                t = _ms(m.group(1), m.group(2))
                continue
            if not pezzo:
                continue
            # LRC a sillabe: un pezzo senza spazio davanti continua la parola di prima
            pezzi = pezzo.split(' ')
            for i, w in enumerate(pezzi):
                if w == '':
                    attacca = False
                    continue
                if attacca and i == 0 and parole:
                    parole[-1][1].append((t, w))
                else:
                    parole.append([t, [(t, w)]])
                t = None
                attacca = True
            attacca = not pezzo.endswith(' ')
        if not parole:
            continue
        for tr in (tempi or [None]):
            righe.append((tr, parole, min(vuote, 1), False))
        vuote = 0
    if any(x[0] is not None for x in righe):
        righe.sort(key=lambda x: (x[0] is None, x[0] or 0))
    return righe


def righe_a_sillabe(righe):
    """Come la 226: sillabe di KaraDom ('\\n' davanti alla 1a sillaba della riga, spazio a fine
    parola). Le sillabe gia' divise nel file (LRC a sillabe) restano le SUE coi suoi tempi;
    senza tempi: 300 ms l'una; LRC a righe: spalmate fino alla riga dopo (max 350 ms)."""
    voci, cursore = [], 1000
    for i, (t0, parole, vuote, sillabe) in enumerate(righe):
        sill = []
        if sillabe:
            sill = [[x, ts] for ts, x in parole]
            sill[-1][0] = sill[-1][0].rstrip()
        for wi, (tw, pezzi) in enumerate([] if sillabe else parole):
            if len(pezzi) == 1:                  # parola intera (TXT, LRC a righe o a parole)
                ss = [(None, x) for x in (_split_syllables(pezzi[0][1]) or [pezzi[0][1]])]
                ss[0] = (pezzi[0][0] if pezzi[0][0] is not None else tw, ss[0][1])
            else:
                ss = pezzi
            for si, (ts, x) in enumerate(ss):
                fine = si == len(ss) - 1
                sill.append([x + (' ' if fine and wi < len(parole) - 1 else ''), ts])
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
                    passo, n = (sill[b][1] - ta) / (b - a), b
                else:
                    n = len(sill)
                    passo = min(350.0, (fine - ta) / (n - a + 1)) if n - a > 1 else 0
                for k in range(a + 1, n):
                    sill[k][1] = int(ta + passo * (k - a))
        cursore = sill[-1][1] + 900
        voci.extend(sill)
    prima = 0
    for v in voci:                                    # tempi mai all'indietro (uguali si')
        v[1] = max(int(v[1]), prima)
        prima = v[1]
    return voci


def _decodifica(raw):
    for enc in ('utf-8-sig', 'cp1252', 'latin-1'):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode('latin-1', 'replace')


def _lettore():
    """Istanza senza finestra, solo per leggere/scrivere MP3 (SYLT / WL5) coi metodi dell'editor."""
    lt = object.__new__(ke.KaraokeTimestampEditor)
    lt.id3_frames, lt.sylt_entries = [], []
    lt.sylt_header = lt.audio_data = lt.mp3_data = None
    lt.id3_version, lt.id3_flags = (3, 0), 0
    lt.wl5_prefix = lt.wl5_suffix = b''
    lt.file_format = None
    return lt


def voci_da_testo(testo):
    """(voci, ha_tempi)"""
    ha_tempi = bool(_RE_RIGA.search(testo) or _e_srt(testo))
    return righe_a_sillabe(leggi_testo(testo)), ha_tempi


def voci_da_file(fp):
    """(voci, ha_tempi) da MP3 SYLT/WL5, MIDI/KAR (con la 226), LRC, SRT, TXT."""
    est = os.path.splitext(fp)[1].lower()
    if est in EST_MIDI:
        m = _m226()
        if m is None:
            raise RuntimeError(_("Il MIDI / KAR si legge e si scrive solo con l'editor MIDI di KaraDom (patch 226)."))
        import mido
        return [list(x) for x in m.voci_da_midi(mido.MidiFile(fp, clip=True))[0]], True
    raw = open(fp, 'rb').read()
    if est == '.mp3' or raw[:3] == b'ID3':
        lt = _lettore()
        if b'<WL5SYNCT>' in raw:
            lt._parse_wl5(raw)
        else:
            lt._parse_id3(raw)
        return [list(x) for x in lt.sylt_entries], True
    return voci_da_testo(_decodifica(raw))


# ---------------- scrittura DENTRO un altro file ----------------
def _copia_orig(fp):
    b, e = os.path.splitext(fp)
    orig = b + '.orig' + e
    if os.path.exists(fp) and not os.path.exists(orig):
        shutil.copy2(fp, orig)
    return orig


def _scrivibile(fp):
    if os.path.exists(fp) and not os.access(fp, os.W_OK):
        os.chmod(fp, 0o666)


def dentro_mp3(fp, voci, wl5=False):
    raw = open(fp, 'rb').read()
    lt = _lettore()
    lt._parse_id3(raw)                         # tiene gli altri tag e l'audio, toglie il SYLT
    if lt.audio_data is None:
        lt.audio_data = raw
    a = lt.audio_data
    i = a.find(b'<WL5SYNCT>')                  # via il WL5SYNCT vecchio, se c'era
    if i >= 0:
        j = a.find(b'</WL5SYNCT>', i)
        lt.audio_data = a[:i] + (a[j + 11:] if j >= 0 else b'')
    lt.sylt_entries = [[t, int(ms)] for t, ms in voci]
    orig = _copia_orig(fp)
    _scrivibile(fp)
    tmp = fp + '.tmp'
    if wl5:
        lt._write_wl5_from_state(tmp)
    else:
        lt._save_sylt(tmp)
    os.replace(tmp, fp)
    return orig


def dentro_midi(fp, voci):
    m = _m226()
    if m is None:
        raise RuntimeError(_("Il MIDI / KAR si legge e si scrive solo con l'editor MIDI di KaraDom (patch 226)."))
    import mido
    ed = object.__new__(ke.KaraokeTimestampEditor)
    ed.midi = mido.MidiFile(fp, clip=True)
    ed.midi_src = m.voci_da_midi(ed.midi)[1]
    ed._testo_inserito = True                   # testo nuovo: stile MLive, come 'Inserisci testo'
    ed.current_file = fp
    ed.sylt_entries = [[t, int(ms)] for t, ms in voci]
    b, e = os.path.splitext(fp)
    orig = b + '.orig' + e                      # _salva_midi la fa da se' (file = current_file)
    ed._salva_midi(fp)
    return orig


def _fai_classe(Base):
    class Editor228(Base):
        def __init__(self, root, filepath=None, on_save_callback=None):
            super().__init__(root, filepath=filepath, on_save_callback=on_save_callback)
            try:
                self._bottone_228()
            except Exception as e:
                print('[228] bottone non messo: %s' % e)

        def _bottone_228(self):
            """UN bottone, dove si vede sempre: barra in alto accanto a 'Inserisci testo' (con la 226) e
            pannello comandi a destra (scorre), sezione Speciali (il sinistro e' tagliato sui 1080p)."""
            from moduli.ui_scale import S, F
            C = self.colors
            barra, speciali = None, None

            def giro(w):
                nonlocal barra, speciali
                for c in w.winfo_children():
                    if isinstance(c, tk.Button):
                        try:
                            t = str(c.cget('text'))
                        except Exception:
                            t = ''
                        if t.startswith('📄 Inserisci testo') and barra is None:
                            barra = c
                        if t in ('🎬 Apertura', ke._("🎬 Apertura")) and speciali is None:
                            speciali = c
                    giro(c)
            giro(self.root)
            stile = dict(command=self.copia_su_file, bg='#5f3dc4', fg='white', relief='flat', cursor='hand2',
                         activebackground=C['accent_hover'], activeforeground='white')
            if barra is not None:
                tk.Button(barra.master, text=_("📋 Copia su altro file"), font=F('Segoe UI', 11, 'bold'),
                          padx=S(12), pady=S(4), **stile).pack(side='left', padx=S(4), pady=S(5), after=barra)
            if speciali is not None:
                tk.Button(speciali.master, text=_("📋 Copia su altro file"), font=F('Segoe UI', 10, 'bold'),
                          padx=S(6), pady=S(6), bd=0, **stile).pack(fill='x', padx=S(3), pady=S(3), before=speciali)

        def copia_su_file(self):
            """Il testo con i tempi dell'editor DENTRO un altro file. Il formato lo decide il file scelto:
            MP3 -> SYLT (WL5SYNCT se quel file era gia' WL5), MIDI/KAR -> testo del MIDI (226)."""
            titolo = _("📋 Copia su altro file")
            try:
                self._apply_pending_edit()
            except Exception:
                pass
            voci = [[t, int(ms)] for t, ms in self.sylt_entries]
            if not voci:
                messagebox.showwarning(titolo, _("Il testo dell'editor e' vuoto: apri prima un file."), parent=self.root)
                return
            tipi = ([("MP3 / MIDI / KAR", "*.mp3 *.mid *.midi *.kar")] if _m226() is not None
                    else [("MP3", "*.mp3")])
            fp = filedialog.askopenfilename(parent=self.root, title=titolo, filetypes=tipi + [("*.*", "*.*")])
            if not fp:
                return
            cur = getattr(self, 'current_file', None)
            if cur and os.path.normcase(os.path.abspath(cur)) == os.path.normcase(os.path.abspath(fp)):
                messagebox.showwarning(titolo, _("Questo e' il file aperto nell'editor: usa SALVA."), parent=self.root)
                return
            try:
                if fp.lower().endswith(EST_MIDI):
                    orig = dentro_midi(fp, voci)
                else:
                    with open(fp, 'rb') as f:
                        wl5 = b'<WL5SYNCT>' in f.read()
                    orig = dentro_mp3(fp, voci, wl5=wl5)
            except Exception as e:
                import traceback
                traceback.print_exc()
                messagebox.showerror(titolo, _("Errore:\n{e}").format(e=e), parent=self.root)
                return
            msg = _("Fatto: {m} sillabe copiate in {f} (copia del file com'era: {o})").format(
                m=len(voci), f=os.path.basename(fp), o=os.path.basename(orig))
            self.status_var.set(msg)
            messagebox.showinfo(titolo, msg, parent=self.root)

    Editor228.__name__ = Base.__name__
    return Editor228



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
    if getattr(ke, '_ver228', None) == _VER:
        return True
    # la base e' l'editor che c'era PRIMA della 228 (con la 226: quello MIDI); una 228 vecchia
    # gia' agganciata nello stesso avvio non si impila sotto la nuova
    base = getattr(ke, '_base228', None) or ke.KaraokeTimestampEditor
    ke._base228 = base
    ke.KaraokeTimestampEditor = _fai_classe(base)
    ke._ver228 = _VER
    print('[228] editor testi: bottone Copia su altro file (v2)')
    return True


def revert():
    base = getattr(ke, '_base228', None)
    if base is not None:
        ke.KaraokeTimestampEditor = base
        ke._ver228 = None
    return True


try:
    apply()
except Exception as _e:
    print('[228] non applicata: %s' % _e)
