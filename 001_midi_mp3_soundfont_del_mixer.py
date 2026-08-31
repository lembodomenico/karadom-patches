# 001_midi_mp3_soundfont_del_mixer.py
#
# MIDI/KAR -> MP3: la conversione usa i suoni del MIXER, quali che siano.
#
#   Se sul Mixer c'e' un EXPANDER  -> l'MP3 si crea con l'expander (registrandolo).
#   Se sul Mixer c'e' il SOUNDFONT -> l'MP3 si crea col SoundFont, come prima,
#                                     e non lo si deve piu' indicare a mano.
#
# Prima invece chiedeva sempre dove fosse l'.sf2 e convertiva sempre e comunque
# con quello, anche a chi stava suonando con l'expander.
#
# COSA CAMBIA, IN DETTAGLIO
# 1) _find_soundfont: leggeva 'soundfont_path' dal config e, se quel percorso non
#    esisteva piu' (configurato su un'altra cartella o un altro PC), rinunciava
#    lasciando il campo vuoto. Ora cerca lo stesso NOME nelle cartelle del
#    programma prima di arrendersi, e la scelta fatta a mano viene ricordata.
# 2) La riga della finestra non e' piu' una casella da riempire: dice con che
#    suoni uscira' l'MP3 (e, con l'expander, da quale ingresso lo registra).
# 3) Con l'expander: KaraDom gli suona il MIDI con lo stesso motore del Mixer
#    (stessi mute, stessi program change) e REGISTRA la sua uscita audio.
#    E' l'unico modo possibile: l'expander e' una scatola fuori dal computer,
#    il suo suono esce dalle sue prese. Percio' dura quanto il brano, mentre
#    col SoundFont il calcolo e' offline e piu' veloce del tempo reale.
#    L'ingresso da cui registrare si sceglie una volta e resta memorizzato.

import os
from pathlib import Path

import moduli.midi_mp3_exporter as mme


# =====================================================================
#  1) QUALE SOUNDFONT: quello del Mixer, ritrovato anche se e' stato spostato
# =====================================================================

def _cartelle_soundfont():
    base = mme._app_base_dir()
    cartelle = [base / "soundfonts", base, Path.cwd() / "soundfonts", Path.cwd()]
    try:
        local = os.environ.get("LOCALAPPDATA", "")
        if local:
            cartelle.append(Path(local) / "KaraDom" / "soundfonts")
    except Exception:
        pass
    return cartelle


def _find_soundfont_dal_mixer():
    nome_cercato = ""
    try:
        from moduli.database import Database
        sf = Database.get_config("soundfont_path", "")
        if sf:
            if os.path.exists(sf):
                return sf
            nome_cercato = os.path.basename(sf)
    except Exception:
        pass

    cartelle = _cartelle_soundfont()

    if nome_cercato:
        for folder in cartelle:
            try:
                p = folder / nome_cercato
                if p.exists():
                    return str(p)
            except Exception:
                continue

    for folder in cartelle:
        try:
            if not folder.exists():
                continue
        except Exception:
            continue
        for pat in ("*.sf2", "*.SF2", "*.sf3", "*.SF3"):
            try:
                found = sorted(folder.glob(pat))
            except Exception:
                found = []
            if found:
                return str(found[0])
    return ""


mme._cartelle_soundfont = _cartelle_soundfont
mme._find_soundfont = _find_soundfont_dal_mixer


# =====================================================================
#  2) COSA STA USANDO IL MIXER + dove entra l'audio dell'expander
# =====================================================================

def _expander_del_mixer():
    """Il nome dell'expander che KaraDom usa, "" se suona col SoundFont.

    ⚠️ `get_active_player()` risponde SOLO se qualcuno ha gia' suonato un MIDI in
    questa sessione: il player si crea al primo uso. Chi apriva KaraDom e lanciava
    subito la conversione si vedeva proporre il SoundFont pur avendo l'expander
    collegato. Percio' se non e' ancora acceso si guarda quello CONFIGURATO, senza
    aprirne la porta.
    """
    try:
        from moduli.expander_midi import get_active_player
        exp = get_active_player()
        if exp:
            return getattr(exp, "nome_porta", "") or ""
    except Exception:
        pass
    try:
        from moduli.expander_midi import get_mode, detect_expander
        if get_mode() == "off":
            return ""
        porta = detect_expander()
        if porta:
            return porta.get("nome", "") or ""
    except Exception:
        pass
    return ""


def _dispositivi_ingresso():
    """Gli ingressi audio del PC: [(indice, nome, canali)]."""
    try:
        import sounddevice as sd
    except Exception:
        return []
    fuori = []
    try:
        for i, d in enumerate(sd.query_devices()):
            n = int(d.get("max_input_channels", 0) or 0)
            if n > 0:
                fuori.append((i, str(d.get("name", "?")), n))
    except Exception:
        pass
    return fuori


def _ingresso_salvato():
    try:
        from moduli.database import Database
        nome = Database.get_config("midi_mp3_input_device", "")
    except Exception:
        nome = ""
    if not nome:
        return None, ""
    for idx, n, _ch in _dispositivi_ingresso():
        if n == nome:
            return idx, n
    return None, nome          # era collegato e adesso non c'e' piu'


def _salva_ingresso(nome):
    try:
        from moduli.database import Database
        Database.set_config("midi_mp3_input_device", nome or "")
    except Exception:
        pass


mme._expander_del_mixer = _expander_del_mixer
mme._dispositivi_ingresso = _dispositivi_ingresso
mme._ingresso_salvato = _ingresso_salvato
mme._salva_ingresso = _salva_ingresso


# =====================================================================
#  3) CONVERSIONE CON L'EXPANDER: gli si suona il MIDI e si registra
# =====================================================================

class ExpanderMp3Exporter(mme.MidiMp3Exporter):
    """MP3 con i suoni dell'EXPANDER invece che del SoundFont.

    Del percorso normale riusa tutto il resto: codifica MP3, loudness, SYLT/LRC.
    """

    def __init__(self, *a, **kw):
        self.device_ingresso = kw.pop("device_ingresso", None)
        self.coda_sec = float(kw.pop("coda_sec", 3.0))
        kw.setdefault("soundfont_path", "")
        super().__init__(*a, **kw)

    def run(self):
        import shutil
        import tempfile
        tmpdir = tempfile.mkdtemp(prefix="karadom_expander_")
        wav = os.path.join(tmpdir, "registrazione.wav")
        try:
            self._registra(wav)
            if self._cancelled:
                return
            self._encode_mp3(wav)
            self._export_sylt()
            self._progress(100, "Completato.")
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def _prendi_player(self):
        from moduli.expander_midi import get_active_player, get_expander_player
        player = get_active_player() or get_expander_player()
        if player is None:
            raise RuntimeError(
                "Nessun expander collegato: controlla la porta MIDI nelle impostazioni.")
        return player

    def _registra(self, wav_path):
        import time
        import wave
        import numpy as np
        try:
            import sounddevice as sd
        except Exception as e:
            raise RuntimeError("Registrazione non disponibile (sounddevice): %s" % e)

        dev = self.device_ingresso
        if dev is None:
            raise RuntimeError("Scegli l'ingresso audio a cui e' collegato l'expander.")

        info = sd.query_devices(dev)
        # SEMPRE il sample rate nativo del device: aprirlo a un valore diverso fa
        # crashare PortAudio nativamente (stessa lezione del Registratore).
        sr = int(round(float(info.get("default_samplerate") or 48000)))
        ch = max(1, min(2, int(info.get("max_input_channels") or 2)))
        self._log("🎙️ Registro da: %s  (%d Hz, %d canali)" % (info.get("name", dev), sr, ch))

        player = self._prendi_player()
        self._log("🎛 Suono il MIDI sull'expander: %s" % getattr(player, "nome_porta", "expander"))
        try:
            player.stop()
        except Exception:
            pass
        if not player.load(self.midi_path):
            raise RuntimeError("L'expander non e' riuscito a caricare il MIDI.")

        for c in range(16):
            try:
                player.set_channel_mute(c, c in self.muted_channels)
            except Exception:
                pass

        durata = 0.0
        try:
            durata = float(player.get_duration_ms() or 0) / 1000.0
        except Exception:
            pass
        if durata > 0:
            self._log("⏱️ Dura %s: la registrazione avviene in tempo reale."
                      % time.strftime("%M:%S", time.gmtime(durata)))

        blocchi = []

        def _arrivo(indata, frames, tinfo, status):
            blocchi.append(indata.copy())

        stream = sd.InputStream(device=dev, samplerate=sr, channels=ch,
                                dtype="float32", callback=_arrivo)
        try:
            with stream:
                player.play()
                t0 = time.time()
                limite = (durata + 60.0) if durata > 0 else 3600.0
                while True:
                    if self._cancelled:
                        self._log("⏹️ Annullato.")
                        break
                    if not getattr(player, "is_playing", False):
                        break
                    trascorso = time.time() - t0
                    if trascorso > limite:
                        self._log("⚠️ Tempo massimo superato: chiudo la registrazione.")
                        break
                    if durata > 0:
                        self._progress(min(78.0, 78.0 * trascorso / durata),
                                       "Registrazione dall'expander...")
                    time.sleep(0.1)
                if not self._cancelled:
                    time.sleep(self.coda_sec)     # riverbero e note che si spengono
        finally:
            try:
                player.stop()
            except Exception:
                pass

        if self._cancelled:
            return
        if not blocchi:
            raise RuntimeError("Non e' arrivato audio da quell'ingresso: controlla il "
                               "cavo e il dispositivo scelto.")

        dati = np.concatenate(blocchi, axis=0)
        picco = float(np.max(np.abs(dati))) if dati.size else 0.0
        if picco < 0.001:
            raise RuntimeError("L'ingresso e' rimasto muto (nessun segnale): controlla il "
                               "cavo, il volume dell'expander e l'ingresso scelto.")
        self._log("📈 Picco registrato: %.1f dB" % (20.0 * np.log10(max(picco, 1e-9))))

        pcm = np.clip(dati, -1.0, 1.0)
        pcm = np.where(pcm >= 0, pcm * 32767.0, pcm * 32768.0).astype("<i2")
        with wave.open(wav_path, "wb") as w:
            w.setnchannels(ch)
            w.setsampwidth(2)
            w.setframerate(sr)
            w.writeframes(pcm.tobytes())
        self._progress(79, "Registrazione finita.")


mme.ExpanderMp3Exporter = ExpanderMp3Exporter


# =====================================================================
#  4) LA FINESTRA: dice con che suoni esce l'MP3 e sceglie l'ingresso
# =====================================================================

try:
    import tkinter as tk
    from tkinter import messagebox

    try:
        from moduli.i18n import _ as _t
    except Exception:
        def _t(s):
            return s

    try:
        from moduli.ui_scale import S as _S, F as _F
    except Exception:
        def _S(n):
            return n

        def _F(fam, size, *a):
            return (fam, size) + tuple(a)

    W = mme.MidiMp3Window

    def _aggiorna_suoni_row(self):
        """Con cosa uscira' l'MP3: lo decide il Mixer, non una scelta a parte."""
        try:
            exp = _expander_del_mixer()
            self.expander_attivo = exp
            if exp and not _dispositivi_ingresso():
                # C'e' l'expander ma il suo audio non rientra nel PC: non e'
                # registrabile. Lo si dice subito, senza far premere Crea a vuoto.
                sf = self.sf_var.get().strip()
                self.device_ingresso = None
                testo = ("Expander %s: non rientra nel PC, l'MP3 esce col SoundFont %s"
                         % (exp, Path(sf).name if sf else ""))
                colore = "#ff9900"
                self._suoni_btn.configure(text="…", command=self._pick_sf)
            elif exp:
                idx, nome = _ingresso_salvato()
                self.device_ingresso = idx
                if idx is not None:
                    testo = "Expander %s  ←  registro da: %s" % (exp, nome)
                    colore = "#c77dff"
                elif nome:
                    testo = "Expander %s  —  l'ingresso «%s» non c'e' piu': scegline uno" % (exp, nome)
                    colore = "#ff9900"
                else:
                    testo = "Expander %s  —  scegli da quale ingresso registrarlo" % exp
                    colore = "#ff9900"
                self._suoni_btn.configure(text="…", command=self._pick_ingresso)
            else:
                sf = self.sf_var.get().strip()
                self.device_ingresso = None
                if sf:
                    testo = "SoundFont %s" % Path(sf).name
                    colore = "#00ff00"
                else:
                    testo = _t("Nessun SoundFont trovato - scegline uno")
                    colore = "#ff9900"
                self._suoni_btn.configure(text="…", command=self._pick_sf)
            self._suoni_label.configure(text=testo, fg=colore)
        except Exception:
            pass

    def _pick_ingresso(self):
        """Da quale presa entra l'audio dell'expander: si sceglie una volta sola."""
        elenco = _dispositivi_ingresso()
        if not elenco:
            messagebox.showerror(
                _t("Nessun ingresso audio"),
                _t("Windows non riporta nessun ingresso audio. Collega l'uscita "
                   "dell'expander a una presa della scheda audio."), parent=self.win)
            return

        dlg = tk.Toplevel(self.win)
        dlg.title(_t("Ingresso dell'expander"))
        dlg.configure(bg=self.BG)
        dlg.transient(self.win)
        dlg.grab_set()
        tk.Label(dlg, text=_t("Dove arriva l'audio dell'expander?"),
                 bg=self.BG, fg=self.FG, font=_F("Segoe UI", 11, "bold")).pack(
                     padx=_S(16), pady=(_S(14), _S(6)))
        lista = tk.Listbox(dlg, bg=self.BG3, fg=self.FG, selectbackground=self.ACCENT,
                           selectforeground="#000000", font=_F("Segoe UI", 10),
                           width=54, height=min(12, len(elenco)), relief="flat",
                           highlightthickness=1, highlightbackground=self.FIELD_BORDER)
        lista.pack(padx=_S(16), pady=_S(6), fill="both", expand=True)
        for _i, nome, ch in elenco:
            lista.insert("end", "%s  (%d can.)" % (nome, ch))
        _idx_ora, nome_ora = _ingresso_salvato()
        for r, (i, nome, _ch) in enumerate(elenco):
            if nome == nome_ora:
                lista.selection_set(r)
                lista.see(r)
                break

        def conferma():
            sel = lista.curselection()
            if sel:
                i, nome, _ch = elenco[sel[0]]
                _salva_ingresso(nome)
                self.device_ingresso = i
                self._log("🎙️ Ingresso dell'expander: %s" % nome)
                self._aggiorna_suoni_row()
            dlg.destroy()

        barra = tk.Frame(dlg, bg=self.BG)
        barra.pack(pady=_S(12))
        tk.Button(barra, text=_t("Usa questo"), command=conferma, bg=self.BTN_BG, fg=self.FG,
                  activebackground=self.BTN_BG_HOVER, activeforeground=self.ACCENT,
                  font=_F("Segoe UI", 10, "bold"), bd=3, relief="raised",
                  cursor="hand2", width=14).pack(side="left", padx=_S(6))
        tk.Button(barra, text=_t("Annulla"), command=dlg.destroy, bg=self.BTN_BG, fg=self.FG,
                  activebackground=self.BTN_BG_HOVER, font=_F("Segoe UI", 10),
                  bd=3, relief="raised", cursor="hand2", width=10).pack(side="left", padx=_S(6))
        lista.bind("<Double-Button-1>", lambda e: conferma())

    def _suoni_row(self, parent):
        row = tk.Frame(parent, bg=self.BG2, pady=_S(3))
        row.pack(fill="x", padx=_S(14))
        tk.Label(row, text=_t("🎹  Suoni"), bg=self.BG2, fg=self.FG,
                 font=_F("Segoe UI", 9, "bold"), width=22, anchor="w").pack(side="left")
        self._suoni_label = tk.Label(row, text="", bg=self.BG2, anchor="w",
                                     font=_F("Segoe UI", 10))
        self._suoni_label.pack(side="left", fill="x", expand=True, padx=_S(6))
        self._suoni_btn = tk.Button(row, text="…", width=4, relief="raised", cursor="hand2",
                                    bg=self.BTN_BG, fg=self.FG,
                                    activebackground=self.BTN_BG_HOVER,
                                    activeforeground=self.ACCENT,
                                    font=_F("Segoe UI", 11, "bold"),
                                    bd=3, highlightthickness=1,
                                    highlightbackground=self.BTN_BORDER,
                                    highlightcolor=self.ACCENT,
                                    command=self._pick_sf)
        self._suoni_btn.pack(side="left")
        self._aggiorna_suoni_row()

    W._suoni_row = _suoni_row
    W._aggiorna_suoni_row = _aggiorna_suoni_row
    W._pick_ingresso = _pick_ingresso

    # la riga del SoundFont diventa la riga "Suoni"; le altre restano com'erano
    _file_row_originale = W._file_row

    def _file_row_o_suoni(self, parent, label, var, command):
        if command == getattr(self, "_pick_sf", None) or "SoundFont" in str(label):
            return _suoni_row(self, parent)
        return _file_row_originale(self, parent, label, var, command)

    W._file_row = _file_row_o_suoni

    # scegliendo un SoundFont a mano: lo si ricorda e si aggiorna la scritta
    _pick_sf_originale = W._pick_sf

    def _pick_sf_e_ricorda(self):
        _pick_sf_originale(self)
        try:
            path = self.sf_var.get().strip()
            if path and os.path.exists(path):
                from moduli.database import Database
                Database.set_config("soundfont_path", path)
        except Exception:
            pass
        try:
            self._aggiorna_suoni_row()
        except Exception:
            pass

    W._pick_sf = _pick_sf_e_ricorda

    # con l'expander non serve il SoundFont: serve sapere da dove registrare
    _validate_originale = W._validate

    def _validate_con_expander(self):
        # senza expander, o con un expander che non rientra nel PC (non registrabile),
        # vale il controllo di sempre: serve il SoundFont
        if not _expander_del_mixer() or not _dispositivi_ingresso():
            return _validate_originale(self)

        midi = self.midi_var.get().strip()
        out = self.out_var.get().strip()
        if not midi or not os.path.exists(midi):
            messagebox.showerror(_t("MIDI mancante"),
                                 _t("Seleziona un file MIDI/KAR valido."), parent=self.win)
            return None
        if getattr(self, "device_ingresso", None) is None:
            messagebox.showerror(
                _t("Ingresso mancante"),
                _t("Il Mixer sta suonando con l'expander, quindi l'MP3 si crea "
                   "registrandolo.\n\nScegli da quale ingresso audio entra."),
                parent=self.win)
            self._pick_ingresso()
            if getattr(self, "device_ingresso", None) is None:
                return None
        if not out:
            messagebox.showerror(_t("Output mancante"),
                                 _t("Scegli dove salvare l'MP3."), parent=self.win)
            return None
        if not out.lower().endswith(".mp3"):
            out += ".mp3"
            self.out_var.set(out)
        try:
            Path(out).parent.mkdir(parents=True, exist_ok=True)
            self._save_output_dir(str(Path(out).parent))
        except Exception as e:
            messagebox.showerror(_t("Percorso non valido"), str(e), parent=self.win)
            return None
        return midi, self.sf_var.get().strip(), out

    W._validate = _validate_con_expander

    # e infine: quale motore parte. Lo decide il Mixer.
    import threading as _threading

    def _begin_export(self, midi, sf, out, muted_channels):
        self.progress_var.set(0)
        self.percent_var.set("0%")
        try:
            self._log_text.delete("1.0", "end")
        except Exception:
            pass

        if muted_channels:
            self._log("🔇 Canali mutati: " + ", ".join(str(c + 1) for c in muted_channels))
        else:
            self._log("✅ Nessun canale mutato: rendering completo.")

        comuni = dict(
            midi_path=midi, mp3_path=out,
            bitrate_kbps=int(self.bitrate_var.get()),
            enhance=self.enhance_var.get(),
            progress_callback=self._t_progress,
            log_callback=self._t_log,
            muted_channels=muted_channels,
        )
        exp = _expander_del_mixer()
        if exp and getattr(self, "device_ingresso", None) is not None:
            self._log("🎛 Converto con l'EXPANDER %s (registrazione in tempo reale)." % exp)
            self.exporter = ExpanderMp3Exporter(
                soundfont_path="", device_ingresso=self.device_ingresso, **comuni)
        else:
            if exp:
                self._log("⚠️ L'expander non ha un ritorno audio nel computer: "
                          "l'MP3 esce con il SoundFont.")
                self._log("   Per inciderlo davvero serve un cavo dalle sue uscite "
                          "a un ingresso del PC.")
            self.exporter = mme.MidiMp3Exporter(soundfont_path=sf, **comuni)

        _threading.Thread(target=self._worker, daemon=True).start()

    W._begin_export = _begin_export

    # --- diagnosi nel LOG della finestra -------------------------------------
    # Il cliente non ha Python: se l'expander "non viene rilevato" deve poter dire
    # COSA vede il programma senza installare niente. Aprendo la conversione, il log
    # elenca uscite MIDI e ingressi audio: basta uno screenshot.
    _apri_originale = mme.apri_midi_mp3_exporter

    def _uscite_midi():
        try:
            import ctypes
            from ctypes import wintypes

            class _CAPS(ctypes.Structure):
                _fields_ = [("wMid", wintypes.WORD), ("wPid", wintypes.WORD),
                            ("vDriverVersion", wintypes.UINT),
                            ("szPname", wintypes.WCHAR * 32),
                            ("wTechnology", wintypes.WORD), ("wVoices", wintypes.WORD),
                            ("wNotes", wintypes.WORD), ("wChannelMask", wintypes.WORD),
                            ("dwSupport", wintypes.DWORD)]

            winmm = ctypes.WinDLL("winmm.dll")
            fuori = []
            for i in range(winmm.midiOutGetNumDevs()):
                c = _CAPS()
                winmm.midiOutGetDevCapsW(i, ctypes.byref(c), ctypes.sizeof(c))
                fuori.append(c.szPname)
            return fuori
        except Exception:
            return []

    def _apri_con_diagnosi(parent, system=None, midi_path=""):
        win = _apri_originale(parent, system=system, midi_path=midi_path)
        try:
            log = getattr(win, "_log", None)
            if log:
                exp = _expander_del_mixer()
                if exp:
                    log(_t("🎛 Expander: {n}").format(n=exp))
                else:
                    log(_t("🎹 Nessun expander: l'MP3 si crea col SoundFont."))
                    porte = [p for p in _uscite_midi()
                             if "microsoft" not in p.lower() and "wavetable" not in p.lower()]
                    if porte:
                        log(_t("   (uscite MIDI viste: {p} — se l'expander è una di "
                               "queste, impostalo in Expander MIDI)").format(p=", ".join(porte)))
                    else:
                        log(_t("   (nessuna uscita MIDI hardware: l'expander non risulta "
                               "collegato o manca il driver)"))
                if exp:
                    ing = _dispositivi_ingresso()
                    if not ing:
                        log(_t("⚠️ Nessun ingresso audio: l'audio dell'expander non può "
                               "rientrare nel computer, quindi non si può registrare."))
        except Exception:
            pass
        return win

    mme.apri_midi_mp3_exporter = _apri_con_diagnosi
    print("[PATCH] midi_mp3_exporter: i suoni della conversione li decide il Mixer")
except Exception as e:
    print("[PATCH] finestra non aggiornata (%s) - la ricerca del SoundFont vale lo stesso" % e)
