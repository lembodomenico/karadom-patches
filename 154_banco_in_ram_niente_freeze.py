import ctypes
import threading


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_154', '1')) == '0'
    except Exception:
        return False


def apply():
    if _spenta():
        return False
    try:
        import moduli.bass_engine as BE
    except Exception as e:
        print('[BANK154] bass_engine assente:', e)
        return False

    Eng = getattr(BE, 'BassEngine', None)
    if Eng is None or getattr(Eng, '_bank154', False):
        return True

    FONT = BE.BASS_MIDI_FONT
    DWORD = BE.DWORD

    def _apply_soundfont_to_stream(self):
        if not self._font or not self._stream or not BE._lib.bassmidi:
            return False
        m = BE._lib.bassmidi
        m.BASS_MIDI_StreamSetFonts.restype = ctypes.c_bool
        m.BASS_MIDI_StreamSetFonts.argtypes = [DWORD, ctypes.c_void_p, DWORD]
        fc = FONT(font=self._font, preset=-1, bank=0)
        ok = m.BASS_MIDI_StreamSetFonts(self._stream, ctypes.byref(fc), 1)
        if ok:
            _stream = self._stream

            def _carica():
                try:
                    m.BASS_MIDI_StreamLoadSamples.restype = ctypes.c_bool
                    m.BASS_MIDI_StreamLoadSamples.argtypes = [DWORD]
                    m.BASS_MIDI_StreamLoadSamples(_stream)
                except Exception:
                    pass

            try:
                threading.Thread(target=_carica, name='load_samples_154', daemon=True).start()
            except Exception:
                _carica()
        return ok

    Eng._apply_soundfont_to_stream = _apply_soundfont_to_stream
    Eng._bank154 = True
    print('[BANK154] StreamLoadSamples spostato su thread di fondo: niente freeze UI col banco su disco')
    return True


def revert():
    pass


try:
    apply()
except Exception as _e:
    print('patch 154: %s' % _e)
