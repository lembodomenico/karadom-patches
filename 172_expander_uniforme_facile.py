import tkinter as tk


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_172', '1')) == '0'
    except Exception:
        return False


def _ingrandisci_radio(root):
    """Allarga l'area cliccabile dei Radiobutton della finestra expander:
    font piu' grande + piu' spazio verticale, e fill='x' SOLO se il radio e'
    da solo nella sua riga (niente bottone accanto), per non rompere il layout."""
    try:
        for w in root.winfo_children():
            try:
                if isinstance(w, tk.Radiobutton):
                    w.config(font=('Segoe UI', 13, 'bold'), anchor='w', padx=10, pady=4)
                    try:
                        fratelli = w.master.winfo_children()
                        da_solo = all((c is w) or not isinstance(c, (tk.Button,)) for c in fratelli)
                        if da_solo:
                            w.pack_configure(fill='x', ipady=8, pady=3)
                        else:
                            w.pack_configure(ipady=8, padx=6)
                    except Exception:
                        pass
            except Exception:
                pass
            _ingrandisci_radio(w)
    except Exception:
        pass


def apply():
    if _spenta():
        return False
    # 1) UNIFORMA: slot default = "Expander Software" (non "SF2 mio")
    try:
        from moduli.database import Database
        Database.set_config('exp_slot', 'default')
    except Exception:
        pass
    # 2) RADIO PIU' FACILI DA SELEZIONARE
    try:
        import moduli.expander_gui as EG
    except Exception:
        return False
    F = getattr(EG, 'FinestraExpander', None)
    if F is None or getattr(F, '_easy172', False):
        return True
    _orig = getattr(F, '_costruisci', None)
    if _orig is None:
        return True

    def _costruisci(self, *a, **k):
        r = _orig(self, *a, **k)
        try:
            root = self if hasattr(self, 'winfo_children') else getattr(self, 'win', None)
            if root is not None:
                root.after(60, lambda: _ingrandisci_radio(root))
        except Exception as e:
            print('[EXP172] costruisci:', e)
        return r
    F._costruisci = _costruisci
    F._easy172 = True
    print('[EXP172] expander uniforme (slot default) + radio piu\' grandi')
    return True


try:
    apply()
except Exception as _e:
    print('patch 172: %s' % _e)
