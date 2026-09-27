# 094 - importazione winlive in finestra dedicata
def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_094', '1')) == '0'
    except Exception:
        return False


def apply():
    if _spenta():
        return False
    try:
        import moduli.opzioni as op
        import tkinter as tk
        from moduli.database import Database
    except Exception:
        return False
    try:
        from moduli.ui_scale import S, F
    except Exception:
        def S(x):
            return x

        def F(f, s, *w):
            return (f, s) + tuple(w)
    try:
        from moduli.i18n import _
    except Exception:
        def _(s):
            return s

    if getattr(op.OpzioniWindow, '_winlive094', False):
        return True

    def create_tab_playlist(self, notebook):
        tab = tk.Frame(notebook, bg='#2d0a3f')
        notebook.add(tab, text=_("📋 Playlist"))

        COLW = S(560)
        wrap = tk.Frame(tab, bg='#2d0a3f')
        wrap.pack(fill='both', expand=True)
        col = tk.Frame(wrap, bg='#2d0a3f')
        col.pack(expand=True, padx=S(20))
        tk.Frame(col, bg='#2d0a3f', width=COLW, height=1).pack()

        def _card():
            c = tk.Frame(col, bg='#3a1550', highlightbackground='#4a2d63', highlightthickness=1)
            c.pack(fill='x', pady=S(9))
            inner = tk.Frame(c, bg='#3a1550')
            inner.pack(fill='x', padx=S(20), pady=S(16))
            return inner

        try:
            from moduli.licensing import richieste_abilitate as _rich_ab
            _sync_ok = bool(_rich_ab())
        except Exception:
            _sync_ok = False
        if _sync_ok:
            self.sync_liste_var = tk.BooleanVar(
                value=(Database.get_config('sync_liste_attiva', '1') == '1'))

            def _salva_sync():
                try:
                    at = bool(self.sync_liste_var.get())
                    Database.set_config('sync_liste_attiva', '1' if at else '0')
                    if at:
                        fn = getattr(Database, '_sync_liste_push', None)
                        if fn:
                            fn(subito=True)
                except Exception as e:
                    print(f"[winlive094] salva sync: {e}")

            def _scarica_sync():
                fn = getattr(Database, '_sync_liste_pull', None)
                ok = False
                if fn:
                    try:
                        ok = fn()
                    except Exception as e:
                        print(f"[winlive094] scarica: {e}")
                try:
                    from tkinter import messagebox
                    if ok:
                        messagebox.showinfo(_("Sincronizzazione"),
                                            _("Scaricati dal server.\nRiapri la finestra playlist per vederli."),
                                            parent=self.window)
                    else:
                        messagebox.showwarning(_("Sincronizzazione"),
                                               _("Niente da scaricare (o richieste remote non attive)."),
                                               parent=self.window)
                except Exception:
                    pass

            s = _card()
            tk.Label(s, text=_("Sincronizzazione sul server"), bg='#3a1550', fg='white',
                     font=F('Arial', 13, 'bold')).pack(anchor='w')
            tk.Label(s, text=_("Tiene preferiti e playlist allineati sul server (richieste remote)."),
                     bg='#3a1550', fg='#e8dff2', font=F('Arial', 9), justify='left').pack(anchor='w', pady=(S(2), S(10)))
            tk.Checkbutton(s, text=_("Sincronizza preferiti e playlist sul server"),
                           variable=self.sync_liste_var, command=_salva_sync,
                           bg='#3a1550', fg='white', selectcolor='#28a745',
                           activebackground='#3a1550', activeforeground='white',
                           font=F('Arial', 11, 'bold')).pack(anchor='w')
            tk.Button(s, text=_("🔄  Scarica dal server ora (da un altro PC)"),
                      command=_scarica_sync, bg='#0078D7', fg='white',
                      font=F('Arial', 10, 'bold'), relief='flat', padx=S(16), pady=S(6),
                      cursor='hand2').pack(anchor='w', pady=(S(10), 0))

        w = _card()
        tk.Label(w, text=_("Importazione da WinLive"), bg='#3a1550', fg='white',
                 font=F('Arial', 13, 'bold')).pack(anchor='w')
        tk.Label(w, text=_("Percorso playlist WinLive e importazione dei file .f10 (singola o in blocco)."),
                 bg='#3a1550', fg='#e8dff2', font=F('Arial', 9), justify='left').pack(anchor='w', pady=(S(2), S(12)))
        tk.Button(w, text=_("📥  Apri importazione WinLive…"),
                  command=self._apri_finestra_winlive, bg='#8B5CF6', fg='white',
                  font=F('Arial', 12, 'bold'), relief='flat', padx=S(24), pady=S(11),
                  cursor='hand2').pack(anchor='w')

    def _apri_finestra_winlive(self):
        if getattr(self, '_win_winlive', None) is not None:
            try:
                if self._win_winlive.winfo_exists():
                    self._win_winlive.deiconify(); self._win_winlive.lift()
                    self._win_winlive.focus_force()
                    return
            except Exception:
                pass

        BG = '#2d0a3f'; CARD = '#3a1550'; SEP = '#4a2d63'
        win = tk.Toplevel(self.window)
        self._win_winlive = win
        win.title(_("Importazione da WinLive"))
        win.configure(bg=BG)
        try:
            win.iconbitmap("img/icona.ico")
        except Exception:
            pass
        W = S(720)
        win.geometry(f"{W}x{S(560)}")
        win.transient(self.window)
        win.resizable(True, True)

        def _on_close():
            self._win_winlive = None
            win.destroy()
        win.protocol("WM_DELETE_WINDOW", _on_close)

        head = tk.Frame(win, bg='#1f0730')
        head.pack(fill='x')
        tk.Label(head, text=_("📥  Importazione da WinLive"), bg='#1f0730', fg='white',
                 font=F('Arial', 16, 'bold')).pack(pady=S(14))

        body = tk.Frame(win, bg=BG)
        body.pack(fill='both', expand=True, padx=S(22), pady=S(18))

        def card(titolo, descr):
            c = tk.Frame(body, bg=CARD, highlightbackground=SEP, highlightthickness=1)
            c.pack(fill='x', pady=(0, S(16)))
            inner = tk.Frame(c, bg=CARD)
            inner.pack(fill='x', padx=S(16), pady=S(14))
            tk.Label(inner, text=titolo, bg=CARD, fg='white',
                     font=F('Arial', 13, 'bold')).pack(anchor='w')
            if descr:
                tk.Label(inner, text=descr, bg=CARD, fg='#e8dff2',
                         font=F('Arial', 9), justify='left').pack(anchor='w', pady=(S(2), S(10)))
            return inner

        c1 = card(_("Percorso playlist WinLive"),
                  _("La cartella dove WinLive tiene le playlist."))
        r1 = tk.Frame(c1, bg=CARD); r1.pack(fill='x')
        self.entry_playlist = tk.Entry(r1, bg='#1a1a1a', fg='white',
                                       font=F('Arial', 10), relief='flat')
        self.entry_playlist.pack(side='left', fill='x', expand=True, ipady=S(4))
        self.entry_playlist.insert(0, Database.get_config('percorso_playlist', ''))
        tk.Button(r1, text=_("Sfoglia"),
                  command=lambda: self.sfoglia_cartella(self.entry_playlist),
                  bg='#0078D7', fg='white', font=F('Arial', 9, 'bold'),
                  relief='flat', padx=S(12)).pack(side='left', padx=(S(8), 0))
        tk.Button(c1, text=_("💾  Salva percorso"), command=self.salva_playlist,
                  bg='#28a745', fg='white', font=F('Arial', 10, 'bold'),
                  relief='flat', padx=S(16), pady=S(6), cursor='hand2').pack(anchor='e', pady=(S(12), 0))

        c2 = card(_("Importa un file F10"),
                  _("Importa un file .f10/.f10list come playlist nel database (indipendente da WinLive)."))
        r2 = tk.Frame(c2, bg=CARD); r2.pack(fill='x')
        tk.Label(r2, text=_("File:"), bg=CARD, fg='white', font=F('Arial', 10)).pack(side='left')
        self.entry_import_f10 = tk.Entry(r2, bg='#1a1a1a', fg='white',
                                         font=F('Arial', 10), relief='flat')
        self.entry_import_f10.pack(side='left', fill='x', expand=True, padx=S(8), ipady=S(4))
        tk.Button(r2, text=_("Sfoglia"),
                  command=lambda: self.sfoglia_file_f10(self.entry_import_f10),
                  bg='#0078D7', fg='white', font=F('Arial', 9, 'bold'),
                  relief='flat', padx=S(12)).pack(side='left')
        r2b = tk.Frame(c2, bg=CARD); r2b.pack(fill='x', pady=(S(10), 0))
        tk.Label(r2b, text=_("Nome playlist (opzionale):"), bg=CARD, fg='white',
                 font=F('Arial', 10)).pack(side='left')
        self.entry_nome_import = tk.Entry(r2b, width=S(24), bg='#1a1a1a', fg='white',
                                          font=F('Arial', 10), relief='flat')
        self.entry_nome_import.pack(side='left', padx=S(8), ipady=S(4))
        tk.Button(c2, text=_("📥  Importa come playlist"),
                  command=self.importa_f10_standalone,
                  bg='#8B5CF6', fg='white', font=F('Arial', 10, 'bold'),
                  relief='flat', padx=S(16), pady=S(6), cursor='hand2').pack(anchor='e', pady=(S(12), 0))

        c3 = card(_("Importa in blocco da una cartella"),
                  _("Importa TUTTI i file .f10/.f10list di una cartella in un colpo solo."))
        r3 = tk.Frame(c3, bg=CARD); r3.pack(fill='x')
        tk.Label(r3, text=_("Cartella:"), bg=CARD, fg='white', font=F('Arial', 10)).pack(side='left')
        self.entry_bulk_f10 = tk.Entry(r3, bg='#1a1a1a', fg='white',
                                       font=F('Arial', 10), relief='flat')
        self.entry_bulk_f10.pack(side='left', fill='x', expand=True, padx=S(8), ipady=S(4))
        tk.Button(r3, text=_("Sfoglia"), command=self._sfoglia_cartella_f10,
                  bg='#0078D7', fg='white', font=F('Arial', 9, 'bold'),
                  relief='flat', padx=S(12)).pack(side='left')
        self._lbl_bulk_status = tk.Label(c3, text="", bg=CARD, fg='#4ade80',
                                         font=F('Arial', 10))
        self._lbl_bulk_status.pack(anchor='w', pady=(S(8), 0))
        tk.Button(c3, text=_("📦  Importa tutte le playlist"),
                  command=self._importa_bulk_f10,
                  bg='#28a745', fg='white', font=F('Arial', 10, 'bold'),
                  relief='flat', padx=S(16), pady=S(6), cursor='hand2').pack(anchor='e', pady=(S(12), 0))

        tk.Button(win, text=_("Chiudi"), command=_on_close,
                  bg='#555555', fg='white', font=F('Arial', 10, 'bold'),
                  relief='flat', padx=S(20), pady=S(8)).pack(pady=(0, S(14)))

        win.update_idletasks()
        rw = max(W, win.winfo_reqwidth())
        sh = win.winfo_screenheight()
        rh = min(win.winfo_reqheight() + S(8), sh - S(80))
        x = (win.winfo_screenwidth() - rw) // 2
        y = max(S(20), (sh - rh) // 2)
        win.geometry(f"{rw}x{rh}+{x}+{y}")
        win.minsize(S(560), S(320))

    op.OpzioniWindow.create_tab_playlist = create_tab_playlist
    op.OpzioniWindow._apri_finestra_winlive = _apri_finestra_winlive
    op.OpzioniWindow._winlive094 = True
    return True


def revert():
    return False


try:
    apply()
except Exception:
    pass
