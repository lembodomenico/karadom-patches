import ctypes

DWORD = ctypes.c_uint32
BASS_ATTRIB_MIDI_VOICES        = 0x12003   # tetto voci PER-STREAM (non globale)
BASS_ATTRIB_MIDI_VOICES_ACTIVE = 0x12004   # voci attive ORA (sola lettura)


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_124', '1')) == '0'
    except Exception:
        return False


def _voci():
    try:
        from moduli.database import Database
        v = Database.get_config('exp_sw_voices', '512')
        return max(64, min(2000, int(float(v))))
    except Exception:
        return 512


def _applica_voci(eng):
    # SOLO expander software: mai HW (winmm), mai riproduzione interna normale.
    if not getattr(eng, '_exp_soft_active', False):
        return
    if not getattr(eng, 'is_midi', False):
        return
    st = getattr(eng, '_stream', 0)
    if not st:
        return
    try:
        import moduli.bass_engine as be
        b = getattr(getattr(be, '_lib', None), 'bass', None)
    except Exception:
        return
    if not b:
        return
    try:
        b.BASS_ChannelSetAttribute.argtypes = [DWORD, DWORD, ctypes.c_float]
        b.BASS_ChannelGetAttribute.argtypes = [DWORD, DWORD, ctypes.POINTER(ctypes.c_float)]
    except Exception:
        pass
    n = _voci()
    try:
        ok = b.BASS_ChannelSetAttribute(st, BASS_ATTRIB_MIDI_VOICES, ctypes.c_float(float(n)))
        cur = ctypes.c_float(0.0)
        try:
            b.BASS_ChannelGetAttribute(st, BASS_ATTRIB_MIDI_VOICES, ctypes.byref(cur))
        except Exception:
            pass
        print('[POLY124] expander software: tetto voci=%d set=%s (letto=%.0f)' % (n, ok, cur.value))
    except Exception as e:
        print('[POLY124] errore set voci:', e)


def apply():
    if _spenta():
        return False
    import sys
    be = sys.modules.get('moduli.bass_engine')
    if be is None:
        try:
            import moduli.bass_engine as be  # noqa
        except Exception:
            print('[POLY124] bass_engine non presente (ok)')
            return False
    BE = getattr(be, 'BassEngine', None)
    if BE is None or getattr(BE, '_poly124', False):
        return True

    _oload = BE.load

    def _load(self, *a, **k):
        r = _oload(self, *a, **k)
        try:
            if r:
                _applica_voci(self)
        except Exception as e:
            print('[POLY124] post-load:', e)
        return r

    BE.load = _load
    BE._poly124 = True

    # se c'e' gia' un motore software attivo con un brano in corso, applico subito
    try:
        from moduli.bass_engine import get_bass_engine
        _applica_voci(get_bass_engine())
    except Exception:
        pass

    print('[POLY124] polifonia alta SOLO su expander software (HW e riproduzione interna intatti)')
    return True


def revert():
    pass


try:
    apply()
except Exception as _e:
    print('patch 124: %s' % _e)
