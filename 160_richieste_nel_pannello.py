import sys, os, time


import queue as _queue160
import threading as _threading160

_coda_log = _queue160.Queue()


def _scrivi_log():
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    p = os.path.join(base, "KaraDom", "rr160.log")
    while True:
        righe = [_coda_log.get()]
        while not _coda_log.empty():
            righe.append(_coda_log.get_nowait())
        try:
            if os.path.exists(p) and os.path.getsize(p) > 2 * 1024 * 1024:
                os.replace(p, p + ".vecchio")
            with open(p, "a", encoding="utf-8") as f:
                f.writelines(righe)
        except Exception:
            pass


_threading160.Thread(target=_scrivi_log, name="Log160", daemon=True).start()


def _rrlog(msg):
    try:
        _coda_log.put_nowait("[%s] %s\n" % (time.strftime("%H:%M:%S"), msg))
    except Exception:
        pass


def _in_sfondo(fn, *a, **k):
    _threading160.Thread(target=fn, args=a, kwargs=k, daemon=True).start()


def _segna_inserito(pid, da_dove):
    def _do():
        try:
            from moduli.requests_api_client import api_call
            api_call('mark_inserted', ids=[pid]); _rrlog("%smark_inserted id=%s" % (da_dove, pid))
        except Exception as e:
            _rrlog("%smark err: %s" % (da_dove, e))
    _in_sfondo(_do)


import re as _re160

_VER160 = 7

_MODIFICHE160 = {}
_INSERITE160 = set()


def _originale160(obj, flag, attr, var):
    o = getattr(obj, '_rr160_o_' + flag, None)
    if o is not None:
        return o
    f = getattr(obj, attr)
    if getattr(obj, '_rr160_' + flag, None) is True:
        fn = getattr(f, '__func__', f)
        try:
            for nome, cella in zip(fn.__code__.co_freevars, fn.__closure__ or ()):
                if nome == var:
                    return cella.cell_contents
        except Exception:
            pass
    return f

_PREFISSO_NUM = _re160.compile(r'^\s*\d+\s*_\s*')


def _senza_numero(nome):
    return _PREFISSO_NUM.sub('', str(nome or '')).strip()

_FRA_ARTISTI = _re160.compile(
    r'\s*(?:,|;|&|\+|/|\s(?:feat\.?|ft\.?|featuring|e|and|con|with|vs\.?|x)\s)\s*', _re160.I)
_FEAT_PAR = _re160.compile(r'\s*[\(\[]\s*(?:feat\.?|ft\.?|featuring|with|con)\s+([^\)\]]*)[\)\]]', _re160.I)
_FEAT_CODA = _re160.compile(r'\s+(?:feat\.?|ft\.?|featuring)\s+(.*)$', _re160.I)
_TAG_VERSIONE = _re160.compile(
    r'[\(\[]?\b(?:duetto|duet|live|karaoke|base|versione|version|remix|acustica|acoustic|'
    r'remastered|remaster)\b[\)\]]?', _re160.I)


def _artisti(artista, extra=()):
    fuori = []
    for blocco in [str(artista or '')] + list(extra):
        for a in _FRA_ARTISTI.split(blocco.strip()):
            a = a.strip(' .-')
            if a and a.lower() not in [x.lower() for x in fuori]:
                fuori.append(a)
    return fuori


def _artisti_puliti(artista):
    return ', '.join(_artisti(artista))


def _filtro_pulito(brano, artista):
    brano = str(brano or '').strip()
    extra = []
    m = _FEAT_PAR.search(brano)
    while m:
        extra.append(m.group(1))
        brano = (brano[:m.start()] + ' ' + brano[m.end():]).strip()
        m = _FEAT_PAR.search(brano)
    m = _FEAT_CODA.search(brano)
    if m:
        extra.append(m.group(1))
        brano = brano[:m.start()].strip()
    senza = _re160.sub(r'\s+', ' ', _TAG_VERSIONE.sub(' ', brano)).strip(' -')
    if senza:
        brano = senza
    arts = _artisti(artista, extra)
    primo = arts[0] if arts else ''
    return (brano + ' ' + primo).strip()


def apply():
    try:
        import tkinter as tk
        from tkinter import ttk
    except Exception as e:
        _rrlog("no tkinter: %s" % e)
        return False

    libmod = sys.modules.get('moduli.libreria')
    if libmod is None:
        try:
            import moduli.libreria as libmod  # noqa
        except Exception as e:
            _rrlog("import moduli.libreria FALLITO: %s" % e)
            return False
    C = getattr(libmod, 'LibreriaSlider', None)
    if C is None:
        _rrlog("LibreriaSlider non trovata")
        return True

    try:
        from moduli.ui_scale import S, F
    except Exception:
        S = lambda x: x
        def F(*a, **k):
            fam = a[0] if a else "Segoe UI"
            sz = a[1] if len(a) > 1 else 12
            st = a[2] if len(a) > 2 else ""
            return (fam, sz, st) if st else (fam, sz)

    PH_CANT = "Inserisci il cantante"
    PH_FILT = "Filtra brano o autore"

    def _api():
        from moduli.requests_api_client import api_call
        return api_call

    def _set_entry(entry, valore, ph):
        try:
            entry.delete(0, tk.END)
            v = str(valore or '').strip()
            if v:
                entry.insert(0, v); entry.config(fg='white')
            else:
                entry.insert(0, ph); entry.config(fg='gray')
        except Exception:
            pass

    def _titolo_aggiorna(self):
        try:
            n = len(self._rr_tree.get_children())
            self._rr_titolo.config(text="\U0001F4CB RICHIESTE IN ARRIVO (%d)" % n)
        except Exception:
            pass

    def _norm2(s):
        import unicodedata, re as _re
        s = unicodedata.normalize('NFD', str(s or ''))
        s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
        s = _re.sub(r"[^a-z0-9]+", " ", s.lower())
        return s.strip()

    def _prova_playlist(self, cantante, brano):
        """Se esiste una playlist col nome del cantante e contiene la canzone,
        apre quella playlist FILTRATA sulla canzone (per selezionarla). True se aperta."""
        try:
            from moduli.database import Database
        except Exception:
            try:
                from database import Database
            except Exception as e:
                _rrlog("no Database: %s" % e); return False
        try:
            pls = Database.get_playlist_standalone_list() or []
        except Exception as e:
            _rrlog("get_playlist_list err: %s" % e); return False
        nc = _norm2(_senza_numero(cantante) or cantante)
        candidate = [p for p in pls if _norm2(_senza_numero(p.get('nome')) or p.get('nome')) == nc]
        candidate.sort(key=lambda p: _norm2(p.get('nome')) != _norm2(cantante))
        if not candidate:
            _rrlog("playlist cantante '%s' NON trovata" % cantante); return False
        nb = _norm2(brano)
        tok = [t for t in nb.split() if len(t) > 1]
        pl = brani = trovato = None
        for p in candidate:
            try:
                bb = Database.get_playlist_standalone_brani(p['id']) or []
            except Exception as e:
                _rrlog("get_brani err: %s" % e); continue
            for b in bb:
                testo = _norm2("%s %s %s" % (b.get('artista') or '', b.get('titolo') or '', b.get('path') or ''))
                if nb and (nb in testo or (tok and all(t in testo for t in tok))):
                    pl, brani, trovato = p, bb, b; break
            if trovato is not None:
                break
        if trovato is None:
            _rrlog("canzone '%s' non nelle playlist di %s (%s)" % (
                brano, cantante, ', '.join(str(p.get('nome')) for p in candidate))); return False
        # apri la playlist con i suoi brani, filtrata sulla canzone
        try:
            if not getattr(self, 'slider_visible', False):
                self.toggle_slider()
        except Exception:
            pass
        try:
            self._pl_mostra_con_ui(brani, pl['nome'])
        except Exception as e:
            _rrlog("mostra playlist err: %s" % e); return False
        try:
            e = self.entry_filtro_brani_pl
            e.delete(0, tk.END); e.insert(0, brano); e.config(fg='white')
            self.filtra_brani_playlist()
        except Exception as ex:
            _rrlog("filtra playlist err: %s" % ex)
        _rrlog("APERTA playlist %s sulla canzone %s" % (pl['nome'], brano))
        return True

    def _on_sel(self):
        try:
            sel = self._rr_tree.selection()
            if not sel:
                return
            v = self._rr_tree.item(sel[0], "values")
            _id = v[0]; cant = str(v[1]).strip(); brano = str(v[2]).strip()
            artista = str(v[3]).strip(); ton = str(v[4]).strip()
            cant_richiesta = cant
            cant = _senza_numero(cant) or cant
            if hasattr(self, 'entry_cantante'):
                _set_entry(self.entry_cantante, cant, PH_CANT)
            if hasattr(self, 'entry_ton'):
                try:
                    self.entry_ton.delete(0, tk.END); self.entry_ton.insert(0, ton or '0')
                except Exception:
                    pass
            self._rr_pending_id = _id
            self._rr_pending_cant = cant
            # PRIMA dei suggerimenti: se il cantante ha una playlist con la canzone,
            # apri quella playlist sulla canzone. Altrimenti suggerimenti come sempre.
            if _prova_playlist(self, cant, brano) or (
                    cant_richiesta != cant and _prova_playlist(self, cant_richiesta, brano)):
                _rrlog("selezione id=%s -> playlist" % _id)
                return
            if hasattr(self, 'entry_filtro'):
                _filtro = _filtro_pulito(brano, artista)
                _set_entry(self.entry_filtro, _filtro, PH_FILT)
                try:
                    self._debounce_suggerimenti()
                except Exception as e:
                    _rrlog("debounce err: %s" % e)
            _rrlog("selezione id=%s cant=%s brano=%s ton=%s (suggerimenti)" % (_id, cant, brano, ton))
        except Exception as e:
            _rrlog("on_sel err: %s" % e)

    def _menu_riga(self, e):
        try:
            iid = self._rr_tree.identify_row(e.y)
            if not iid:
                return
            self._rr_tree.selection_set(iid); self._rr_tree.focus(iid)
            m = tk.Menu(self._rr_tree, tearoff=0, bg="#2a2a2a", fg="white", activebackground="#0078D7",
                        activeforeground="white", font=F("Segoe UI", 12, "bold"))
            m.add_command(label="\u270F  Modifica", command=lambda: _modifica(self, iid))
            m.tk_popup(e.x_root, e.y_root)
        except Exception as ex:
            _rrlog("menu riga err: %s" % ex)

    def _modifica(self, iid):
        try:
            v = list(self._rr_tree.item(iid, "values"))
        except Exception:
            return
        while len(v) < 6:
            v.append('')
        top = tk.Toplevel(self._rr_frame)
        top.title("Modifica richiesta")
        top.configure(bg="#1a1a1a")
        top.transient(self._rr_frame.winfo_toplevel())
        top.resizable(False, False)
        tk.Label(top, text="\u270F MODIFICA RICHIESTA", bg="#1a1a1a", fg="#ffd700",
                 font=F("Segoe UI", 13, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", padx=S(12), pady=(S(10), S(6)))
        campi = []
        for r, (nome, val, larg) in enumerate((("CANTANTE", v[1], 34), ("BRANO", v[2], 34),
                                               ("ARTISTA", v[3], 34), ("TONALITA'", v[4], 6)), start=1):
            tk.Label(top, text=nome, bg="#1a1a1a", fg="#00d4ff", font=F("Segoe UI", 11, "bold"),
                     anchor="w").grid(row=r, column=0, sticky="w", padx=S(12), pady=S(4))
            en = tk.Entry(top, width=larg, bg="#2a2a2a", fg="white", insertbackground="white", relief="flat",
                          font=F("Segoe UI", 12, "bold"))
            en.insert(0, str(val))
            en.grid(row=r, column=1, sticky="w", padx=(0, S(12)), pady=S(4), ipady=S(3))
            campi.append(en)

        def salva(_e=None):
            nuovi = tuple(en.get().strip() for en in campi)
            _id = v[0]
            _MODIFICHE160[str(_id)] = nuovi
            try:
                if self._rr_tree.exists(iid):
                    self._rr_tree.item(iid, values=(_id,) + nuovi + (v[5],))
            except Exception:
                pass
            _rrlog("modifica id=%s -> %r" % (_id, nuovi))

            def _invia():
                try:
                    r = _api()('update_request', id=int(_id), cantante=nuovi[0], brano=nuovi[1],
                               artista=nuovi[2], ton=nuovi[3])
                    _rrlog("update_request id=%s: %r" % (_id, r))
                except Exception as ex:
                    _rrlog("update_request err: %s" % ex)
            _in_sfondo(_invia)
            top.destroy()
            try:
                if str(getattr(self, '_rr_pending_id', '')) == str(_id) or iid in self._rr_tree.selection():
                    _on_sel(self)
            except Exception:
                pass

        bt = tk.Frame(top, bg="#1a1a1a")
        bt.grid(row=5, column=0, columnspan=2, sticky="e", padx=S(12), pady=(S(8), S(12)))
        tk.Button(bt, text="ANNULLA", bg="#444444", fg="white", relief="flat", bd=0, cursor="hand2",
                  font=F("Segoe UI", 11, "bold"), padx=S(14), pady=S(4), command=top.destroy).pack(side=tk.RIGHT)
        tk.Button(bt, text="SALVA", bg="#28a745", fg="white", relief="flat", bd=0, cursor="hand2",
                  font=F("Segoe UI", 11, "bold"), padx=S(14), pady=S(4), command=salva).pack(side=tk.RIGHT, padx=(0, S(8)))
        top.bind("<Return>", salva)
        top.bind("<Escape>", lambda e: top.destroy())
        try:
            top.update_idletasks()
            x = self._rr_frame.winfo_rootx() + (self._rr_frame.winfo_width() - top.winfo_width()) // 2
            y = self._rr_frame.winfo_rooty() + S(20)
            top.geometry("+%d+%d" % (max(0, x), max(0, y)))
            top.grab_set()
            campi[0].focus_set(); campi[0].select_range(0, tk.END)
        except Exception:
            pass

    def _carica(self, chiudi_se_vuoto=False):
        import threading
        def _worker():
            try:
                resp = _api()('load')
            except Exception as e:
                _rrlog("load err: %s" % e); return
            if not (isinstance(resp, dict) and resp.get('ok')):
                _rrlog("load risposta non ok: %r" % (resp,)); return
            rows = resp.get('rows') or []
            _rrlog("load ok, righe=%d" % len(rows))
            def _popola():
                try:
                    if not self._rr_tree.winfo_exists():
                        return
                    self._rr_tree.delete(*self._rr_tree.get_children())
                    self._rr_map = {}
                    for r in rows:
                        _id = r.get('ID')
                        if str(_id) in _INSERITE160:
                            continue
                        cant = str(r.get('CANTANTE') or '').upper()
                        tit = str(r.get('BRANO') or '').strip(); art = str(r.get('ARTISTA') or '').strip()
                        ton = str(r.get('TON') or ''); cod = str(r.get('CODICE_PRENOTAZIONE') or '')
                        brano = tit; artista = art; low = tit.lower()
                        if not ('youtu.be/' in low or 'youtube.com/' in low or low.startswith('http')):
                            if " - " in tit:
                                pp = tit.split(" - ", 1); artista = pp[0].strip(); brano = pp[1].strip()
                            elif "-" in tit:
                                pp = tit.split("-", 1); artista = pp[0].strip(); brano = pp[1].strip()
                        valori = (_id, cant, str(brano).upper(), _artisti_puliti(artista).upper(), str(ton).upper(), cod)
                        if str(_id) in _MODIFICHE160:
                            valori = (_id,) + _MODIFICHE160[str(_id)] + (cod,)
                        iid = self._rr_tree.insert("", "end", values=valori)
                        self._rr_map[_id] = iid
                    _titolo_aggiorna(self)
                    if chiudi_se_vuoto and len(rows) == 0:
                        _hide(self); _rrlog("nessuna richiesta -> chiudo")
                except Exception as e:
                    _rrlog("popola err: %s" % e)
            try:
                self._rr_frame.after(0, _popola)
            except Exception as e:
                _rrlog("after popola err: %s" % e)
        threading.Thread(target=_worker, daemon=True).start()

    def _build(self):
        if getattr(self, '_rr_dock_done', False):
            return True
        # host = finestra principale (root), così il pannello sta SOPRA (area palco),
        # come overlay, senza coprire barra/righe della libreria.
        parent = getattr(self, 'parent', None)
        if parent is None:
            try:
                parent = self.header_top.winfo_toplevel()
            except Exception as e:
                _rrlog("build: nessun parent: %s" % e)
                return False
        try:
            self._rr_pending_id = None
            self._rr_map = {}
            self._rr_visible = False
            fr = tk.Frame(parent, bg="#1a1a1a", bd=2, relief="solid")
            self._rr_frame = fr
            head = tk.Frame(fr, bg="#1a1a1a"); head.pack(fill=tk.X, padx=S(8), pady=S(6))
            self._rr_titolo = tk.Label(head, text="\U0001F4CB RICHIESTE IN ARRIVO", bg="#1a1a1a",
                                       fg="#ffd700", font=F("Segoe UI", 13, "bold"), anchor="w")
            self._rr_titolo.pack(side=tk.LEFT)
            tk.Button(head, text="✕", bg="#dc3545", fg="white", relief="flat", bd=0,
                      cursor="hand2", font=F("Segoe UI", 10, "bold"), width=2,
                      command=lambda: _hide(self)).pack(side=tk.RIGHT)
            try:
                st = ttk.Style()
                st.configure("RRDock.Treeview", background="#2a2a2a", foreground="white",
                             fieldbackground="#2a2a2a", borderwidth=0,
                             font=F("Segoe UI", 13, "bold"), rowheight=S(30))
                st.configure("RRDock.Treeview.Heading", background="#1a1a2e", foreground="#00d4ff",
                             borderwidth=1, font=F("Segoe UI", 13, "bold"))
                st.map("RRDock.Treeview", background=[('selected', '#0078D7')], foreground=[('selected', 'white')])
            except Exception:
                pass
            tf = tk.Frame(fr, bg="#2a2a2a"); tf.pack(fill=tk.BOTH, expand=True, padx=S(8), pady=(0, S(8)))
            sb = ttk.Scrollbar(tf, orient=tk.VERTICAL); sb.pack(side=tk.RIGHT, fill=tk.Y)
            cols = ("id", "cantante", "brano", "artista", "ton", "codice")
            tv = ttk.Treeview(tf, columns=cols, show="headings", height=5,
                              style="RRDock.Treeview", yscrollcommand=sb.set)
            self._rr_tree = tv
            for c, t in (("id", "ID"), ("cantante", "\U0001F464 CANTANTE"), ("brano", "\U0001F3B5 BRANO"),
                         ("artista", "\U0001F3A4 ARTISTA"), ("ton", "\U0001F3B9 TON"), ("codice", "")):
                tv.heading(c, text=t)
            tv.column("id", width=S(50), anchor="center")
            tv.column("cantante", width=S(200), anchor="w")
            tv.column("brano", width=S(340), anchor="w")
            tv.column("artista", width=S(200), anchor="w")
            tv.column("ton", width=S(60), anchor="center")
            tv.column("codice", width=0, stretch=False)
            tv.pack(side=tk.LEFT, fill=tk.BOTH, expand=True); sb.config(command=tv.yview)
            tv.bind("<<TreeviewSelect>>", lambda e: _on_sel(self))
            tv.bind("<Button-3>", lambda e: _menu_riga(self, e))
            self._rr_dock_done = True
            # chiudi il pannello quando PARTE la riproduzione (system.play)
            try:
                sysobj = getattr(self, 'system', None)
                if sysobj is not None:
                    Sc = type(sysobj)
                    if hasattr(Sc, 'play') and getattr(Sc, '_rr160_play', None) != _VER160:
                        _op = _originale160(Sc, 'play', 'play', '_op')
                        Sc._rr160_o_play = _op
                        def play_wrap(s, *a, **k):
                            try:
                                lib = getattr(s, 'libreria', None)
                                if lib is not None and getattr(lib, '_rr_visible', False):
                                    lib._rr_frame.place_forget(); lib._rr_visible = False
                                    _rrlog("chiuso pannello: parte riproduzione")
                            except Exception:
                                pass
                            return _op(s, *a, **k)
                        Sc.play = play_wrap; Sc._rr160_play = _VER160
            except Exception as e:
                _rrlog("wrap play err: %s" % e)
            _rrlog("build OK")
            return True
        except Exception as e:
            _rrlog("build err: %s" % e)
            return False

    def _show(self):
        # aprendo il pannello richieste col bottone, se la scaletta è chiusa aprila
        try:
            if hasattr(self, 'toggle_slider') and not getattr(self, 'slider_visible', False):
                self.toggle_slider(); _rrlog("apertura pannello: scaletta chiusa -> aperta")
        except Exception as e:
            _rrlog("apri scaletta err: %s" % e)
        if not _build(self):
            return
        try:
            # allinea il pannello ESATTAMENTE al blocco barra/righe (stessa X e larghezza),
            # appena SOPRA la barra Cant/Brano/Ton (come img 9).
            try:
                self.parent.update_idletasks()
                rf = self.header_top.master
                rx = self.parent.winfo_rootx(); ry = self.parent.winfo_rooty()
                x = rf.winfo_rootx() - rx
                w = rf.winfo_width()
                y_bar = self.header_top.winfo_rooty() - ry
                if w < 50 or y_bar < 60:
                    raise ValueError("misure non pronte")
                dx = min(x, 16)   # appena piu' a sinistra
                x -= dx; w += dx
                self._rr_frame.place(x=x, y=y_bar, width=w, anchor='sw')
            except Exception:
                self._rr_frame.place(relx=0.5, rely=0.6, anchor='s', relwidth=0.7)
            self._rr_frame.lift()
            self._rr_visible = True
            _carica(self)
            _rrlog("show sopra la barra (y=%s)" % y_bar)
        except Exception as e:
            _rrlog("show err: %s" % e)

    def _hide(self):
        try:
            self._rr_frame.place_forget(); self._rr_visible = False; _rrlog("hide")
        except Exception as e:
            _rrlog("hide err: %s" % e)

    def _togli_riga(self, pid):
        try:
            mappa = getattr(self, '_rr_map', {}) or {}
            iid = None
            for k in list(mappa):
                if str(k) == str(pid):
                    iid = mappa.pop(k)
            if iid is None:
                for i in self._rr_tree.get_children():
                    if str(self._rr_tree.item(i, 'values')[0]) == str(pid):
                        iid = i
            if iid and self._rr_tree.exists(iid):
                self._rr_tree.delete(iid); _titolo_aggiorna(self)
        except Exception as e:
            _rrlog("togli riga err: %s" % e)

    def _svuota_campi(self):
        try:
            if hasattr(self, 'entry_cantante'):
                _set_entry(self.entry_cantante, '', PH_CANT)
            if hasattr(self, 'entry_filtro'):
                _set_entry(self.entry_filtro, '', PH_FILT)
            if hasattr(self, 'entry_ton'):
                self.entry_ton.delete(0, tk.END); self.entry_ton.insert(0, '0')
            _rrlog("richiesta inserita -> campi svuotati")
        except Exception as e:
            _rrlog("svuota campi err: %s" % e)

    def _dopo_inserita(self):
        try:
            if not getattr(self, '_rr_dock_done', False):
                return
            if not self._rr_tree.get_children():
                _hide(self); _rrlog("ultima richiesta inserita -> chiudo")
            elif getattr(self, '_rr_visible', False):
                self._rr_frame.lift(); _rrlog("richiesta inserita, altre in attesa -> resta aperto")
            _carica(self, chiudi_se_vuoto=True)
        except Exception as e:
            _rrlog("dopo inserita err: %s" % e)

    def _toggle(self):
        _rrlog("toggle chiamato (visible=%s)" % getattr(self, '_rr_visible', None))
        if getattr(self, '_rr_visible', False):
            # gia' aperto: se ci sono richieste (nuove/lampeggio) AGGIORNA; se non ce ne
            # sono piu' CHIUDE. La ✕ chiude sempre.
            _carica(self, chiudi_se_vuoto=True); _rrlog("toggle: refresh/chiudi-se-vuoto")
        else:
            _show(self)

    # wrap __init__: installa SOLO i metodi (build lazy al primo toggle)
    if getattr(C, '_rr160_init', None) != _VER160:
        _orig_init = _originale160(C, 'init', '__init__', '_orig_init')
        C._rr160_o_init = _orig_init
        def init_wrap(self, *a, **k):
            _orig_init(self, *a, **k)
            try:
                self._rr_toggle = lambda s=self: _toggle(s)
                self._rr_dock_done = False
                _rrlog("init wrap: _rr_toggle installato")
            except Exception as e:
                _rrlog("init wrap err: %s" % e)
        C.__init__ = init_wrap
        C._rr160_init = _VER160

    # wrap crea_riga: inserito=1 se veniva da remota
    if getattr(C, '_rr160_crea', None) != _VER160:
        _orig_crea = _originale160(C, 'crea', 'crea_riga', '_orig_crea')
        C._rr160_o_crea = _orig_crea
        def crea_wrap(self, *a, **k):
            r = _orig_crea(self, *a, **k)
            try:
                pid = getattr(self, '_rr_pending_id', None)
                da_pl = k.get('from_playlist') or (len(a) >= 5 and a[4])
                cant_riga = k.get('cantante', a[0] if a else '')
                if pid is not None and not da_pl and _norm2(_senza_numero(cant_riga)) != _norm2(_senza_numero(getattr(self, '_rr_pending_cant', ''))):
                    _rrlog("riga di '%s' non e' la richiesta id=%s di '%s': resta in attesa"
                           % (cant_riga, pid, getattr(self, '_rr_pending_cant', '')))
                    pid = None
                if pid is not None and not da_pl:
                    _segna_inserito(pid, "")
                    _INSERITE160.add(str(pid))
                    _togli_riga(self, pid)
                    self._rr_pending_id = None
                    _dopo_inserita(self)
                    _svuota_campi(self)
            except Exception as e:
                _rrlog("crea hook err: %s" % e)
            return r
        C.crea_riga = crea_wrap
        C._rr160_crea = _VER160

    # wrap toggle_slider: chiudi il pannello quando si CHIUDE la scaletta
    if hasattr(C, 'toggle_slider') and getattr(C, '_rr160_slider', None) != _VER160:
        _ots = _originale160(C, 'slider', 'toggle_slider', '_ots')
        C._rr160_o_slider = _ots
        def ts_wrap(self, *a, **k):
            r = _ots(self, *a, **k)
            try:
                if not getattr(self, 'slider_visible', True) and getattr(self, '_rr_visible', False):
                    self._rr_frame.place_forget(); self._rr_visible = False
                    _rrlog("chiuso pannello: scaletta chiusa")
            except Exception:
                pass
            return r
        C.toggle_slider = ts_wrap
        C._rr160_slider = _VER160

    # wrap "+" dalla playlist: dopo aver messo il brano in scaletta, ESCI dalla
    # playlist e torna alla scaletta.
    if hasattr(C, '_aggiungi_da_playlist') and getattr(C, '_rr160_pladd', None) != _VER160:
        _oadd = _originale160(C, 'pladd', '_aggiungi_da_playlist', '_oadd')
        C._rr160_o_pladd = _oadd
        def add_wrap(self, *a, **k):
            if 'cantante' in k:
                k['cantante'] = _senza_numero(k['cantante']) or k['cantante']
            elif a:
                a = ((_senza_numero(a[0]) or a[0]),) + tuple(a[1:])
            r = _oadd(self, *a, **k)
            richiesta_fatta = False
            # se il brano viene da una richiesta remota -> inserito=1 nella tabella remota
            try:
                pid = getattr(self, '_rr_pending_id', None)
                cant_riga = k.get('cantante', a[0] if a else '')
                if pid is not None and _norm2(_senza_numero(cant_riga)) != _norm2(_senza_numero(getattr(self, '_rr_pending_cant', ''))):
                    _rrlog("+ playlist: '%s' non e' la richiesta id=%s: resta in attesa" % (cant_riga, pid))
                    pid = None
                if pid is not None:
                    _segna_inserito(pid, "+ playlist ")
                    _INSERITE160.add(str(pid))
                    _togli_riga(self, pid)
                    self._rr_pending_id = None
                    richiesta_fatta = True
                    _dopo_inserita(self)
            except Exception as e:
                _rrlog("+ playlist hook err: %s" % e)
            # esci dalla playlist e torna alla scaletta
            try:
                if hasattr(self, 'ripristina_righe_backup'):
                    self.ripristina_righe_backup()
                    _rrlog("+ da playlist: tornato alla scaletta")
            except Exception as e:
                _rrlog("ripristina err: %s" % e)
            if richiesta_fatta:
                _svuota_campi(self)
                try:
                    self.entry_cantante.winfo_toplevel().after(150, lambda: _svuota_campi(self))
                except Exception:
                    pass
            return r
        C._aggiungi_da_playlist = add_wrap
        C._rr160_pladd = _VER160

    # il bottone richieste (campanella) ora fa TOGGLE del pannello.
    # ⛔ ui.py fa un import LOCALE `from .richieste_remote import apri_finestra_remoti`
    #    DENTRO la funzione che costruisce la UI (gira DOPO questa patch): quindi
    #    va sostituita la funzione NEL MODULO richieste_remote, così l'import locale
    #    di ui prende la nostra versione. Sostituisco anche il globale di ui (backup).
    rrmod = sys.modules.get('moduli.richieste_remote')
    if rrmod is None:
        try:
            import moduli.richieste_remote as rrmod  # noqa
        except Exception as e:
            rrmod = None
            _rrlog("import richieste_remote fallito: %s" % e)
    _orig_apri = None
    if rrmod is not None:
        if getattr(rrmod, '_rr160_orig', None) is None:
            rrmod._rr160_orig = getattr(rrmod, 'apri_finestra_remoti', None)
        _orig_apri = rrmod._rr160_orig

    def toggle_remoti(system):
        _rrlog("toggle_remoti chiamato")
        lib = getattr(system, 'libreria', None)
        if lib is not None and hasattr(lib, '_rr_toggle'):
            try:
                lib._rr_toggle(); return
            except Exception as e:
                _rrlog("toggle_remoti err: %s" % e)
        _rrlog("fallback vecchia finestra (lib=%r has_toggle=%s)" % (
            lib is not None, hasattr(lib, '_rr_toggle') if lib is not None else False))
        if callable(_orig_apri):
            _orig_apri(system)

    if rrmod is not None:
        rrmod.apri_finestra_remoti = toggle_remoti
        _rrlog("richieste_remote.apri_finestra_remoti sostituito con toggle")
    uimod = sys.modules.get('moduli.ui')
    if uimod is not None:
        uimod.apri_finestra_remoti = toggle_remoti
        _rrlog("ui.apri_finestra_remoti sostituito con toggle")

    _rrlog("apply OK")
    print('[RR160] Richieste nel pannello principale (toggle)')
    return True


try:
    _rrlog("=== patch 160 caricata ===")
    apply()
except Exception as _e:
    _rrlog("apply EXCEPTION: %s" % _e)
    print('patch 160: %s' % _e)
