import sys


def apply():
    try:
        import tkinter as tk
        from tkinter import ttk
    except Exception:
        return False

    # moduli necessari
    libmod = sys.modules.get('moduli.libreria')
    if libmod is None:
        try:
            import moduli.libreria as libmod  # noqa
        except Exception:
            print('[RR160] moduli.libreria non presente (ok)')
            return False
    C = getattr(libmod, 'LibreriaSlider', None)
    if C is None:
        return True

    try:
        from moduli.ui_scale import S, F
    except Exception:
        S = lambda x: x
        F = lambda *a, **k: a[:2] if len(a) >= 2 else ('Segoe UI', 12)

    PH_CANT = "Inserisci il cantante"
    PH_FILT = "Filtra brano o autore"

    def _api():
        from moduli.requests_api_client import api_call
        return api_call

    # ── costruzione pannello agganciato (nascosto) ──
    def _build_dock(self):
        if getattr(self, '_rr_dock_done', False):
            return
        parent = self.header_top.master  # right_frame
        self._rr_pending_id = None
        self._rr_map = {}
        self._rr_visible = False

        fr = tk.Frame(parent, bg="#1a1a1a", bd=2, relief="solid")
        self._rr_frame = fr  # NON packato: compare col bottone

        head = tk.Frame(fr, bg="#1a1a1a")
        head.pack(fill=tk.X, padx=S(8), pady=S(6))
        self._rr_titolo = tk.Label(head, text="📋 RICHIESTE IN ARRIVO", bg="#1a1a1a",
                                   fg="#ffd700", font=F("Segoe UI", 13, "bold"), anchor="w")
        self._rr_titolo.pack(side=tk.LEFT)
        tk.Button(head, text="✕", bg="#dc3545", fg="white", relief="flat", bd=0,
                  cursor="hand2", font=F("Segoe UI", 10, "bold"), width=2,
                  command=lambda: _rr_hide(self)).pack(side=tk.RIGHT)

        try:
            st = ttk.Style()
            st.configure("RRDock.Treeview", background="#2a2a2a", foreground="white",
                         fieldbackground="#2a2a2a", borderwidth=0,
                         font=F("Segoe UI", 13, "bold"), rowheight=S(30))
            st.configure("RRDock.Treeview.Heading", background="#1a1a2e", foreground="#00d4ff",
                         borderwidth=1, font=F("Segoe UI", 13, "bold"))
            st.map("RRDock.Treeview", background=[('selected', '#0078D7')],
                   foreground=[('selected', 'white')])
        except Exception:
            pass

        tf = tk.Frame(fr, bg="#2a2a2a")
        tf.pack(fill=tk.BOTH, expand=True, padx=S(8), pady=(0, S(8)))
        sb = ttk.Scrollbar(tf, orient=tk.VERTICAL)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        cols = ("id", "cantante", "brano", "artista", "ton", "codice")
        tv = ttk.Treeview(tf, columns=cols, show="headings", height=5,
                          style="RRDock.Treeview", yscrollcommand=sb.set)
        self._rr_tree = tv
        tv.heading("id", text="ID")
        tv.heading("cantante", text="👤 CANTANTE")
        tv.heading("brano", text="🎵 BRANO")
        tv.heading("artista", text="🎤 ARTISTA")
        tv.heading("ton", text="🎹 TON")
        tv.heading("codice", text="")
        tv.column("id", width=S(50), anchor="center")
        tv.column("cantante", width=S(200), anchor="w")
        tv.column("brano", width=S(340), anchor="w")
        tv.column("artista", width=S(200), anchor="w")
        tv.column("ton", width=S(60), anchor="center")
        tv.column("codice", width=0, stretch=False)
        tv.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.config(command=tv.yview)
        tv.bind("<<TreeviewSelect>>", lambda e: _on_sel(self))

        self._rr_dock_done = True

    def _rr_titolo_aggiorna(self):
        try:
            n = len(self._rr_tree.get_children())
            self._rr_titolo.config(text=f"📋 RICHIESTE IN ARRIVO ({n})")
        except Exception:
            pass

    def _set_entry(entry, valore, ph):
        try:
            entry.delete(0, tk.END)
            v = str(valore or '').strip()
            if v:
                entry.insert(0, v)
                entry.config(fg='white')
            else:
                entry.insert(0, ph)
                entry.config(fg='gray')
        except Exception:
            pass

    def _on_sel(self):
        sel = self._rr_tree.selection()
        if not sel:
            return
        v = self._rr_tree.item(sel[0], "values")
        _id = v[0]
        cantante = str(v[1]).strip()
        brano = str(v[2]).strip()
        ton = str(v[4]).strip()
        # riempi cantante e tonalità della barra principale
        if hasattr(self, 'entry_cantante'):
            _set_entry(self.entry_cantante, cantante, PH_CANT)
        if hasattr(self, 'entry_ton'):
            try:
                self.entry_ton.delete(0, tk.END)
                self.entry_ton.insert(0, ton or '0')
            except Exception:
                pass
        # metti il brano nel filtro e fai comparire i suggerimenti
        if hasattr(self, 'entry_filtro'):
            _set_entry(self.entry_filtro, brano, PH_FILT)
            try:
                self._debounce_suggerimenti()
            except Exception as e:
                print('[RR160 sugg]', e)
        # ricorda che questo inserimento viene da una richiesta remota
        self._rr_pending_id = _id

    def _rr_carica(self):
        def _worker():
            try:
                resp = _api()('load')
            except Exception as e:
                print('[RR160 load]', e)
                return
            if not (isinstance(resp, dict) and resp.get('ok')):
                return
            rows = resp.get('rows') or []

            def _popola():
                try:
                    if not self._rr_tree.winfo_exists():
                        return
                except Exception:
                    return
                self._rr_tree.delete(*self._rr_tree.get_children())
                self._rr_map = {}
                for r in rows:
                    _id = r.get('ID')
                    cant = str(r.get('CANTANTE') or '').upper()
                    tit = str(r.get('BRANO') or '').strip()
                    art = str(r.get('ARTISTA') or '').strip()
                    ton = str(r.get('TON') or '')
                    cod = str(r.get('CODICE_PRENOTAZIONE') or '')
                    brano = tit
                    artista = art
                    low = tit.lower()
                    if not ('youtu.be/' in low or 'youtube.com/' in low or low.startswith('http')):
                        if " - " in tit:
                            p = tit.split(" - ", 1); artista = p[0].strip(); brano = p[1].strip()
                        elif "-" in tit:
                            p = tit.split("-", 1); artista = p[0].strip(); brano = p[1].strip()
                    iid = self._rr_tree.insert("", "end", values=(
                        _id, cant, str(brano).upper(), str(artista).upper(),
                        str(ton).upper(), cod))
                    self._rr_map[_id] = iid
                _rr_titolo_aggiorna(self)
            try:
                self._rr_frame.after(0, _popola)
            except Exception:
                pass
        import threading
        threading.Thread(target=_worker, daemon=True).start()

    def _rr_show(self):
        try:
            if not self._rr_frame.winfo_ismapped():
                self._rr_frame.pack(side='top', fill='x', before=self.header_top)
            self._rr_visible = True
            _rr_carica(self)
        except Exception as e:
            print('[RR160 show]', e)

    def _rr_hide(self):
        try:
            self._rr_frame.pack_forget()
            self._rr_visible = False
        except Exception:
            pass

    def _rr_toggle(self):
        if getattr(self, '_rr_visible', False):
            _rr_hide(self)
        else:
            _rr_show(self)

    # espongo i metodi sull'istanza (via closure) — li lego nell'__init__ wrap
    def _install(self):
        self._rr_toggle = lambda: _rr_toggle(self)
        self._rr_carica = lambda: _rr_carica(self)

    # ── wrap __init__: costruisce il pannello dopo la UI ──
    if not getattr(C, '_rr160_init', False):
        _orig_init = C.__init__

        def init_wrap(self, *a, **k):
            _orig_init(self, *a, **k)
            try:
                _build_dock(self)
                _install(self)
            except Exception as e:
                print('[RR160 build]', e)
        C.__init__ = init_wrap
        C._rr160_init = True

    # ── wrap crea_riga: dopo l'inserimento, inserito=1 se veniva da remota ──
    if not getattr(C, '_rr160_crea', False):
        _orig_crea = C.crea_riga

        def crea_wrap(self, *a, **k):
            r = _orig_crea(self, *a, **k)
            try:
                pid = getattr(self, '_rr_pending_id', None)
                da_playlist = k.get('from_playlist') or (len(a) >= 5 and a[4])
                if pid is not None and not da_playlist:
                    try:
                        _api()('mark_inserted', ids=[pid])
                    except Exception as e:
                        print('[RR160 mark]', e)
                    iid = (getattr(self, '_rr_map', {}) or {}).pop(pid, None)
                    try:
                        if iid and self._rr_tree.exists(iid):
                            self._rr_tree.delete(iid)
                            _rr_titolo_aggiorna(self)
                    except Exception:
                        pass
                    self._rr_pending_id = None
            except Exception as e:
                print('[RR160 crea hook]', e)
            return r
        C.crea_riga = crea_wrap
        C._rr160_crea = True

    # ── il bottone richieste (campanella) ora fa TOGGLE del pannello ──
    uimod = sys.modules.get('moduli.ui')
    if uimod is not None:
        _orig_apri = getattr(uimod, 'apri_finestra_remoti', None)

        def toggle_remoti(system):
            lib = getattr(system, 'libreria', None)
            if lib is not None and hasattr(lib, '_rr_toggle'):
                try:
                    lib._rr_toggle()
                    return
                except Exception as e:
                    print('[RR160 toggle]', e)
            if callable(_orig_apri):
                _orig_apri(system)
        uimod.apri_finestra_remoti = toggle_remoti

    print('[RR160] Richieste in arrivo nel pannello principale (toggle come YouTube)')
    return True


try:
    apply()
except Exception as _e:
    print('patch 160: %s' % _e)
