# 101 - Convertitore MP3: bottone per scegliere la sorgente (expander software/hardware o SoundFont); default = ciò che suona nel Mixer
import os


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_101', '1')) == '0'
    except Exception:
        return False


def _exp_dir():
    return os.path.join(os.environ.get('LOCALAPPDATA', ''), 'KaraDom', 'dipendenze', 'Expander')


def _base_bank():
    d = _exp_dir()
    cfg = os.path.join(d, 'expander.cfg')
    try:
        if os.path.exists(cfg):
            p = open(cfg, encoding='utf-8').read().strip()
            if p and os.path.exists(p):
                return p
    except Exception:
        pass
    for c in (os.path.join(d, 'banco_toh.sf3'), os.path.join(d, 'banco.sf3'),
              os.path.join(d, 'banco.sf2')):
        if os.path.exists(c):
            return c
    import glob
    sf3 = sorted(glob.glob(os.path.join(d, '*.sf3')))
    if sf3:
        return sf3[0]
    if os.path.exists(r'C:\Users\lembo\Desktop\KARADOM\KaraDom HD.sf2'):
        return r'C:\Users\lembo\Desktop\KARADOM\KaraDom HD.sf2'
    return ''


def _overlay_bank():
    p = os.path.join(_exp_dir(), 'overlay.sf2')
    return p if os.path.exists(p) else ''


def _porte_hw(ex):
    out = []
    try:
        for p in ex.list_ports():
            n = p.get('nome', '') or ''
            if p.get('punteggio', 0) > 0 and 'loop' not in n.lower():
                out.append(n)
    except Exception:
        pass
    return out


def _loopmidi_presente(ex):
    try:
        return any('loop' in (p.get('nome', '') or '').lower() for p in ex.list_ports())
    except Exception:
        return False


def _mixer_attivo(ex):
    # ('software'|'hw'|'sf', valore) = cosa sta usando il Mixer adesso
    try:
        p = ex.get_active_player()
        if p:
            n = getattr(p, 'nome_porta', '') or ''
            return ('software' if 'loop' in n.lower() else 'hw', n)
    except Exception:
        pass
    try:
        if ex.get_mode() != 'off':
            d = ex.detect_expander()
            if d:
                n = d.get('nome', '') or ''
                return ('software' if 'loop' in n.lower() else 'hw', n)
    except Exception:
        pass
    return ('sf', None)


def apply():
    if _spenta():
        return False
    import sys
    mod = sys.modules.get('moduli.midi_mp3_exporter')
    ex_mod = sys.modules.get('moduli.expander_midi')
    if mod is None:
        try:
            import moduli.midi_mp3_exporter as mod  # noqa
        except Exception:
            print('patch 101: exporter non presente (ok)')
            return False
    if ex_mod is None:
        try:
            import moduli.expander_midi as ex_mod  # noqa
        except Exception:
            ex_mod = None
    W = getattr(mod, 'MidiMp3Window', None)
    if W is None or getattr(W, '_picker_101', False):
        return True

    def _refresh(self):
        try:
            self._aggiorna_suoni_row()
        except Exception:
            pass

    def _set_scelta(self, scelta):
        self._scelta_101 = scelta
        try:
            if scelta[0] == 'sf' and scelta[1]:
                self.sf_var.set(scelta[1])
        except Exception:
            pass
        _refresh(self)
        # aggiorna il LOG con la sorgente appena scelta
        try:
            tipo, val = scelta
            if tipo == 'software':
                self._log("🎹 KaraDom Expander Software")
            elif tipo == 'hw':
                self._log("🎛 Expander %s" % val)
            else:
                sf = self.sf_var.get().strip()
                self._log("🎹 SoundFont: %s" % (os.path.basename(sf) if sf else 'nessuno'))
        except Exception:
            pass

    def _pick_sf(self):
        from tkinter import filedialog
        p = filedialog.askopenfilename(
            title="Scegli SoundFont",
            filetypes=[("SoundFont", "*.sf2 *.sf3"), ("Tutti", "*.*")])
        if p:
            _set_scelta(self, ('sf', p))

    def _menu_sorgenti(self):
        import tkinter as tk
        top = self._suoni_btn.winfo_toplevel()
        m = tk.Menu(top, tearoff=0)
        if _loopmidi_presente(ex_mod):
            m.add_command(label="🎹 Expander software",
                          command=lambda: _set_scelta(self, ('software', None)))
        for n in _porte_hw(ex_mod):
            m.add_command(label="🎛 Expander %s (registra)" % n,
                          command=lambda n=n: _set_scelta(self, ('hw', n)))
        cur = ''
        try:
            cur = self.sf_var.get().strip()
        except Exception:
            cur = ''
        if cur:
            m.add_command(label="🎵 SoundFont: %s" % os.path.basename(cur),
                          command=lambda: _set_scelta(self, ('sf', cur)))
        m.add_command(label="📂 Scegli SoundFont (SF2/SF3)…",
                      command=lambda: _pick_sf(self))
        try:
            x = self._suoni_btn.winfo_rootx()
            y = self._suoni_btn.winfo_rooty() + self._suoni_btn.winfo_height()
            m.tk_popup(x, y)
        finally:
            try:
                m.grab_release()
            except Exception:
                pass

    def _aggiorna_suoni_row(self):
        try:
            if not getattr(self, '_scelta_101', None):
                self._scelta_101 = _mixer_attivo(ex_mod)
            tipo, val = self._scelta_101
            testo = ''
            colore = '#00ff00'
            if tipo == 'software':
                b = _base_bank()
                try:
                    if b:
                        self.sf_var.set(b)
                except Exception:
                    pass
                self.device_ingresso = None
                testo = "KaraDom Expander Software"
                colore = "#c77dff"
            elif tipo == 'hw':
                idx = None
                nome = ''
                try:
                    idx, nome = mod._ingresso_salvato()
                except Exception:
                    pass
                self.device_ingresso = idx
                if idx is not None:
                    testo = "Expander %s  ←  registra da: %s" % (val, nome)
                else:
                    testo = "Expander %s  —  scegli l'ingresso col menu «Cambia»" % val
                colore = "#c77dff"
            else:
                sf = ''
                try:
                    sf = self.sf_var.get().strip()
                except Exception:
                    sf = ''
                self.device_ingresso = None
                testo = "SoundFont:  %s" % (os.path.basename(sf) if sf else 'nessuno — scegline uno')
                colore = "#00ff00" if sf else "#ff9900"
            try:
                self._suoni_label.configure(text=testo, fg=colore)
                self._suoni_btn.configure(text="…", command=lambda: _menu_sorgenti(self))
            except Exception:
                pass
        except Exception as e:
            print('[MP3] suoni row 101:', e)

    W._aggiorna_suoni_row = _aggiorna_suoni_row
    W._menu_sorgenti_101 = _menu_sorgenti

    # log iniziale: con la scelta SOFTWARE, "SoundFont del Mixer" -> "Expander software",
    # e niente frasi da hardware ("esce dalle prese")
    if hasattr(W, '_log') and not getattr(W, '_log_101', False):
        _orig_log = W._log
        def _log(self, msg):
            try:
                m = str(msg)
                sc = getattr(self, '_scelta_101', None)
                if sc and sc[0] == 'software':
                    if 'esce dalle sue prese' in m or "sta suonando con l'expander" in m:
                        return None
                    if 'SoundFont del Mixer' in m:
                        msg = "🎹 KaraDom Expander Software"
            except Exception:
                pass
            return _orig_log(self, msg)
        W._log = _log
        W._log_101 = True

    # dispatch: usa la scelta del picker
    if hasattr(W, '_begin_export'):
        _orig_begin = W._begin_export
        def _begin_export(self, midi, sf, out, muted_channels):
            try:
                sc = getattr(self, '_scelta_101', None) or _mixer_attivo(ex_mod)
                tipo, val = sc
                if tipo == 'software':
                    self.device_ingresso = None
                    b = _base_bank()
                    if b:
                        sf = b
                elif tipo == 'hw':
                    pass  # registra: usa self.device_ingresso
                else:
                    self.device_ingresso = None
            except Exception:
                pass
            return _orig_begin(self, midi, sf, out, muted_channels)
        W._begin_export = _begin_export

    # il log iniziale non deve dire cose da hardware quando la scelta e' software/sf
    if not getattr(mod, '_edm_101', False):
        _orig_edm = mod._expander_del_mixer
        def _expander_del_mixer():
            try:
                n = _orig_edm()
            except Exception:
                n = ''
            if n and 'loop' in n.lower():
                return ''   # il software non e' una scatola da registrare
            return n
        mod._expander_del_mixer = _expander_del_mixer
        mod._edm_101 = True

    # overlay Tyros nel render offline (come suona l'expander software)
    Exp = getattr(mod, 'MidiMp3Exporter', None)
    if Exp is not None and hasattr(Exp, '_prepare_stream') and not getattr(Exp, '_overlay_101', False):
        _orig_prep = Exp._prepare_stream
        def _prepare_stream(self, *a, **k):
            r = _orig_prep(self, *a, **k)
            try:
                ov = _overlay_bank()
                base = str(getattr(self, 'soundfont_path', ''))
                # applica l'overlay Tyros SOLO se il banco base e' quello dell'expander
                if ov and _base_bank() and os.path.normcase(base) == os.path.normcase(_base_bank()) \
                        and getattr(self, '_stream', 0) and getattr(self, '_font', 0):
                    import ctypes
                    m = mod._lib.bassmidi
                    _p, _fl = mod._percorso_per_bass(ov)
                    m.BASS_MIDI_FontInit.restype = mod.DWORD
                    m.BASS_MIDI_FontInit.argtypes = [ctypes.c_void_p, mod.DWORD]
                    fo = m.BASS_MIDI_FontInit(_p, _fl)
                    if fo:
                        voci = [mod.BASS_MIDI_FONT(font=fo, preset=p, bank=0) for p in range(0, 80)]
                        voci.append(mod.BASS_MIDI_FONT(font=fo, preset=0, bank=128))
                        voci.append(mod.BASS_MIDI_FONT(font=self._font, preset=-1, bank=0))
                        arr = (mod.BASS_MIDI_FONT * len(voci))(*voci)
                        m.BASS_MIDI_StreamSetFonts.restype = ctypes.c_bool
                        m.BASS_MIDI_StreamSetFonts.argtypes = [mod.DWORD, ctypes.c_void_p, mod.DWORD]
                        m.BASS_MIDI_StreamSetFonts(self._stream, arr, len(voci))
                        try:
                            m.BASS_MIDI_StreamLoadSamples(self._stream)
                        except Exception:
                            pass
                        print('[MP3] overlay Tyros applicato al render')
            except Exception as e:
                print('[MP3] overlay render:', e)
            return r
        Exp._prepare_stream = _prepare_stream
        Exp._overlay_101 = True

    W._picker_101 = True
    print('[MP3] patch 101: picker sorgente nel convertitore (expander software/hardware/SoundFont)')
    return True


def revert():
    pass


try:
    apply()
except Exception as _e:
    print('patch 101: %s' % _e)
