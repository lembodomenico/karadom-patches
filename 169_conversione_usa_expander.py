import os
import ctypes
import importlib.util


def _cfg(k, d=''):
    try:
        from moduli.database import Database
        return str(Database.get_config(k, d))
    except Exception:
        return d


def _fx171(self, stream):
    """Se e' attiva la 171 (X-Light clean-match), applico la SUA catena al render:
    riverbero DX8 + DSP numpy (_cb) identico al vivo."""
    if _cfg('patch_171', '1') == '0':
        return False
    p = os.path.join(os.environ.get("LOCALAPPDATA", ""), "KaraDom", "patches",
                     "171_expander_xlight_clean_match.py")
    if not os.path.isfile(p):
        return False
    spec = importlib.util.spec_from_file_location("xl171_exp", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    import moduli.midi_mp3_exporter as MME
    b = MME._lib.bass
    DWORD = MME.DWORD

    class REV(ctypes.Structure):
        _fields_ = [("fInGain", ctypes.c_float), ("fReverbMix", ctypes.c_float),
                    ("fReverbTime", ctypes.c_float), ("fHighFreqRTRatio", ctypes.c_float)]
    b.BASS_ChannelSetFX.restype = DWORD
    b.BASS_ChannelSetFX.argtypes = [DWORD, DWORD, ctypes.c_int]
    b.BASS_FXSetParameters.argtypes = [DWORD, ctypes.c_void_p]
    hr = b.BASS_ChannelSetFX(stream, 8, 26)   # DX8 reverb
    if hr:
        b.BASS_FXSetParameters(hr, ctypes.byref(
            REV(0.0, float(mod._REV_MIX), float(mod._REV_MS), 0.5)))
    b.BASS_ChannelSetDSP.restype = DWORD
    b.BASS_ChannelSetDSP.argtypes = [DWORD, mod.DSPPROC, ctypes.c_void_p, ctypes.c_int]
    mod._ST.clear()
    b.BASS_ChannelSetDSP(stream, mod._cb, None, 0)
    self._xl171_mod = mod
    try:
        self._log("Expander X-Light CLEAN-MATCH applicato al render (169->171)")
    except Exception:
        pass
    return True


def _fx170(self, stream):
    """Se e' attiva la 170 (EQ X-Light PULITA), applico le sue 5 bande DX8 al render."""
    if _cfg('patch_170', '1') == '0':
        return False
    p = os.path.join(os.environ.get("LOCALAPPDATA", ""), "KaraDom", "patches",
                     "170_expander_xlight_pulito.py")
    if not os.path.isfile(p):
        return False
    spec = importlib.util.spec_from_file_location("xl170_exp", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    import moduli.midi_mp3_exporter as MME
    b = MME._lib.bass
    DWORD = MME.DWORD

    class PEQ(ctypes.Structure):
        _fields_ = [("fCenter", ctypes.c_float), ("fBandwidth", ctypes.c_float),
                    ("fGain", ctypes.c_float)]
    b.BASS_ChannelSetFX.restype = DWORD
    b.BASS_ChannelSetFX.argtypes = [DWORD, DWORD, ctypes.c_int]
    b.BASS_FXSetParameters.argtypes = [DWORD, ctypes.c_void_p]
    for i, (f0, g, bw) in enumerate(mod._BANDS):
        h = b.BASS_ChannelSetFX(stream, 7, 200 + i)   # DX8 PARAMEQ
        if h:
            b.BASS_FXSetParameters(h, ctypes.byref(PEQ(float(f0), float(bw), float(g))))
    try:
        self._log("Expander X-Light PULITO applicato al render (169->170): 5 bande")
    except Exception:
        pass
    return True


def _fx167(self, stream):
    if _cfg('patch_167', '1') == '0':
        return False
    p = os.path.join(os.environ.get("LOCALAPPDATA", ""), "KaraDom", "patches",
                     "167_expander_come_xlight.py")
    if not os.path.isfile(p):
        return False
    spec = importlib.util.spec_from_file_location("xl167_exp", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    import moduli.midi_mp3_exporter as MME
    b = MME._lib.bass
    DWORD = MME.DWORD
    P = mod._scegli_profilo()

    class REV(ctypes.Structure):
        _fields_ = [("fInGain", ctypes.c_float), ("fReverbMix", ctypes.c_float),
                    ("fReverbTime", ctypes.c_float), ("fHighFreqRTRatio", ctypes.c_float)]
    b.BASS_ChannelSetFX.restype = DWORD
    b.BASS_ChannelSetFX.argtypes = [DWORD, DWORD, ctypes.c_int]
    b.BASS_FXSetParameters.argtypes = [DWORD, ctypes.c_void_p]
    hr = b.BASS_ChannelSetFX(stream, 8, 25)      # DX8 reverb
    if hr:
        b.BASS_FXSetParameters(hr, ctypes.byref(
            REV(0.0, float(P["rev_mix"]), float(P["rev_ms"]), 0.5)))
    b.BASS_ChannelSetDSP.restype = DWORD
    b.BASS_ChannelSetDSP.argtypes = [DWORD, mod.DSPPROC, ctypes.c_void_p, ctypes.c_int]
    mod._ST.clear()
    b.BASS_ChannelSetDSP(stream, mod._cb, None, 0)
    self._xl167_mod = mod          # tiene vivo il callback per tutto il render
    try:
        self._log("Expander X-Light applicato al render (169): profilo %s" %
                  ("MAX" if P is mod._PUSH else "sicuro"))
    except Exception:
        pass
    return True


def apply():
    try:
        import moduli.midi_mp3_exporter as MME
    except Exception:
        return False
    Exp = getattr(MME, "MidiMp3Exporter", None)
    if Exp is None or getattr(Exp, "_xl169", False):
        return True

    _orig_init = Exp.__init__

    def __init__(self, *a, **k):
        _orig_init(self, *a, **k)
        # Se il Mixer usa l'expander SOFTWARE, la conversione deve renderlo col suo
        # banco (anche core.kdl, estensione neutra) + effetti 167. La GUI compilata
        # rileva il software solo a runtime (dopo aver suonato un MIDI): qui lo forzo
        # anche da config, cosi' vale sempre.
        try:
            from moduli.database import Database
            soft = bool(getattr(self, "_soft_fx", False))
            if not soft:
                try:
                    from moduli.bass_engine import get_bass_engine
                    soft = bool(getattr(get_bass_engine(), "_exp_soft_active", False))
                except Exception:
                    soft = False
                if not soft:
                    soft = str(Database.get_config("sorgente_scelta", "")) == "software"
            if soft:
                self._soft_fx = True
                banco = Database.get_config("exp_banco_path", "") or ""
                if banco and os.path.isfile(banco):
                    self.soundfont_path = banco
        except Exception:
            pass
    Exp.__init__ = __init__

    _orig_fx = getattr(Exp, "_applica_fx_soft", None)

    def _applica_fx_soft(self, stream):
        try:
            if _fx171(self, stream):     # X-Light clean-match (se attiva)
                return
        except Exception:
            pass
        try:
            if _fx170(self, stream):     # EQ X-Light pulita
                return
        except Exception:
            pass
        try:
            if _fx167(self, stream):     # exciter (se riattivato)
                return
        except Exception:
            pass
        if _orig_fx:
            try:
                _orig_fx(self, stream)
            except Exception:
                pass
    Exp._applica_fx_soft = _applica_fx_soft
    Exp._xl169 = True

    # Etichetta finestra: mostra l'EXPANDER SOFTWARE nella riga "Suoni"
    # (altrimenti appare solo "SoundFont" e sembra che l'expander non ci sia).
    Win = getattr(MME, "MidiMp3Window", None)
    if Win is not None and not getattr(Win, "_xl169", False):
        _orig_row = getattr(Win, "_aggiorna_suoni_row", None)

        def _aggiorna_suoni_row(self):
            try:
                from moduli.bass_engine import get_bass_engine
                soft = bool(getattr(get_bass_engine(), "_exp_soft_active", False))
            except Exception:
                soft = False
            if not soft:
                soft = (_cfg('sorgente_scelta', '') == 'software')
            if soft:
                try:
                    from moduli.database import Database
                    banco = Database.get_config("exp_banco_path", "") or ""
                    nome = os.path.basename(banco) or "core.kdl"
                    self.expander_attivo = ""
                    self.device_ingresso = None
                    # il controllo pre-conversione pretende un SoundFont valido:
                    # gli do il banco dell'expander (core.kdl esiste) cosi' non blocca.
                    if banco and os.path.isfile(banco):
                        try:
                            self.sf_var.set(banco)
                        except Exception:
                            pass
                    self._suoni_label.configure(
                        text="Expander software (X-Light) — %s" % nome, fg="#c77dff")
                    self._suoni_btn.configure(text="…", command=self._pick_sf)
                    self._suoni_label.configure(cursor="hand2")
                    self._suoni_label.bind("<Button-1>", lambda e: self._suoni_btn.invoke())
                    return
                except Exception:
                    pass
            if _orig_row:
                return _orig_row(self)
        if _orig_row:
            Win._aggiorna_suoni_row = _aggiorna_suoni_row
            Win._xl169 = True
    return True


try:
    apply()
except Exception as _e:
    print("patch 169: %s" % _e)
