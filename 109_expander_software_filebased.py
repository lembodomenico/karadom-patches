import os
import ctypes

DWORD = ctypes.c_uint32
BASS_ATTRIB_VOL = 2
BASS_FX_DX8_PARAMEQ = 7
BASS_FX_DX8_REVERB = 8


class DX8_PARAMEQ(ctypes.Structure):
    _fields_ = [("fCenter", ctypes.c_float), ("fBandwidth", ctypes.c_float),
                ("fGain", ctypes.c_float)]


class DX8_REVERB(ctypes.Structure):
    _fields_ = [("fInGain", ctypes.c_float), ("fReverbMix", ctypes.c_float),
                ("fReverbTime", ctypes.c_float), ("fHighFreqRTRatio", ctypes.c_float)]


def _exp_dir():
    return os.path.join(os.environ.get('LOCALAPPDATA', ''), 'KaraDom', 'dipendenze', 'Expander')


def _banco():
    # 1) banco scelto dall'utente nella finestra Expander (config exp_banco_path)
    p = _cfg('exp_banco_path', '')
    if p and os.path.isfile(p):
        return p
    # 2) altrimenti i file nella cartella Expander
    d = _exp_dir()
    for c in (os.path.join(d, 'banco_toh.sf3'), os.path.join(d, 'banco.sf3'),
              os.path.join(d, 'banco.sf2')):
        if os.path.isfile(c):
            return c
    import glob
    g = sorted(glob.glob(os.path.join(d, '*.sf3'))) or sorted(glob.glob(os.path.join(d, '*.sf2')))
    return g[0] if g else ''


def _cfg(chiave, default=''):
    try:
        from moduli.database import Database
        v = Database.get_config(chiave, default)
        return v if v not in (None, '') else default
    except Exception:
        return default


def _int(v, d):
    try:
        return int(float(v))
    except Exception:
        return d


def _on():
    return str(_cfg('expander_socket', '0')) == '1'


def _same(a, b):
    try:
        return os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(b))
    except Exception:
        return a == b


# ============ DSP (Volume / Brillantezza / Riverbero) sul motore file-based ============

def _applica_fx(eng):
    """Applica volume + EQ acuti (brillantezza) + riverbero DX8 SULLO STREAM del
    motore. Va richiamata dopo ogni load (lo stream si ricrea). Se lo stream non
    c'e' ancora, i valori restano in config e si applicano al prossimo load."""
    try:
        from moduli import bass_engine as _bemod
    except Exception:
        return
    b = getattr(_bemod, '_lib', None)
    b = getattr(b, 'bass', None) if b else None
    st = getattr(eng, '_stream', 0)
    if not b or not st:
        return
    vol = _int(_cfg('exp_sw_vol', '100'), 100)
    bri = _int(_cfg('exp_sw_bright', '50'), 50)
    rev = _int(_cfg('exp_sw_reverb', '20'), 20)
    bas = _int(_cfg('exp_sw_bass', '75'), 75)   # 50 = neutro, 75 = +6 dB sui gravi
    # --- volume (attributo dello stream) ---
    try:
        b.BASS_ChannelSetAttribute.argtypes = [DWORD, DWORD, ctypes.c_float]
        b.BASS_ChannelSetAttribute(st, BASS_ATTRIB_VOL, ctypes.c_float(max(0, min(100, vol)) / 100.0))
    except Exception:
        pass
    # --- prototipi FX ---
    try:
        b.BASS_ChannelSetFX.restype = DWORD
        b.BASS_ChannelSetFX.argtypes = [DWORD, DWORD, ctypes.c_int]
        b.BASS_FXSetParameters.argtypes = [DWORD, ctypes.c_void_p]
    except Exception:
        return
    # --- brillantezza = EQ acuti (shelf a 7 kHz), 50 = neutro ---
    try:
        hf = getattr(eng, '_fx_eq_109', 0)
        if not hf:
            hf = b.BASS_ChannelSetFX(st, BASS_FX_DX8_PARAMEQ, 2)
            eng._fx_eq_109 = hf
        if hf:
            g = (max(0, min(100, bri)) - 50) / 50.0 * 12.0   # -12..+12 dB
            b.BASS_FXSetParameters(hf, ctypes.byref(DX8_PARAMEQ(7000.0, 18.0, g)))
    except Exception:
        pass
    # --- bassi = EQ gravi (peaking a 80 Hz, banda larga 36 semitoni), 50 = neutro ---
    try:
        hb = getattr(eng, '_fx_bass_109', 0)
        if not hb:
            hb = b.BASS_ChannelSetFX(st, BASS_FX_DX8_PARAMEQ, 3)
            eng._fx_bass_109 = hb
        gb = (max(0, min(100, bas)) - 50) / 50.0 * 15.0   # -15..+15 dB
        if hb:
            r = b.BASS_FXSetParameters(hb, ctypes.byref(DX8_PARAMEQ(80.0, 36.0, gb)))
            print('[EXP109] EQ bassi: fx=%s gain=%.1f dB set=%s' % (hb, gb, r))
        else:
            try:
                b.BASS_ErrorGetCode.restype = ctypes.c_int
                ec = b.BASS_ErrorGetCode()
            except Exception:
                ec = '?'
            print('[EXP109] EQ bassi NON creato (BASS_ChannelSetFX=0, err=%s): '
                  'i DX8 non si agganciano a questo stream' % ec)
    except Exception as e:
        print('[EXP109] EQ bassi errore:', e)
    # --- riverbero ---
    try:
        hr = getattr(eng, '_fx_rev_109', 0)
        if not hr:
            hr = b.BASS_ChannelSetFX(st, BASS_FX_DX8_REVERB, 1)
            eng._fx_rev_109 = hr
        if hr:
            v = max(0, min(100, rev))
            mix = -96.0 if v == 0 else (-24.0 + (v / 100.0) * 24.0)
            b.BASS_FXSetParameters(hr, ctypes.byref(DX8_REVERB(0.0, mix, 1500.0, 0.5)))
    except Exception:
        pass


# ============ MOTORE file-based con il banco expander ============

def _motore():
    try:
        from moduli.bass_engine import get_bass_engine, is_bass_available
    except Exception as e:
        print('[EXP109] bass_engine non disponibile:', e)
        return None
    if not is_bass_available():
        print('[EXP109] BASS non disponibile')
        return None
    b = _banco()
    if not b:
        print('[EXP109] banco non trovato in', _exp_dir())
        return None
    try:
        eng = get_bass_engine()
        if not getattr(eng, 'initialized', False):
            eng.initialize(b)
        elif not (eng.soundfont_path and _same(eng.soundfont_path, b)):
            eng.synth.sfload(b)
        eng._exp_soft_active = True
        # se c'e' gia' uno stream in corso, applico subito il DSP
        _applica_fx(eng)
        return eng
    except Exception as e:
        print('[EXP109] motore errore:', e)
        return None


def _ripristina():
    """Esco dall'expander software: rimetto il SoundFont normale e spengo il flag."""
    try:
        from moduli.bass_engine import get_bass_engine, is_bass_available
    except Exception:
        return
    if not is_bass_available():
        return
    try:
        eng = get_bass_engine()
        if not getattr(eng, 'initialized', False) or not getattr(eng, '_exp_soft_active', False):
            return
        b = _banco()
        if b and eng.soundfont_path and _same(eng.soundfont_path, b):
            sf = None
            try:
                sf = eng._find_soundfont()
            except Exception:
                sf = None
            if sf and not _same(sf, b) and os.path.isfile(sf):
                eng.synth.sfload(sf)
        eng._exp_soft_active = False
    except Exception as e:
        print('[EXP109] ripristino:', e)


def apply():
    import sys
    mod = sys.modules.get('moduli.expander_midi')
    if mod is None:
        try:
            import moduli.expander_midi as mod  # noqa
        except Exception:
            print('[EXP109] expander_midi non presente (ok)')
            return False
    if getattr(mod, '_filebased_109', False):
        return True

    # 1) get_expander_player: HW vero -> precedenza; software -> MOTORE FILE-BASED.
    if hasattr(mod, 'get_expander_player'):
        _ogp = mod.get_expander_player

        def _get_player(*a, **k):
            # rilevo l'HW VERO SENZA costruire il player software (se no la 104
            # costruirebbe l'ExpanderPlayer in-process come effetto collaterale).
            real_hw = False
            try:
                porta = mod.detect_expander()
                if porta and porta.get('id', -1) != -1 \
                        and 'software' not in (porta.get('nome', '') or '').lower():
                    real_hw = True
            except Exception:
                real_hw = False
            if real_hw:
                print('[EXP109] scelta: HW fisico')
                _ripristina()
                try:
                    return _ogp(*a, **k)      # costruisce il player HW (winmm), come sempre
                except Exception as e:
                    print('[EXP109] player HW:', e)
                    return None
            if _on():
                eng = _motore()
                if eng is not None:
                    print('[EXP109] scelta: SOFTWARE (BassEngine file-based)')
                    return eng
                print('[EXP109] software richiesto MA _motore() = None (niente BassEngine)')
                return None
            print('[EXP109] scelta: nessun expander (_on=False)')
            _ripristina()
            return None

        mod._get_player_orig109 = _ogp
        mod.get_expander_player = _get_player

    # 2) DSP: riaggancio i cursori (106 chiama ex._exp_soft_dsp) al motore file-based.
    def _dsp(vol=None, bright=None, reverb=None, bass=None):
        try:
            if vol is not None:
                mod._set_cfg('exp_sw_vol', str(_int(vol, 100)))
            if bright is not None:
                mod._set_cfg('exp_sw_bright', str(_int(bright, 50)))
            if reverb is not None:
                mod._set_cfg('exp_sw_reverb', str(_int(reverb, 20)))
            if bass is not None:
                mod._set_cfg('exp_sw_bass', str(_int(bass, 75)))
        except Exception:
            pass
        try:
            from moduli.bass_engine import get_bass_engine
            _applica_fx(get_bass_engine())
        except Exception as e:
            print('[EXP109] dsp:', e)
    mod._exp_soft_dsp = _dsp

    # 3) ri-applico il DSP a OGNI nuovo brano (lo stream si ricrea nel load)
    try:
        import moduli.bass_engine as _bemod
        BE = getattr(_bemod, 'BassEngine', None)
        if BE is not None and hasattr(BE, 'load') and not getattr(BE, '_fx109', False):
            _oload = BE.load

            def _load(self, *a, **k):
                r = _oload(self, *a, **k)
                try:
                    if r and getattr(self, '_exp_soft_active', False) and getattr(self, 'is_midi', False):
                        self._fx_eq_109 = 0   # lo stream e' nuovo: i vecchi handle non valgono
                        self._fx_rev_109 = 0
                        self._fx_bass_109 = 0
                        _applica_fx(self)
                except Exception as e:
                    print('[EXP109] fx post-load:', e)
                return r

            BE.load = _load
            BE._fx109 = True
    except Exception as e:
        print('[EXP109] hook load:', e)

    # 4) etichetta mixer: "Expander Software" quando suona il banco
    try:
        import moduli.mixer as _mx
        P = getattr(_mx, 'MIDIMixerPanel', None)
        if P is not None and hasattr(P, '_update_soundfont_display') and not getattr(P, '_lbl_109', False):
            _osf = P._update_soundfont_display

            def _usd(self, *a, **k):
                r = _osf(self, *a, **k)
                try:
                    from moduli.bass_engine import get_bass_engine
                    lbl = getattr(self, 'sf_label', None)
                    if lbl is not None and getattr(get_bass_engine(), '_exp_soft_active', False):
                        lbl.config(text='Expander Software', fg='#c77dff')
                except Exception:
                    pass
                return r

            P._update_soundfont_display = _usd
            P._lbl_109 = True
    except Exception as e:
        print('[EXP109] etichetta:', e)

    mod._filebased_109 = True
    print('[EXP109] expander software FILE-BASED (BassEngine + banco) + DSP + LED + etichetta')
    return True


def revert():
    try:
        import sys
        mod = sys.modules.get('moduli.expander_midi')
        if mod is not None and getattr(mod, '_filebased_109', False):
            if hasattr(mod, '_get_player_orig109'):
                mod.get_expander_player = mod._get_player_orig109
            del mod._filebased_109
    except Exception:
        pass


try:
    apply()
except Exception as _e:
    print('patch 109: %s' % _e)
