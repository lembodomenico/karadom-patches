import tkinter as tk


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_175', '1')) == '0'
    except Exception:
        return False


def _ingrandisci(root):
    # SOLO font piu' grande sui Radiobutton -> area cliccabile piu' ampia.
    # NIENTE pack_configure / fill / variable: non puo' rompere la selezione.
    try:
        for w in root.winfo_children():
            try:
                if isinstance(w, tk.Radiobutton):
                    w.config(font=('Segoe UI', 13, 'bold'))
            except Exception:
                pass
            _ingrandisci(w)
    except Exception:
        pass


def apply():
    if _spenta():
        return False
    try:
        import moduli.expander_gui as EG
    except Exception:
        return False
    F = getattr(EG, 'FinestraExpander', None)
    if F is None or getattr(F, '_big175', False):
        return True
    _orig = getattr(F, '_costruisci', None)
    if _orig is None:
        return True

    def _costruisci(self, *a, **k):
        r = _orig(self, *a, **k)
        try:
            root = self if hasattr(self, 'winfo_children') else getattr(self, 'win', None)
            if root is not None:
                root.after(80, lambda: _ingrandisci(root))
        except Exception as e:
            print('[EXP175]', e)
        return r
    F._costruisci = _costruisci
    F._big175 = True
    print('[EXP175] radio expander piu\' grandi (solo font)')
    return True


try:
    apply()
except Exception as _e:
    print('patch 175: %s' % _e)
