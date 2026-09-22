# 092 - opzione: sincronizza le liste
def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_092', '1')) == '0'
    except Exception:
        return False


def apply():
    if _spenta():
        return False
    try:
        import moduli.opzioni as op
        import tkinter as tk
        from tkinter import ttk
    except Exception:
        return False
    if getattr(op.OpzioniWindow, '_syncopt092', False):
        return True

    _orig = op.OpzioniWindow.__init__

    def __init__(self, *a, **k):
        _orig(self, *a, **k)
        try:
            from moduli.licensing import richieste_abilitate
            if not richieste_abilitate():
                return
        except Exception:
            return
        try:
            win = getattr(self, 'window', None)
            if win is None:
                return
            # trova il Notebook
            trovato = {'nb': None}

            def cerca(w):
                if trovato['nb'] is not None:
                    return
                for c in w.winfo_children():
                    if isinstance(c, ttk.Notebook):
                        trovato['nb'] = c
                        return
                    cerca(c)
                    if trovato['nb'] is not None:
                        return
            cerca(win)
            nb = trovato['nb']
            if nb is None:
                return
            # trova la scheda Playlist
            tab_frame = None
            for tid in nb.tabs():
                try:
                    if 'Playlist' in nb.tab(tid, 'text'):
                        tab_frame = win.nametowidget(tid)
                        break
                except Exception:
                    pass
            if tab_frame is None:
                return
            # gia' presente? (source ricompilato che ce l'ha) -> non doppiare
            if getattr(self, 'sync_liste_var', None) is not None:
                return

            from moduli.database import Database
            try:
                from moduli.ui_scale import S, F
            except Exception:
                def S(x): return x
                def F(f, s, *w): return (f, s)
            try:
                from moduli.i18n import _
            except Exception:
                def _(s): return s

            self.sync_liste_var = tk.BooleanVar(
                value=(Database.get_config('sync_liste_attiva', '1') == '1'))

            def _salva():
                try:
                    at = bool(self.sync_liste_var.get())
                    Database.set_config('sync_liste_attiva', '1' if at else '0')
                    if at:
                        fn = getattr(Database, '_sync_liste_push', None)
                        if fn:
                            fn(subito=True)
                        else:
                            try:
                                from moduli.sync_liste import sincronizza
                                sincronizza(subito=True)
                            except Exception:
                                pass
                except Exception as e:
                    print(f"[sync liste] opzione: {e}")

            box = tk.Frame(tab_frame, bg='#2d0a3f')
            # in CIMA alla scheda (la Playlist è lunga: in fondo restava tagliata)
            _kids = [w for w in tab_frame.winfo_children() if w is not box]
            if _kids:
                box.pack(fill='x', padx=S(20), pady=S(8), before=_kids[0])
            else:
                box.pack(fill='x', padx=S(20), pady=S(8))
            tk.Label(box, text=_("SINCRONIZZAZIONE SUL SERVER"), bg='#2d0a3f',
                     fg='white', font=F('Arial', 13, 'bold')).pack(anchor='w')
            tk.Label(box, text=_("Tiene preferiti e playlist allineati sul server."),
                     bg='#2d0a3f', fg='#888888', font=F('Arial', 9)).pack(anchor='w')
            tk.Checkbutton(box, text=_("Sincronizza preferiti e playlist sul server"),
                           variable=self.sync_liste_var, command=_salva,
                           bg='#2d0a3f', fg='white', selectcolor='#28a745',
                           activebackground='#2d0a3f', activeforeground='white',
                           font=F('Arial', 12, 'bold')).pack(anchor='w', pady=S(4))
        except Exception as e:
            print(f"[sync liste] opzioni UI: {e}")

    op.OpzioniWindow.__init__ = __init__
    op.OpzioniWindow._syncopt092 = True
    return True


def revert():
    return False


try:
    apply()
except Exception:
    pass
