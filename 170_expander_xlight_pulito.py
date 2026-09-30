import ctypes

DWORD = ctypes.c_uint32
FX_PARAMEQ = 7
# EQ X-Light PULITA (misurata: scarto 5.3 dB, niente exciter -> niente frizzo).
# (centro Hz, gain dB, banda semitoni)
_BANDS = [(60.0, -3.0, 20.0),
          (125.0, 8.0, 20.0),
          (2000.0, -8.0, 17.0),
          (6000.0, 7.0, 23.0),
          (11000.0, 8.0, 26.0)]


class _PEQ(ctypes.Structure):
    _fields_ = [("fCenter", ctypes.c_float), ("fBandwidth", ctypes.c_float),
                ("fGain", ctypes.c_float)]


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_170', '1')) == '0'
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
    b = _bass()
    st = getattr(eng, '_stream', 0)
    if not b or not st:
        return
    try:
        b.BASS_ChannelSetFX.restype = DWORD
        b.BASS_ChannelSetFX.argtypes = [DWORD, DWORD, ctypes.c_int]
        b.BASS_FXSetParameters.argtypes = [DWORD, ctypes.c_void_p]
        handles = getattr(eng, '_fx170', None)
        if not handles or getattr(eng, '_fx170_st', 0) != st:
            handles = [b.BASS_ChannelSetFX(st, FX_PARAMEQ, 200 + i) for i in range(len(_BANDS))]
            eng._fx170 = handles
            eng._fx170_st = st
        for h, (f0, g, bw) in zip(handles, _BANDS):
            if h:
                b.BASS_FXSetParameters(h, ctypes.byref(_PEQ(f0, bw, g)))
        print('[XL170] EQ X-Light pulita applicata (5 bande DX8, no exciter)')
    except Exception as e:
        print('[XL170] errore:', e)


def apply():
    if _spenta():
        return False
    try:
        from moduli.database import Database
        Database.set_config('patch_167', '0')     # niente exciter (sporca)
        Database.set_config('patch_157', '0')     # niente auto-tono (doppio EQ)
        Database.set_config('patch_159', '1')     # auto-volume ok
        Database.set_config('patch_110', '0')     # STOP Timbres: il banco e' core.kdl
        # neutralizzo bright/bass della 109 per non sommarli alla 170
        Database.set_config('exp_sw_bright', '50')
        Database.set_config('exp_sw_bass', '50')
        # il banco DEVE essere core.kdl (la 110 lo dirottava su Timbres)
        _def = Database.get_config('exp_banco_default', '') or ''
        import os as _os
        if _def and _os.path.isfile(_def):
            Database.set_config('exp_banco_path', _def)
        if str(Database.get_config('exp_sw_reverb', '')) in ('', '20', '25'):
            Database.set_config('exp_sw_reverb', '30')   # un po' di spazio X-Light
    except Exception:
        pass
    try:
        import moduli.bass_engine as BE
    except Exception:
        return False
    Eng = getattr(BE, 'BassEngine', None)
    if Eng is None or getattr(Eng, '_xl170', False):
        return True
    _orig = Eng.load

    def load(self, *a, **k):
        r = _orig(self, *a, **k)
        try:
            if r and getattr(self, 'is_midi', False) and _is_software():
                self._fx170 = None      # lo stream e' nuovo
                _applica(self)
        except Exception as e:
            print('[XL170] hook:', e)
        return r
    Eng.load = load
    Eng._xl170 = True
    print('[XL170] expander X-Light PULITO pronto (5 bande, no exciter)')
    return True


try:
    apply()
except Exception as _e:
    print('patch 170: %s' % _e)
