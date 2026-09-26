def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_130', '1')) == '0'
    except Exception:
        return False


def apply():
    if _spenta():
        return False
    try:
        import tkinter as tk
        import moduli.libreria as lib
        C = getattr(lib, 'LibreriaSlider', None)
        if C is None or getattr(C, '_cestino_ton130', False):
            return True
        _orig = C.svuota_campo_filtro

        def _svuota(self):
            r = _orig(self)
            try:
                self.entry_ton.delete(0, tk.END)
                self.entry_ton.insert(0, "0")
                self.entry_ton.config(fg='white')
            except Exception:
                pass
            return r

        C.svuota_campo_filtro = _svuota
        C._cestino_ton130 = True
        print('[TON130] cestino filtro azzera anche la tonalita')
    except Exception as e:
        print('[TON130] hook:', e)
    return True


def revert():
    pass


try:
    apply()
except Exception as _e:
    print('patch 130: %s' % _e)
