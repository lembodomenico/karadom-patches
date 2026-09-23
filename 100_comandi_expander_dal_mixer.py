# 100 - Pannello Expander: bottone che apre la finestra dei comandi dell'expander software (che gira nel tray)
def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_100', '1')) == '0'
    except Exception:
        return False


def apply():
    if _spenta():
        return False
    import sys, os
    # solo se l'expander SOFTWARE e' installato (altrimenti il bottone non serve)
    _exe = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'KaraDom', 'dipendenze',
                        'Expander', 'KaraDom Expander.exe')
    if not os.path.exists(_exe):
        return False
    eg = sys.modules.get('moduli.expander_gui')
    if eg is None:
        try:
            import moduli.expander_gui as eg  # noqa
        except Exception:
            print('patch 100: expander_gui non presente (ok)')
            return False
    F = getattr(eg, 'FinestraExpander', None)
    if F is None or getattr(F, '_comandi_100', False):
        return True

    _orig = F._costruisci

    def _apri_comandi():
        base = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'KaraDom', 'dipendenze', 'Expander')
        try:
            os.makedirs(base, exist_ok=True)
            with open(os.path.join(base, 'apri_comandi.flag'), 'w') as f:
                f.write('1')
            print('[EXP] richiesta apertura finestra comandi expander')
        except Exception as e:
            print('[EXP] flag comandi:', e)

    def _fix_testi(w):
        import tkinter as tk
        for c in w.winfo_children():
            try:
                if isinstance(c, tk.Label):
                    t = c.cget('text')
                    if ('brano successivo' in t) or ('prossimo brano' in t) or ('brano MIDI' in t):
                        c.config(text="Le modifiche si applicano SUBITO, anche a brano in corso.\n"
                                      "L'audio esce dalle uscite dell'expander.")
            except Exception:
                pass
            try:
                _fix_testi(c)
            except Exception:
                pass

    def _costruisci(self):
        _orig(self)
        try:
            _fix_testi(self.win)
        except Exception:
            pass
        try:
            import tkinter as tk
            try:
                from moduli.ui_scale import S, F as _FN
                font = _FN('Arial', 9, 'bold'); ipady = S(4); mx = S(14); my = S(10)
            except Exception:
                font = ('Arial', 9, 'bold'); ipady = 4; mx = 14; my = 10
            tk.Button(self.win, text="🎚 Comandi expander (volume, riverbero, larghezza…)",
                      command=_apri_comandi, bg='#0d6efd', fg='white', font=font,
                      relief='flat', bd=0, cursor='hand2', pady=ipady).pack(
                          fill='x', padx=mx, pady=(0, my))
        except Exception as e:
            print('patch 100 costruisci:', e)

    F._costruisci = _costruisci
    F._costruisci_orig_100 = _orig
    F._comandi_100 = True
    print('[EXP] patch 100: bottone "Comandi expander" nel pannello Expander')
    return True


def revert():
    try:
        import sys
        eg = sys.modules.get('moduli.expander_gui')
        F = getattr(eg, 'FinestraExpander', None) if eg else None
        if F is not None and getattr(F, '_comandi_100', False):
            if hasattr(F, '_costruisci_orig_100'):
                F._costruisci = F._costruisci_orig_100
            del F._comandi_100
    except Exception:
        pass


try:
    apply()
except Exception as _e:
    print('patch 100: %s' % _e)
