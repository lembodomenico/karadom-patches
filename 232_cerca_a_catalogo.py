# 232 - menu contestuale: "Cerca a catalogo" (brano o artista; artista = tutto il suo catalogo)
# [21-10-2026] utente: "in KaraDom sul menu contestuale mettimi una voce 'Cerca a catalogo' dove mi mostri
# un campo da digitare che sia un brano o un artista e nel caso dell'artista mi mostrerai il catalogo
# filtrato; questa funzione ce l'avra' solo chi ha le richieste remote attivate".
# Il catalogo e' quello sul server (brani_memorizzati2 del gestore): catalogo_api.php action 'cerca'
# (entra solo con una licenza che ha le richieste remote).

_VER = 1


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_232', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def _abilitata():
    """Solo chi ha le richieste remote (stesso controllo della campanella)."""
    try:
        from moduli.requests_api_client import richieste_abilitate
        return bool(richieste_abilitate())
    except Exception:
        return False


_finestra = [None]


def _apri(parent):
    import threading
    import tkinter as tk
    from tkinter import ttk

    w = _finestra[0]
    try:
        if w is not None and w.winfo_exists():
            w.deiconify(); w.lift(); w.focus_force()
            return
    except Exception:
        pass

    win = tk.Toplevel(parent)
    _finestra[0] = win
    win.title('Cerca a catalogo')
    win.configure(bg='#1a1a2e')
    win.geometry('720x560')
    win.minsize(480, 320)
    try:
        win.transient(parent)
        win.attributes('-topmost', True)
        win.after(400, lambda: win.attributes('-topmost', False))
    except Exception:
        pass

    tk.Label(win, text='Scrivi un brano o un artista', bg='#1a1a2e', fg='#ffd700',
             font=('Segoe UI', 13, 'bold')).pack(padx=14, pady=(12, 4), anchor='w')
    var = tk.StringVar()
    ent = tk.Entry(win, textvariable=var, font=('Segoe UI', 15, 'bold'), bg='#000000', fg='white',
                   insertbackground='white', relief='solid', bd=1)
    ent.pack(padx=14, pady=4, fill='x', ipady=6)
    stato = tk.Label(win, text='', bg='#1a1a2e', fg='#cccccc', font=('Segoe UI', 11), anchor='w')
    stato.pack(padx=14, pady=(2, 4), fill='x')

    cornice = tk.Frame(win, bg='#1a1a2e')
    cornice.pack(padx=14, pady=(0, 12), fill='both', expand=True)
    try:
        st = ttk.Style()
        st.configure('Cat232.Treeview', background='#0a0a0a', foreground='white', fieldbackground='#0a0a0a',
                     font=('Segoe UI', 12), rowheight=26)
        st.configure('Cat232.Treeview.Heading', font=('Segoe UI', 12, 'bold'))
        st.map('Cat232.Treeview', background=[('selected', '#00d4ff')], foreground=[('selected', 'black')])
    except Exception:
        pass
    tv = ttk.Treeview(cornice, columns=('artista', 'titolo'), show='headings', style='Cat232.Treeview')
    tv.heading('artista', text='Artista')
    tv.heading('titolo', text='Titolo')
    tv.column('artista', width=240, anchor='w')
    tv.column('titolo', width=420, anchor='w')
    sb = ttk.Scrollbar(cornice, orient='vertical', command=tv.yview)
    tv.configure(yscrollcommand=sb.set)
    sb.pack(side='right', fill='y')
    tv.pack(side='left', fill='both', expand=True)

    giro = {'n': 0, 'timer': None}

    def mostra(n, esito, errore=None):
        if n != giro['n'] or not win.winfo_exists():
            return                                   # e' arrivata la risposta di una ricerca vecchia
        tv.delete(*tv.get_children())
        if errore:
            stato.config(text='Errore: %s' % errore, fg='#ff6b6b')
            return
        brani = esito.get('brani') or []
        for b in brani:
            tv.insert('', 'end', values=(b.get('artista', ''), b.get('titolo', '')))
        if not brani:
            stato.config(text='Nessun brano trovato nel catalogo', fg='#cccccc')
        elif esito.get('artista'):
            stato.config(text='Catalogo di %s: %d brani' % (brani[0].get('artista', ''), len(brani)), fg='#7CFC00')
        else:
            stato.config(text='%d brani trovati' % len(brani), fg='#cccccc')

    def cerca():
        q = var.get().strip()
        giro['n'] += 1
        n = giro['n']
        if len(q) < 2:
            tv.delete(*tv.get_children())
            stato.config(text='', fg='#cccccc')
            return
        stato.config(text='Cerco…', fg='#cccccc')

        # la risposta arriva in un thread: la si lascia in 'giro' e la finestra la raccoglie
        # dal proprio thread (Tk non va toccato da altri thread)
        def lavora():
            try:
                from moduli.catalogo_remoto import _chiedi
                giro['risposta'] = (n, _chiedi('cerca', q=q), None)
            except Exception as e:
                giro['risposta'] = (n, {}, str(e))
        threading.Thread(target=lavora, daemon=True).start()

        def raccogli():
            if not win.winfo_exists():
                return
            r = giro.pop('risposta', None)
            if r is None:
                if n == giro['n']:
                    win.after(80, raccogli)
                return
            mostra(*r)
        win.after(80, raccogli)

    def scrivendo(*_a):
        if giro['timer']:
            try:
                win.after_cancel(giro['timer'])
            except Exception:
                pass
        giro['timer'] = win.after(350, cerca)

    var.trace_add('write', scrivendo)

    def copia(_e=None):
        sel = tv.selection()
        if not sel:
            return
        a, t = tv.item(sel[0], 'values')
        try:
            win.clipboard_clear(); win.clipboard_append('%s - %s' % (a, t))
            stato.config(text='Copiato: %s - %s' % (a, t), fg='#7CFC00')
        except Exception:
            pass
    tv.bind('<Double-Button-1>', copia)
    win.bind('<Escape>', lambda e: win.destroy())
    win.update_idletasks()
    win.lift()
    ent.focus_force()


def apply():
    if _spenta():
        return False
    try:
        import tkinter as tk
        if getattr(tk.Menu, '_ver232', None) == _VER:
            return True
        prima = getattr(tk.Menu, '_o232_add_command', None) or tk.Menu.add_command
        tk.Menu._o232_add_command = prima

        def add_command(self, cnf=None, **kw):
            esito = prima(self, cnf, **kw) if cnf is not None else prima(self, **kw)
            try:
                lab = str(kw.get('label') or '')
                # accanto a "Richieste Remote" (lo stesso menu in cui la 231 mette "Entra come cliente")
                if 'Remot' in lab and not getattr(self, '_cat232', False) and _abilitata():
                    self._cat232 = True
                    prima(self, label='Cerca a catalogo...',
                          command=lambda w=self: _apri(getattr(tk, '_default_root', None) or w.master))
            except Exception as e:
                print('[232] menu: %s' % e)
            return esito
        tk.Menu.add_command = add_command
        tk.Menu._ver232 = _VER
        print('[232] "Cerca a catalogo" nel menu (solo con le richieste remote)')
        return True
    except Exception as e:
        print('[232] %s' % e)
        return False


def revert():
    try:
        import tkinter as tk
        if getattr(tk.Menu, '_o232_add_command', None):
            tk.Menu.add_command = tk.Menu._o232_add_command
            tk.Menu._ver232 = None
    except Exception:
        pass
