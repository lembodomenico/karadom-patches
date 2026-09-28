def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_152', '1')) == '0'
    except Exception:
        return False


def apply():
    if _spenta():
        return False
    try:
        import moduli.expander_gui as EG
    except Exception as e:
        print('[H152] expander_gui assente:', e); return False
    F = getattr(EG, 'FinestraExpander', None)
    if F is None or not hasattr(F, '_costruisci') or getattr(F, '_fixh152', False):
        return True
    _o = F._costruisci

    def _c(self):
        r = _o(self)
        # etichetta di stato ad altezza FISSA (2 righe) -> la finestra non si accorcia
        try:
            self.lbl_stato.config(height=2)
        except Exception as e:
            print('[H152] lbl_stato:', e)
        # blocca anche l'altezza minima della finestra al valore a regime
        try:
            def _lock(s=self):
                try:
                    s.win.update_idletasks()
                    w = max(s.win.winfo_width(), s.win.winfo_reqwidth())
                    h = max(s.win.winfo_height(), s.win.winfo_reqheight())
                    s.win.minsize(w, h)
                except Exception:
                    pass
            self.win.after(200, _lock)
        except Exception:
            pass
        return r

    F._costruisci = _c
    F._fixh152 = True
    print('[H152] finestra expander: altezza fissa (stato 2 righe)')
    return True


def revert():
    pass


try:
    apply()
except Exception as _e:
    print('patch 152: %s' % _e)
