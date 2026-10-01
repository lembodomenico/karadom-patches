import ctypes

DWORD = ctypes.c_uint32


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_176', '1')) == '0'
    except Exception:
        return False


def apply():
    if _spenta():
        return False
    try:
        import moduli.bass_engine as BE
    except Exception:
        return False
    Eng = getattr(BE, 'BassEngine', None)
    if Eng is None or not hasattr(Eng, '_load_soundfont') or getattr(Eng, '_freefont176', False):
        return True
    _orig = Eng._load_soundfont

    def _load_soundfont(self, sf_path):
        old = getattr(self, '_font', 0)
        r = _orig(self, sf_path)
        # dopo il load il NUOVO font e' gia' applicato allo stream: il vecchio non
        # serve piu'. Lo libero -> niente leak di handle ne' banco ricaricato in RAM
        # ad ogni switch (era la causa dell'inceppamento dopo 2-3 cambi sorgente).
        try:
            new = getattr(self, '_font', 0)
            if r and old and new and old != new:
                m = BE._lib.bassmidi
                m.BASS_MIDI_FontFree.restype = ctypes.c_bool
                m.BASS_MIDI_FontFree.argtypes = [DWORD]
                m.BASS_MIDI_FontFree(old)
        except Exception as e:
            print('[FONT176] free:', e)
        return r
    Eng._load_soundfont = _load_soundfont
    Eng._freefont176 = True
    print('[FONT176] libero il font vecchio ad ogni cambio (stop leak/saturazione)')
    return True


try:
    apply()
except Exception as _e:
    print('patch 176: %s' % _e)
