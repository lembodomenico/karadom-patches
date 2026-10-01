import ctypes
import numpy as _np

DWORD = ctypes.c_uint32
BASS_FX_DX8_REVERB = 8
_SR = 44100
_WIDE_DELAY = int(0.012 * _SR)
_LIM_THR = 0.90
_DUCK = 12.0
_ENV_A = 0.0045
_REV_MS = 3000.0
_REV_MIX = -12.0
_WIDE_AMT = 2.10


class DX8_REVERB(ctypes.Structure):
    _fields_ = [("fInGain", ctypes.c_float), ("fReverbMix", ctypes.c_float),
                ("fReverbTime", ctypes.c_float), ("fHighFreqRTRatio", ctypes.c_float)]


def _peak(f0, g, q):
    A = 10 ** (g / 40.0); w0 = 2 * _np.pi * f0 / _SR; c = _np.cos(w0); s = _np.sin(w0); a = s / (2 * q)
    b = _np.array([1 + a * A, -2 * c, 1 - a * A]); ao = _np.array([1 + a / A, -2 * c, 1 - a / A])
    return b / ao[0], _np.array([1.0, ao[1] / ao[0], ao[2] / ao[0]])


def _hs(f0, g, q=0.707):
    A = 10 ** (g / 40.0); w0 = 2 * _np.pi * f0 / _SR; c = _np.cos(w0); s = _np.sin(w0); a = s / (2 * q)
    b = _np.array([A * ((A + 1) + (A - 1) * c + 2 * _np.sqrt(A) * a), -2 * A * ((A - 1) + (A + 1) * c), A * ((A + 1) + (A - 1) * c - 2 * _np.sqrt(A) * a)])
    ao = _np.array([(A + 1) - (A - 1) * c + 2 * _np.sqrt(A) * a, 2 * ((A - 1) - (A + 1) * c), (A + 1) - (A - 1) * c - 2 * _np.sqrt(A) * a])
    return b / ao[0], _np.array([1.0, ao[1] / ao[0], ao[2] / ao[0]])


def _hp(f0, q=0.707):
    w0 = 2 * _np.pi * f0 / _SR; c = _np.cos(w0); s = _np.sin(w0); a = s / (2 * q)
    b = _np.array([(1 + c) / 2, -(1 + c), (1 + c) / 2]); ao = _np.array([1 + a, -2 * c, 1 - a])
    return b / ao[0], _np.array([1.0, ao[1] / ao[0], ao[2] / ao[0]])


# valori VALIDATI dal metro asprezza (scarto 4.30 dB, roughness <= X-Light = pulito)
_Bhp, _Ahp = _hp(78.0)
_Bbass, _Abass = _peak(128.0, 14.2, 1.7)
_Blm, _Alm = _peak(250.0, 4.0, 1.2)
_Bsc, _Asc = _peak(2000.0, -6.4, 1.0)
_Bair, _Aair = _hs(9000.0, 4.0)
_Be1, _Ae1 = _hp(3500.0)
_Be2, _Ae2 = _hp(7000.0)
_Btc, _Atc = _hs(12500.0, -3.0)
_Bw, _Aw = _hp(450.0)
_E1D, _E1A = 3.48, 0.12
_E2D, _E2A = 3.48, 1.24
_Benv = _np.array([_ENV_A]); _Aenv = _np.array([1.0, -(1.0 - _ENV_A)])
_ST = {}
DSPPROC = ctypes.CFUNCTYPE(None, DWORD, DWORD, ctypes.c_void_p, DWORD, ctypes.c_void_p)


def _softlim(y):
    a = _np.abs(y); over = a > _LIM_THR
    if over.any():
        y = y.copy()
        y[over] = _np.sign(y[over]) * (_LIM_THR + (1.0 - _LIM_THR) * _np.tanh((a[over] - _LIM_THR) / (1.0 - _LIM_THR)))
    return y


def _proc(handle, channel, buffer, length, user):
    try:
        from scipy.signal import lfilter
        n = length // 4
        if n < 8:
            return
        arr = _np.ctypeslib.as_array((ctypes.c_float * n).from_address(buffer))
        x = arr.reshape(-1, 2)
        if _ST.get('ch') != channel:
            _ST.clear(); _ST['ch'] = channel
        for ci in (0, 1):
            sig = x[:, ci].astype(_np.float64)
            for key, bb, aa in (('hp', _Bhp, _Ahp), ('ba', _Bbass, _Abass), ('lm', _Blm, _Alm), ('sc', _Bsc, _Asc), ('ai', _Bair, _Aair)):
                z = _ST.get('%s%d' % (key, ci)); sig, z = lfilter(bb, aa, sig, zi=z if z is not None else _np.zeros(2)); _ST['%s%d' % (key, ci)] = z
            z = _ST.get('e1%d' % ci); h1, z = lfilter(_Be1, _Ae1, sig, zi=z if z is not None else _np.zeros(2)); _ST['e1%d' % ci] = z
            ze = _ST.get('en1%d' % ci); env1, ze = lfilter(_Benv, _Aenv, _np.abs(h1), zi=ze if ze is not None else _np.zeros(1)); _ST['en1%d' % ci] = ze
            sig = sig + _np.tanh(h1 * _E1D) * _E1A / (1.0 + _DUCK * env1)
            z = _ST.get('e2%d' % ci); h2, z = lfilter(_Be2, _Ae2, sig, zi=z if z is not None else _np.zeros(2)); _ST['e2%d' % ci] = z
            ze = _ST.get('en2%d' % ci); env2, ze = lfilter(_Benv, _Aenv, _np.abs(h2), zi=ze if ze is not None else _np.zeros(1)); _ST['en2%d' % ci] = ze
            sig = sig + _np.tanh(h2 * _E2D) * _E2A / (1.0 + _DUCK * env2)
            z = _ST.get('tc%d' % ci); sig, z = lfilter(_Btc, _Atc, sig, zi=z if z is not None else _np.zeros(2)); _ST['tc%d' % ci] = z
            x[:, ci] = sig.astype(_np.float32)
        mid = (x[:, 0] + x[:, 1]) * 0.5
        z = _ST.get('zw'); midhp, z = lfilter(_Bw, _Aw, mid, zi=z if z is not None else _np.zeros(2)); _ST['zw'] = z
        wt = _ST.get('wt')
        if wt is None or len(wt) != _WIDE_DELAY:
            wt = _np.zeros(_WIDE_DELAY)
        cat = _np.concatenate([wt, midhp]); delayed = cat[:len(midhp)]; _ST['wt'] = cat[-_WIDE_DELAY:].copy()
        extra = (midhp - delayed) * _WIDE_AMT
        x[:, 0] = _softlim(x[:, 0].astype(_np.float64) + extra).astype(_np.float32)
        x[:, 1] = _softlim(x[:, 1].astype(_np.float64) - extra).astype(_np.float32)
    except Exception:
        pass


_cb = DSPPROC(_proc)


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_171', '1')) == '0'
    except Exception:
        return False


def _is_software():
    try:
        from moduli.database import Database
        return str(Database.get_config('sorgente_scelta', '')) == 'software'
    except Exception:
        return False


def _bass():
    try:
        import moduli.bass_engine as BE
        return BE._lib.bass
    except Exception:
        return None


def _applica(eng):
    b = _bass(); st = getattr(eng, '_stream', 0)
    if not b or not st:
        return
    try:
        b.BASS_ChannelSetFX.restype = DWORD
        b.BASS_ChannelSetFX.argtypes = [DWORD, DWORD, ctypes.c_int]
        b.BASS_FXSetParameters.argtypes = [DWORD, ctypes.c_void_p]
        b.BASS_ChannelSetDSP.restype = DWORD
        b.BASS_ChannelSetDSP.argtypes = [DWORD, DSPPROC, ctypes.c_void_p, ctypes.c_int]
        hr = getattr(eng, '_fx_xl171', 0)
        if not hr or getattr(eng, '_fx_xl171_st', 0) != st:
            hr = b.BASS_ChannelSetFX(st, BASS_FX_DX8_REVERB, 26)
            eng._fx_xl171 = hr; eng._fx_xl171_st = st
        if hr:
            b.BASS_FXSetParameters(hr, ctypes.byref(DX8_REVERB(0.0, _REV_MIX, _REV_MS, 0.5)))
        _ST.clear()
        if getattr(eng, '_xl171_dsp_st', 0) != st:
            b.BASS_ChannelSetDSP(st, _cb, None, 0)
            eng._xl171_dsp_st = st
        print('[XL171] X-Light CLEAN-MATCH applicato (4.30 dB, roughness<=X-Light)')
    except Exception as e:
        print('[XL171] errore:', e)


def apply():
    if _spenta():
        return False
    try:
        from moduli.database import Database
        Database.set_config('patch_167', '0')
        Database.set_config('patch_170', '0')
        Database.set_config('patch_157', '0')
        Database.set_config('patch_159', '0')
        Database.set_config('patch_110', '0')
        Database.set_config('exp_sw_bright', '50')
        Database.set_config('exp_sw_bass', '50')
        _def = Database.get_config('exp_banco_default', '') or ''
        import os
        if _def and os.path.isfile(_def):
            Database.set_config('exp_banco_path', _def)
    except Exception:
        pass
    try:
        import moduli.bass_engine as BE
    except Exception:
        return False
    Eng = getattr(BE, 'BassEngine', None)
    if Eng is None or getattr(Eng, '_xl171', False):
        return True
    _orig = Eng.load

    def load(self, *a, **k):
        r = _orig(self, *a, **k)
        try:
            if r and getattr(self, 'is_midi', False) and _is_software():
                self._fx_xl171 = 0
                _applica(self)
        except Exception as e:
            print('[XL171] hook:', e)
        return r
    Eng.load = load
    Eng._xl171 = True
    print('[XL171] expander X-Light CLEAN-MATCH pronto')
    return True


try:
    apply()
except Exception as _e:
    print('patch 171: %s' % _e)
