import ctypes
import numpy as _np

DWORD = ctypes.c_uint32
BASS_FX_DX8_REVERB = 8
_SR = 44100
_WIDE_DELAY = int(0.012 * _SR)
_LIM_THR = 0.90   # sotto soglia lineare, sopra satura dolce -> mai clip


class DX8_REVERB(ctypes.Structure):
    _fields_ = [("fInGain", ctypes.c_float), ("fReverbMix", ctypes.c_float),
                ("fReverbTime", ctypes.c_float), ("fHighFreqRTRatio", ctypes.c_float)]


def _peak(f0, gdb, q):
    A = 10 ** (gdb / 40.0); w0 = 2 * _np.pi * f0 / _SR; c = _np.cos(w0); s = _np.sin(w0); a = s / (2 * q)
    b = _np.array([1 + a * A, -2 * c, 1 - a * A]); ao = _np.array([1 + a / A, -2 * c, 1 - a / A])
    return b / ao[0], _np.array([1.0, ao[1] / ao[0], ao[2] / ao[0]])


def _highshelf(f0, gdb, q=0.707):
    A = 10 ** (gdb / 40.0); w0 = 2 * _np.pi * f0 / _SR; c = _np.cos(w0); s = _np.sin(w0); a = s / (2 * q)
    b = _np.array([A * ((A + 1) + (A - 1) * c + 2 * _np.sqrt(A) * a), -2 * A * ((A - 1) + (A + 1) * c), A * ((A + 1) + (A - 1) * c - 2 * _np.sqrt(A) * a)])
    ao = _np.array([(A + 1) - (A - 1) * c + 2 * _np.sqrt(A) * a, 2 * ((A - 1) - (A + 1) * c), (A + 1) - (A - 1) * c - 2 * _np.sqrt(A) * a])
    return b / ao[0], _np.array([1.0, ao[1] / ao[0], ao[2] / ao[0]])


def _highpass(f0, q=0.707):
    w0 = 2 * _np.pi * f0 / _SR; c = _np.cos(w0); s = _np.sin(w0); a = s / (2 * q)
    b = _np.array([(1 + c) / 2, -(1 + c), (1 + c) / 2]); ao = _np.array([1 + a, -2 * c, 1 - a])
    return b / ao[0], _np.array([1.0, ao[1] / ao[0], ao[2] / ao[0]])


def _profilo(hpf, bass, scoop, air, e1, e2, topcut, wide, rev_ms, rev_mix):
    # e1/e2 = (hp_freq, drive, amt); topcut = (freq, gain_dB) shelf per domare l'estremo
    return {
        'hp': _highpass(hpf),
        'bass': _peak(*bass),
        'scoop': _peak(*scoop),
        'air': _highshelf(*air),
        'e1f': _highpass(e1[0]), 'e1d': e1[1], 'e1a': e1[2],
        'e2f': _highpass(e2[0]), 'e2d': e2[1], 'e2a': e2[2],
        'topcut': _highshelf(topcut[0], topcut[1]),
        'wide': _highpass(450.0), 'wide_amt': wide,
        'rev_ms': rev_ms, 'rev_mix': rev_mix,
    }


# SICURO (scarto 5.2 dB): equilibrato, niente rimbombo/asprezza
_SAFE = _profilo(48.0, (160.0, 5.5, 1.3), (2000.0, -8.0, 1.0), (9000.0, 3.0),
                 (3600.0, 3.0, 0.55), (7000.0, 5.0, 0.0), (13000.0, 0.0),
                 0.70, 1200.0, -16.0)
# SPINTO/MAX (scarto 4.23 dB, il piu' vicino possibile al vero X-Light col banco kdl4):
# basso stretto (155/+11), scavo 2k, DUE exciter (4-8k + 8-12k) che CREANO l'aria mancante,
# taglio sopra 13k per non frizzare l'estremo, stereo largo, riverbero ~3 s come l'X-Light.
# brillantezza -6.2 (vero -6.1), 8-12k riempiti, stereo 0.75 (vero 0.92). Rumore di fondo NON sale.
_PUSH = _profilo(78.0, (128.0, 15.5, 1.7), (2000.0, -8.7, 1.0), (9000.0, 0.0),
                 (3500.0, 3.0, 0.12), (7000.0, 3.0, 1.10), (12500.0, -8.0),
                 2.10, 3000.0, -12.0)
_CUR = _SAFE
# Exciter "ducking": si abbassa da solo quando gli acuti sono forti (transienti,
# piatti) -> aria sui suoni tenuti, niente frizzo sulla batteria.
_DUCK = 12.0
_ENV_A = 0.0045                        # inviluppo ~5 ms
_Benv = _np.array([_ENV_A]); _Aenv = _np.array([1.0, -(1.0 - _ENV_A)])
_ST = {}
DSPPROC = ctypes.CFUNCTYPE(None, DWORD, DWORD, ctypes.c_void_p, DWORD, ctypes.c_void_p)


def _softlim(y):
    a = _np.abs(y)
    over = a > _LIM_THR
    if over.any():
        y = y.copy()
        y[over] = _np.sign(y[over]) * (_LIM_THR + (1.0 - _LIM_THR) * _np.tanh((a[over] - _LIM_THR) / (1.0 - _LIM_THR)))
    return y


def _proc(handle, channel, buffer, length, user):
    try:
        from scipy.signal import lfilter
        P = _CUR
        n = length // 4
        if n < 8:
            return
        arr = _np.ctypeslib.as_array((ctypes.c_float * n).from_address(buffer))
        x = arr.reshape(-1, 2)
        if _ST.get('ch') != channel:
            _ST.clear(); _ST['ch'] = channel
        for ci in (0, 1):
            sig = x[:, ci].astype(_np.float64)
            for key in ('hp', 'bass', 'scoop', 'air'):
                b, a = P[key]; z = _ST.get('%s%d' % (key, ci))
                sig, z = lfilter(b, a, sig, zi=z if z is not None else _np.zeros(2)); _ST['%s%d' % (key, ci)] = z
            # exciter 1 (4-8k) con ducking sui transienti
            b, a = P['e1f']; z = _ST.get('e1%d' % ci)
            h1, z = lfilter(b, a, sig, zi=z if z is not None else _np.zeros(2)); _ST['e1%d' % ci] = z
            ze = _ST.get('e1env%d' % ci)
            env1, ze = lfilter(_Benv, _Aenv, _np.abs(h1), zi=ze if ze is not None else _np.zeros(1)); _ST['e1env%d' % ci] = ze
            sig = sig + _np.tanh(h1 * P['e1d']) * P['e1a'] / (1.0 + _DUCK * env1)
            # exciter 2 (8-12k) -> crea l'aria che nel banco NON c'e', con ducking
            if P['e2a'] > 0:
                b, a = P['e2f']; z = _ST.get('e2%d' % ci)
                h2, z = lfilter(b, a, sig, zi=z if z is not None else _np.zeros(2)); _ST['e2%d' % ci] = z
                ze = _ST.get('e2env%d' % ci)
                env2, ze = lfilter(_Benv, _Aenv, _np.abs(h2), zi=ze if ze is not None else _np.zeros(1)); _ST['e2env%d' % ci] = ze
                sig = sig + _np.tanh(h2 * P['e2d']) * P['e2a'] / (1.0 + _DUCK * env2)
            # taglio dell'estremo (13k) per non frizzare
            b, a = P['topcut']; z = _ST.get('tc%d' % ci)
            sig, z = lfilter(b, a, sig, zi=z if z is not None else _np.zeros(2)); _ST['tc%d' % ci] = z
            x[:, ci] = sig.astype(_np.float32)
        # widener che PRESERVA lo stereo (aggiunge side, NON collassa a mono)
        bw, aw = P['wide']; mid = (x[:, 0] + x[:, 1]) * 0.5
        z = _ST.get('zw'); midhp, z = lfilter(bw, aw, mid, zi=z if z is not None else _np.zeros(2)); _ST['zw'] = z
        wt = _ST.get('wt')
        if wt is None or len(wt) != _WIDE_DELAY:
            wt = _np.zeros(_WIDE_DELAY)
        cat = _np.concatenate([wt, midhp]); delayed = cat[:len(midhp)]; _ST['wt'] = cat[-_WIDE_DELAY:].copy()
        extra = (midhp - delayed) * P['wide_amt']
        x[:, 0] = _softlim(x[:, 0].astype(_np.float64) + extra).astype(_np.float32)
        x[:, 1] = _softlim(x[:, 1].astype(_np.float64) - extra).astype(_np.float32)
    except Exception:
        pass


_cb = DSPPROC(_proc)


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_167', '1')) == '0'
    except Exception:
        return False


def _scegli_profilo():
    global _CUR
    try:
        from moduli.database import Database
        _CUR = _PUSH if str(Database.get_config('xl_spinta', '0')) == '1' else _SAFE
    except Exception:
        _CUR = _SAFE
    return _CUR


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
    P = _scegli_profilo()
    try:
        b.BASS_ChannelSetFX.restype = DWORD
        b.BASS_ChannelSetFX.argtypes = [DWORD, DWORD, ctypes.c_int]
        b.BASS_FXSetParameters.argtypes = [DWORD, ctypes.c_void_p]
        b.BASS_ChannelSetDSP.restype = DWORD
        b.BASS_ChannelSetDSP.argtypes = [DWORD, DSPPROC, ctypes.c_void_p, ctypes.c_int]
        hr = getattr(eng, '_fx_xl_rev', 0)
        if not hr or getattr(eng, '_fx_xl_rev_st', 0) != st:
            hr = b.BASS_ChannelSetFX(st, BASS_FX_DX8_REVERB, 25)
            eng._fx_xl_rev = hr; eng._fx_xl_rev_st = st
        if hr:
            b.BASS_FXSetParameters(hr, ctypes.byref(DX8_REVERB(0.0, P['rev_mix'], P['rev_ms'], 0.5)))
        _ST.clear()
        if getattr(eng, '_xl_dsp_st', 0) != st:
            b.BASS_ChannelSetDSP(st, _cb, None, 0)
            eng._xl_dsp_st = st
        print('[XL167] profilo %s applicato (riverbero %d ms)' % ('SPINTO/MAX' if P is _PUSH else 'sicuro', int(P['rev_ms'])))
    except Exception as e:
        print('[XL167] errore:', e)


def apply():
    if _spenta():
        return False
    _scegli_profilo()
    try:
        from moduli.database import Database
        Database.set_config('patch_159', '0')
        # il banco (core.kdl) lo imposta la 168: la 167 NON tocca exp_banco
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
            slot = str(_D.get_config('exp_slot', 'default'))
            if r and sw and slot != 'mio' and getattr(self, 'is_midi', False):
                _applica_xlight(self)
        except Exception as e:
            print('[XL167] hook:', e)
        return r
    Eng.load = load
    Eng._xl167 = True
    print('[XL167] expander X-Light pronto (interruttore xl_spinta)')
    return True


try:
    apply()
except Exception as _e:
    print('patch 167: %s' % _e)
