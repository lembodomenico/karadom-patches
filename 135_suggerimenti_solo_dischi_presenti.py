import os


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_135', '1')) == '0'
    except Exception:
        return False


def _dischi_montati():
    # set delle lettere di unita' montate ORA (istantaneo, niente I/O)
    try:
        import ctypes
        mask = ctypes.windll.kernel32.GetLogicalDrives()
        return set(chr(ord('A') + i) for i in range(26) if mask & (1 << i))
    except Exception:
        return None  # in dubbio: non filtrare


def _tieni(b, montati):
    # tieni: brani "virtuali" (nel DB, senza file locale) e quelli su disco montato/rete;
    # scarta SOLO quelli con un percorso su un'unita' NON montata.
    try:
        if b.get('_virtuale'):
            return True
        p = b.get('path', '')
        if not p:
            return True
        d = os.path.splitdrive(os.path.abspath(p))[0]  # "D:"
        if not d or len(d) < 2 or d[1] != ':':
            return True  # UNC/rete: non escludere
        letter = d[0].upper()
        if montati is None:
            return True
        return letter in montati
    except Exception:
        return True


def apply():
    if _spenta():
        return False
    try:
        import moduli.libreria as lib
        C = getattr(lib, 'LibreriaSlider', None)
        if C is None or getattr(C, '_sugg135', False):
            return True
        _orig = C._mostra_risultati_filtro

        def _wrap(self, finali):
            try:
                montati = _dischi_montati()
                finali = [b for b in (finali or []) if _tieni(b, montati)]
            except Exception as e:
                print('[SUGG135] filtro:', e)
            return _orig(self, finali)

        C._mostra_risultati_filtro = _wrap
        C._sugg135 = True
        print('[SUGG135] suggerimenti: esclusi i brani su dischi non montati')
    except Exception as e:
        print('[SUGG135] hook:', e)
    return True


def revert():
    pass


try:
    apply()
except Exception as _e:
    print('patch 135: %s' % _e)
