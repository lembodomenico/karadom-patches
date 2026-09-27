import os


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_141', '1')) == '0'
    except Exception:
        return False


# ---- metodi nuovi/aggiornati per l'albero playlist (copiati dal sorgente) ----

def _aggiorna_listbox_playlist(self):
    tv = self.playlist_listbox
    try:
        tv.delete(*tv.get_children())
    except Exception:
        pass
    for i, p in enumerate(self.playlist_data_filtered):
        try:
            tv.insert('', 'end', iid=str(i), text="📁 %s" % p['nome'])
            tv.insert(str(i), 'end', text='...')
        except Exception:
            pass


def _pl_sel_idx(self):
    try:
        sel = self.playlist_listbox.selection()
        if not sel:
            return None
        iid = sel[0]
        while iid and not iid.isdigit():
            iid = self.playlist_listbox.parent(iid)
        return int(iid) if iid and iid.isdigit() else None
    except Exception:
        return None


def _pl_cartella_madre(self, idx):
    try:
        from moduli.database import Database
        pl = self.playlist_data_filtered[idx]
        if pl.get('tipo') == 'standalone':
            brani = Database.get_playlist_standalone_brani(pl['id'])
        else:
            brani = self._leggi_f10list(pl.get('path', ''))
        dirs = [os.path.dirname(b.get('path', '')) for b in (brani or []) if b.get('path')]
        dirs = [d for d in dirs if d]
        if not dirs:
            return None
        try:
            madre = os.path.commonpath(dirs)
        except Exception:
            madre = dirs[0]
        if madre and os.path.isdir(madre):
            return madre
        return dirs[0] if os.path.isdir(dirs[0]) else None
    except Exception:
        return None


def _pl_on_open(self, event=None):
    tv = self.playlist_listbox
    try:
        sel = tv.selection()
        if not sel:
            return
        iid = sel[0]
        ch = tv.get_children(iid)
        if ch and tv.item(ch[0])['text'] == '...':
            tv.delete(ch[0])
        elif ch:
            return
        if iid.isdigit():
            base = self._pl_cartella_madre(int(iid))
            if not base:
                return
            tv.item(iid, values=(base,))
        else:
            v = tv.item(iid)['values']
            base = str(v[0]) if v else ''
        if not base or not os.path.isdir(base):
            return
        from moduli.disco_lento import lista_sottocartelle_sicura
        sub = lista_sottocartelle_sicura(base)
        if not sub:
            return
        for folder, ha_sub in sub:
            fp = os.path.join(base, folder)
            c = tv.insert(iid, 'end', text="📁 %s" % folder, values=(fp,))
            if ha_sub:
                tv.insert(c, 'end', text='...')
    except Exception as e:
        print('[PLALB141] open:', e)


_PL_EXT = {'.mp3','.mp4','.avi','.mkv','.flv','.wav','.flac','.aac','.ogg','.wma','.m4a',
           '.webm','.mov','.wmv','.mpg','.mpeg','.mid','.midi','.kar','.kfn','.mkf','.m4v',
           '.aiff','.aif','.opus','.ape','.m4b','.mp2','.cdg','.3gp'}


def _pl_brani_cartella(self, path, ricorsivo):
    """Elenco brani (dict pronti per _mostra_brani_playlist) di una cartella.
    ricorsivo=True (cartella madre = tutto) / False (sottocartella = solo il suo contenuto)."""
    out = []
    try:
        if ricorsivo:
            for r, d, files in os.walk(path):
                for f in sorted(files):
                    e = os.path.splitext(f)[1].lower()
                    if e in _PL_EXT:
                        out.append({'path': os.path.join(r, f), 'ext': e[1:].upper(),
                                    'brano_completo': os.path.splitext(f)[0], 'tonalita': '0'})
        else:
            for f in sorted(os.listdir(path)):
                fp = os.path.join(path, f)
                if os.path.isfile(fp):
                    e = os.path.splitext(f)[1].lower()
                    if e in _PL_EXT:
                        out.append({'path': fp, 'ext': e[1:].upper(),
                                    'brano_completo': os.path.splitext(f)[0], 'tonalita': '0'})
    except Exception as e:
        print('[PLALB141] lista:', e)
    return out


def _pl_mostra_con_ui(self, brani, nome):
    """Come on_playlist_select: mostra la barra filtro/bottoni + i brani nella tabella."""
    from moduli.i18n import _
    self.playlist_nome_corrente = nome
    try:
        self.filtro_brani_playlist_frame.pack(side='top', fill='x', before=self.canvas.master)
        self.entry_filtro_brani_pl.delete(0, __import__('tkinter').END)
        self.entry_filtro_brani_pl.insert(0, _("Filtra brani..."))
        self.entry_filtro_brani_pl.config(fg='gray')
    except Exception:
        pass
    try:
        if not self.righe_backup:
            self.backup_righe_attuali()
    except Exception:
        pass
    self.brani_playlist_correnti = brani
    self._mostra_brani_playlist(brani, nome)


def _pl_redraw_buttons(self):
    """Ridisegna i bottoni allineati alle righe VISIBILI del tree.
    ≡ e + SEMPRE (anche brani da cartella senza brano_id); ✕ solo con brano_id.
    (Il vecchio saltava le righe senza brano_id -> sottocartelle senza bottoni.)"""
    if not hasattr(self, '_pl_btn_canvas'):
        return
    self._pl_btn_canvas.delete('all')
    bw = self._S(28)
    _px0, _px1, _px2 = self._S(2), self._S(32), self._S(62)
    try:
        y_offset = self._pl_tree.winfo_rooty() - self._pl_btn_canvas.winfo_rooty()
    except Exception:
        y_offset = 0
    for iid in self._pl_tree.get_children():
        data = self._pl_data.get(iid)
        if not data:
            continue
        try:
            bbox = self._pl_tree.bbox(iid)
        except Exception:
            bbox = None
        if not bbox:
            continue
        y_top = bbox[1] + y_offset
        row_h = bbox[3]
        y_mid = y_top + row_h // 2
        # ≡ grigio (sempre)
        self._pl_btn_canvas.create_rectangle(_px0, y_top, _px0+bw, y_top+row_h,
            fill='#333333', outline='', tags=('btn_drag_%s' % iid, 'btn'))
        self._pl_btn_canvas.create_text(_px0+bw//2, y_mid, text='≡',
            fill='#888888', font=self._F('Segoe UI', 12, 'bold'), tags=('btn_drag_%s' % iid, 'btn'))
        # + blu (sempre)
        self._pl_btn_canvas.create_rectangle(_px1, y_top, _px1+bw, y_top+row_h,
            fill='#0078D7', outline='', tags=('btn_add_%s' % iid, 'btn'))
        self._pl_btn_canvas.create_text(_px1+bw//2, y_mid, text='+',
            fill='white', font=self._F('Segoe UI', 12, 'bold'), tags=('btn_add_%s' % iid, 'btn'))
        # ✕ rosso (sempre)
        self._pl_btn_canvas.create_rectangle(_px2, y_top, _px2+bw, y_top+row_h,
            fill='#dc3545', outline='', tags=('btn_del_%s' % iid, 'btn'))
        self._pl_btn_canvas.create_text(_px2+bw//2, y_mid, text='✕',
            fill='white', font=self._F('Segoe UI', 11, 'bold'), tags=('btn_del_%s' % iid, 'btn'))
    try:
        canvas_h = self._pl_btn_canvas.winfo_height()
        if canvas_h < 2:
            canvas_h = 500
        self._pl_btn_canvas.config(scrollregion=(0, 0, self._S(95), canvas_h))
        self._pl_btn_canvas.yview_moveto(0)
    except Exception:
        pass


def _pl_on_select(self, event=None):
    try:
        tv = self.playlist_listbox
        sel = tv.selection()
        if not sel:
            return
        iid = sel[0]
        if iid.isdigit():
            # cartella madre: flusso ORIGINALE (brani della playlist CON i bottoni)
            self.on_playlist_select(None)
        else:
            # sottocartella: il suo contenuto (ricorsivo sotto di essa)
            v = tv.item(iid)['values']
            p = str(v[0]) if v else ''
            if p and os.path.isdir(p):
                self._pl_mostra_con_ui(self._pl_brani_cartella(p, True), os.path.basename(p))
    except Exception as e:
        print('[PLALB141] select:', e)


def _converti(self):
    """Sostituisce la Listbox playlist con un Treeview (albero) + shim Listbox-compatibili,
    cosi' il codice esistente (curselection/selection_set/see/delete 0,END) continua a funzionare."""
    import tkinter as tk
    from tkinter import ttk
    old = getattr(self, 'playlist_listbox', None)
    if old is None:
        return
    if isinstance(old, ttk.Treeview):
        return  # gia' convertito
    parent = old.master
    sb = None
    for w in parent.winfo_children():
        if isinstance(w, (ttk.Scrollbar, tk.Scrollbar)):
            sb = w
            break
    try:
        old.pack_forget()
    except Exception:
        pass
    try:
        old.destroy()
    except Exception:
        pass
    tree = ttk.Treeview(parent, show='tree', style="Custom.Treeview", selectmode='browse')
    if sb is not None:
        try:
            tree.configure(yscrollcommand=sb.set)
            sb.configure(command=tree.yview)
        except Exception:
            pass
    tree.pack(side='left', fill='both', expand=True)

    # shim Listbox-compatibili
    _orig_del = tree.delete
    def _del(*a):
        if len(a) == 2 and a[0] == 0 and a[1] in ('end', tk.END):
            ids = tree.get_children()
            if ids:
                _orig_del(*ids)
            return
        return _orig_del(*a)
    tree.delete = _del

    tree.curselection = (lambda: ((self._pl_sel_idx(),) if self._pl_sel_idx() is not None else ()))

    _orig_ss = tree.selection_set
    tree.selection_set = (lambda *a: _orig_ss(*[str(x) for x in a]))

    def _sc(*a, **k):
        s = tree.selection()
        if s:
            tree.selection_remove(*s)
    tree.selection_clear = _sc

    _orig_see = tree.see
    tree.see = (lambda i: _orig_see(str(i)))
    tree.activate = (lambda i: _orig_see(str(i)))

    tree.bind('<<TreeviewOpen>>', self._pl_on_open)
    tree.bind('<<TreeviewSelect>>', self._pl_on_select)

    self.playlist_listbox = tree
    print('[PLALB141] pannello playlist convertito ad albero')


def apply():
    if _spenta():
        return False
    try:
        import moduli.libreria as lib
        C = getattr(lib, 'LibreriaSlider', None)
        if C is None or getattr(C, '_plalb141', False):
            return True
        C._aggiorna_listbox_playlist = _aggiorna_listbox_playlist
        C._pl_sel_idx = _pl_sel_idx
        C._pl_cartella_madre = _pl_cartella_madre
        C._pl_brani_cartella = _pl_brani_cartella
        C._pl_mostra_con_ui = _pl_mostra_con_ui
        C._pl_on_open = _pl_on_open
        C._pl_on_select = _pl_on_select
        C._pl_redraw_buttons = _pl_redraw_buttons

        _ocs = C.create_slider

        def _wrap_cs(self, *a, **k):
            r = _ocs(self, *a, **k)
            try:
                _converti(self)
            except Exception as e:
                print('[PLALB141] conversione:', e)
            return r

        C.create_slider = _wrap_cs
        C._plalb141 = True
        print('[PLALB141] albero playlist come i preferiti attivo')
    except Exception as e:
        print('[PLALB141] hook:', e)
    return True


def revert():
    pass


try:
    apply()
except Exception as _e:
    print('patch 141: %s' % _e)
