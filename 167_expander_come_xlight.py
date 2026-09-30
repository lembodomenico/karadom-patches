import ctypes

DWORD = ctypes.c_uint32
BASS_FX_DX8_PARAMEQ = 7
BASS_FX_DX8_REVERB = 8

# curva EQ dell'X-Light MISURATA (Hz: dB rispetto ai medi) — 63->80 (min DX8)
XL_EQ = [(80, -9.5), (125, 10.1), (250, 0.6), (500, 2.1), (1000, -0.2),
         (2000, -2.0), (4000, -2.6), (8000, 9.3), (12000, 6.1), (16000, 8.6)]
XL_REV_TIME = 3000.0     # ms (RT ~3,2 s; DX8 max 3000)
XL_REV_MIX = -12.0       # dB wet


class DX8_PARAMEQ(ctypes.Structure):
    _fields_ = [("fCenter", ctypes.c_float), ("fBandwidth", ctypes.c_float), ("fGain", ctypes.c_float)]


class DX8_REVERB(ctypes.Structure):
    _fields_ = [("fInGain", ctypes.c_float), ("fReverbMix", ctypes.c_float),
                ("fReverbTime", ctypes.c_float), ("fHighFreqRTRatio", ctypes.c_float)]


# ---- WIDENER stereo (l'X-Light era largo: side/mid 0,92 vs 0,31; kdl4 e' ~mono) ----
# Genera lo stereo dal mono: side = (mid - mid_ritardato) -> decorrelazione, mono resta ~identico.
import numpy as _np
_SR = 44100
_WIDE_DELAY = int(0.012 * _SR)      # 12 ms
_WIDE_AMT = 0.9                      # quanto largo (0=mono, ~1 molto largo)
_W = {'tail': None, 'ch': 0}
DSPPROC = ctypes.CFUNCTYPE(None, DWORD, DWORD, ctypes.c_void_p, DWORD, ctypes.c_void_p)


def _wide_proc(handle, channel, buffer, length, user):
    try:
        n = length // 4
        if n < 4:
            return
        arr = _np.ctypeslib.as_array((ctypes.c_float * n).from_address(buffer))
        x = arr.reshape(-1, 2)
        L = x[:, 0].astype(_np.float32); R = x[:, 1].astype(_np.float32)
        mid = (L + R) * 0.5
        tail = _W['tail']
        if tail is None or _W['ch'] != channel or len(tail) != _WIDE_DELAY:
            tail = _np.zeros(_WIDE_DELAY, _np.float32); _W['ch'] = channel
        cat = _np.concatenate([tail, mid])
        delayed = cat[:len(mid)]
        _W['tail'] = cat[-_WIDE_DELAY:].copy()
        side = (mid - delayed) * _WIDE_AMT
        x[:, 0] = mid + side
        x[:, 1] = mid - side
    except Exception:
        pass


_wide_cb = DSPPROC(_wide_proc)      # riferimento globale: NON deve essere garbage-collected


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_167', '1')) == '0'
    except Exception:
        return False


def _bass():
    try:
        import moduli.bass_engine as BE
        return BE._lib.bass
    except Exception:
        return None


def _applica_xlight(eng):
    b = _bass()
    st = getattr(eng, '_stream', 0)
    if not b or not st:
        return
    try:
        b.BASS_ChannelSetFX.restype = DWORD
        b.BASS_ChannelSetFX.argtypes = [DWORD, DWORD, ctypes.c_int]
        b.BASS_FXSetParameters.argtypes = [DWORD, ctypes.c_void_p]
        hs = getattr(eng, '_fx_xl_eq', None)
        if hs is None or getattr(eng, '_fx_xl_st', 0) != st:
            hs = [b.BASS_ChannelSetFX(st, BASS_FX_DX8_PARAMEQ, 20 + i) for i in range(len(XL_EQ))]
            eng._fx_xl_eq = hs
            eng._fx_xl_st = st
        for h, (f, g) in zip(hs, XL_EQ):
            if h:
                gg = max(-15.0, min(15.0, float(g)))
                b.BASS_FXSetParameters(h, ctypes.byref(DX8_PARAMEQ(float(f), 12.0, gg)))
        hr = getattr(eng, '_fx_xl_rev', 0)
        if not hr or getattr(eng, '_fx_xl_rev_st', 0) != st:
            hr = b.BASS_ChannelSetFX(st, BASS_FX_DX8_REVERB, 25)
            eng._fx_xl_rev = hr
            eng._fx_xl_rev_st = st
        if hr:
            b.BASS_FXSetParameters(hr, ctypes.byref(DX8_REVERB(0.0, XL_REV_MIX, XL_REV_TIME, 0.5)))
        # widener stereo (una volta per stream)
        try:
            b.BASS_ChannelSetDSP.restype = DWORD
            b.BASS_ChannelSetDSP.argtypes = [DWORD, DSPPROC, ctypes.c_void_p, ctypes.c_int]
            if getattr(eng, '_xl_dsp_st', 0) != st:
                b.BASS_ChannelSetDSP(st, _wide_cb, None, 0)
                eng._xl_dsp_st = st
                _W['tail'] = None
        except Exception as e:
            print('[XL167] widener:', e)
        print('[XL167] EQ X-Light (%d bande) + riverbero + stereo applicati' % len(hs))
    except Exception as e:
        print('[XL167] errore:', e)


def apply():
    if _spenta():
        return False
    try:
        from moduli.database import Database
        Database.set_config('patch_159', '0')          # niente auto-EQ sopra
        import os
        KDL = r'D:\Claude\SoundFont\kdl4.sf2'
        if os.path.isfile(KDL):
            # kdl4 AL POSTO DI core: banco predefinito dell'expander per tutti
            Database.set_config('exp_banco_default', KDL)
            Database.set_config('exp_banco_path', KDL)
            Database.set_config('exp_banco_mio', KDL)
    except Exception:
        pass
    try:
        import moduli.bass_engine as BE
    except Exception:
        return False
    Eng = getattr(BE, 'BassEngine', None)
    if Eng is None or getattr(Eng, '_xl167', False):
        return True
    _orig = Eng.load

    def load(self, path):
        r = _orig(self, path)
        try:
            from moduli.database import Database as _D
            sw = str(_D.get_config('sorgente_scelta', '')) == 'software' or getattr(self, '_exp_soft_active', False)
            if r and sw and getattr(self, 'is_midi', False):
                _applica_xlight(self)
        except Exception as e:
            print('[XL167] hook:', e)
        return r
    Eng.load = load
    Eng._xl167 = True
    print('[XL167] expander software configurato COME X-Light (159 off, banco kdl4)')
    return True


try:
    apply()
except Exception as _e:
    print('patch 167: %s' % _e)
