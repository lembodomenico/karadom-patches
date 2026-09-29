import os
import threading
import ctypes


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_162', '1')) == '0'
    except Exception:
        return False


def _limite_mb():
    try:
        from moduli.database import Database
        return float(Database.get_config('ram_banco_max_mb', '3000'))
    except Exception:
        return 3000.0


_CARICATI = set()


def _carica_tutto(font, path):
    try:
        import moduli.bass_engine as BE
        m = BE._lib.bassmidi
        if not m or not font or font in _CARICATI:
            return
        mb = os.path.getsize(path) / 1048576.0 if path and os.path.exists(path) else 0
        if mb > _limite_mb():
            print('[RAM162] banco %.0f MB oltre il limite: resta su disco' % mb)
            return
        try:
            class _MS(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_uint32), ("dwMemoryLoad", ctypes.c_uint32),
                            ("ullTotalPhys", ctypes.c_uint64), ("ullAvailPhys", ctypes.c_uint64),
                            ("ullTotalPageFile", ctypes.c_uint64), ("ullAvailPageFile", ctypes.c_uint64),
                            ("ullTotalVirtual", ctypes.c_uint64), ("ullAvailVirtual", ctypes.c_uint64),
                            ("ullAvailExtendedVirtual", ctypes.c_uint64)]
            ms = _MS(); ms.dwLength = ctypes.sizeof(_MS)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(ms))
            libera = ms.ullAvailPhys / 1048576.0
            if libera < mb + 2048:
                print('[RAM162] RAM libera %.0f MB: poca per %.0f MB di banco, resta su disco' % (libera, mb))
                return
        except Exception:
            pass
        _CARICATI.add(font)
        m.BASS_MIDI_FontLoad.restype = ctypes.c_bool
        m.BASS_MIDI_FontLoad.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_int]
        ok = m.BASS_MIDI_FontLoad(font, -1, -1)
        print('[RAM162] banco caricato tutto in RAM (%.0f MB): %s' % (mb, ok))
    except Exception as e:
        print('[RAM162] errore:', e)


def apply():
    if _spenta():
        return False
    try:
        import moduli.bass_engine as BE
    except Exception as e:
        print('[RAM162] bass_engine assente:', e)
        return False
    Eng = getattr(BE, 'BassEngine', None)
    if Eng is None or getattr(Eng, '_ram162', False):
        return True
    _orig = Eng._load_soundfont

    def _load_soundfont(self, sf_path):
        ok = _orig(self, sf_path)
        try:
            if ok and not _spenta():
                threading.Thread(target=_carica_tutto, args=(getattr(self, '_font', 0), str(sf_path)),
                                 name='ram_162', daemon=True).start()
        except Exception as e:
            print('[RAM162] hook:', e)
        return ok

    Eng._load_soundfont = _load_soundfont
    Eng._ram162 = True
    try:
        eng = BE.get_bass_engine() if hasattr(BE, 'get_bass_engine') else None
        if eng is not None and getattr(eng, '_font', 0):
            threading.Thread(target=_carica_tutto, args=(eng._font, getattr(eng, '_soundfont_path', '')),
                             name='ram_162', daemon=True).start()
    except Exception:
        pass
    return True


def revert():
    pass


try:
    apply()
except Exception as _e:
    print('patch 162: %s' % _e)
