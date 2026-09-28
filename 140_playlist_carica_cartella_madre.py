import os


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_140', '1')) == '0'
    except Exception:
        return False


def apply():
    if _spenta():
        return False
    try:
        import moduli.libreria as lib
        C = getattr(lib, 'LibreriaSlider', None)
        if C is None or getattr(C, '_plmadre140', False):
            return True
        _orig = C.on_playlist_select

        def _wrap(self, event=None):
            r = _orig(self, event)
            try:
                brani = getattr(self, 'brani_playlist_correnti', None) or []
                dirs = []
                for b in brani:
                    p = b.get('path', '') if isinstance(b, dict) else ''
                    if p:
                        d = os.path.dirname(p)
                        if d:
                            dirs.append(d)
                if dirs:
                    try:
                        madre = os.path.commonpath(dirs)
                    except Exception:
                        madre = dirs[0]
                    if madre and os.path.isdir(madre):
                        self.percorso_attivo = madre
                        self.carica_brani(madre)
                        print('[PLMADRE140] playlist -> cartella madre %s' % madre)
            except Exception as e:
                print('[PLMADRE140] wrap:', e)
            return r

        C.on_playlist_select = _wrap
        C._plmadre140 = True
        print('[PLMADRE140] selezionando una playlist carico la cartella madre (come un preferito)')
    except Exception as e:
        print('[PLMADRE140] hook:', e)
    return True


def revert():
    pass


try:
    apply()
except Exception as _e:
    print('patch 140: %s' % _e)
