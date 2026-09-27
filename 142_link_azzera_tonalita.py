import tkinter as tk


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_142', '1')) == '0'
    except Exception:
        return False


def _azzera_ton_se_link(self):
    try:
        t = self.entry_filtro.get().strip().lower()
        if ('youtu.be/' in t or 'youtube.com/' in t
                or t.startswith('http://') or t.startswith('https://')):
            self.entry_ton.delete(0, tk.END)
            self.entry_ton.insert(0, "0")
            self.entry_ton.config(fg='white')
    except Exception:
        pass


def apply():
    if _spenta():
        return False
    try:
        import moduli.libreria as lib
        C = getattr(lib, 'LibreriaSlider', None)
        if C is None or getattr(C, '_linkton142', False):
            return True
        C._azzera_ton_se_link = _azzera_ton_se_link
        _orig = C._debounce_suggerimenti

        def _wrap(self, event=None):
            # aggancia una volta anche il tasto destro -> Incolla
            try:
                if not getattr(self, '_linkton142_paste', False):
                    self.entry_filtro.bind('<<Paste>>',
                        lambda e: self.parent.after(1, self._azzera_ton_se_link), add='+')
                    self._linkton142_paste = True
            except Exception:
                pass
            try:
                self._azzera_ton_se_link()
            except Exception:
                pass
            return _orig(self, event)

        C._debounce_suggerimenti = _wrap
        C._linkton142 = True
        print('[LINKTON142] link nel filtro -> tonalita a 0')
    except Exception as e:
        print('[LINKTON142] hook:', e)
    return True


def revert():
    pass


try:
    apply()
except Exception as _e:
    print('patch 142: %s' % _e)
