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
        nc = _norm2(cantante)
        pl = None
        for p in pls:
            if _norm2(p.get('nome')) == nc:
                pl = p; break
        if pl is None:
            _rrlog("playlist cantante '%s' NON trovata" % cantante); return False
        try:
            brani = Database.get_playlist_standalone_brani(pl['id']) or []
        except Exception as e:
            _rrlog("get_brani err: %s" % e); return False
        nb = _norm2(brano)
        tok = [t for t in nb.split() if len(t) > 1]
        trovato = None
        for b in brani:
            testo = _norm2("%s %s %s" % (b.get('artista') or '', b.get('titolo') or '', b.get('path') or ''))
            if nb and (nb in testo or (tok and all(t in testo for t in tok))):
                trovato = b; break
        if trovato is None:
            _rrlog("canzone '%s' non nella playlist di %s" % (brano, cantante)); return False
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
            if hasattr(self, 'entry_cantante'):
                _set_entry(self.entry_cantante, cant, PH_CANT)
            if hasattr(self, 'entry_ton'):
                try:
                    self.entry_ton.delete(0, tk.END); self.entry_ton.insert(0, ton or '0')
                except Exception:
                    pass
            self._rr_pending_id = _id
            # PRIMA dei suggerimenti: se il cantante ha una playlist con la canzone,
            # apri quella playlist sulla canzone. Altrimenti suggerimenti come sempre.
            if _prova_playlist(self, cant, brano):
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
                        _id = r.get('ID'); cant = str(r.get('CANTANTE') or '').upper()
                        tit = str(r.get('BRANO') or '').strip(); art = str(r.get('ARTISTA') or '').strip()
                        ton = str(r.get('TON') or ''); cod = str(r.get('CODICE_PRENOTAZIONE') or '')
                        brano = tit; artista = art; low = tit.lower()
                        if not ('youtu.be/' in low or 'youtube.com/' in low or low.startswith('http')):
                            if " - " in tit:
                                pp = tit.split(" - ", 1); artista = pp[0].strip(); brano = pp[1].strip()
                            elif "-" in tit:
                                pp = tit.split("-", 1); artista = pp[0].strip(); brano = pp[1].strip()
                        iid = self._rr_tree.insert("", "end", values=(
                            _id, cant, str(brano).upper(), _artisti_puliti(artista).upper(), str(ton).upper(), cod))
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
            self._rr_dock_done = True
            # chiudi il pannello quando PARTE la riproduzione (system.play)
            try:
                sysobj = getattr(self, 'system', None)
                if sysobj is not None:
                    Sc = type(sysobj)
                    if hasattr(Sc, 'play') and not getattr(Sc, '_rr160_play', False):
                        _op = Sc.play
                        def play_wrap(s, *a, **k):
                            try:
                                lib = getattr(s, 'libreria', None)
                                if lib is not None and getattr(lib, '_rr_visible', False):
                                    lib._rr_frame.place_forget(); lib._rr_visible = False
                                    _rrlog("chiuso pannello: parte riproduzione")
                            except Exception:
                                pass
                            return _op(s, *a, **k)
                        Sc.play = play_wrap; Sc._rr160_play = True
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

    def _toggle(self):
        _rrlog("toggle chiamato (visible=%s)" % getattr(self, '_rr_visible', None))
        if getattr(self, '_rr_visible', False):
            # gia' aperto: se ci sono richieste (nuove/lampeggio) AGGIORNA; se non ce ne
            # sono piu' CHIUDE. La ✕ chiude sempre.
            _carica(self, chiudi_se_vuoto=True); _rrlog("toggle: refresh/chiudi-se-vuoto")
        else:
            _show(self)

    # wrap __init__: installa SOLO i metodi (build lazy al primo toggle)
    if not getattr(C, '_rr160_init', False):
        _orig_init = C.__init__
        def init_wrap(self, *a, **k):
            _orig_init(self, *a, **k)
            try:
                self._rr_toggle = lambda s=self: _toggle(s)
                self._rr_dock_done = False
                _rrlog("init wrap: _rr_toggle installato")
            except Exception as e:
                _rrlog("init wrap err: %s" % e)
        C.__init__ = init_wrap
        C._rr160_init = True

    # wrap crea_riga: inserito=1 se veniva da remota
    if not getattr(C, '_rr160_crea', False):
        _orig_crea = C.crea_riga
        def crea_wrap(self, *a, **k):
            r = _orig_crea(self, *a, **k)
            try:
                pid = getattr(self, '_rr_pending_id', None)
                da_pl = k.get('from_playlist') or (len(a) >= 5 and a[4])
                if pid is not None and not da_pl:
                    _segna_inserito(pid, "")
                    iid = (getattr(self, '_rr_map', {}) or {}).pop(pid, None)
                    try:
                        if iid and self._rr_tree.exists(iid):
                            self._rr_tree.delete(iid); _titolo_aggiorna(self)
                    except Exception:
                        pass
                    self._rr_pending_id = None
                    # refresh completo delle richieste dal server
                    try:
                        if getattr(self, '_rr_dock_done', False):
                            _carica(self)
                    except Exception:
                        pass
            except Exception as e:
                _rrlog("crea hook err: %s" % e)
            return r
        C.crea_riga = crea_wrap
        C._rr160_crea = True

    # wrap toggle_slider: chiudi il pannello quando si CHIUDE la scaletta
    if hasattr(C, 'toggle_slider') and not getattr(C, '_rr160_slider', False):
        _ots = C.toggle_slider
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
        C._rr160_slider = True

    # wrap "+" dalla playlist: dopo aver messo il brano in scaletta, ESCI dalla
    # playlist e torna alla scaletta.
    if hasattr(C, '_aggiungi_da_playlist') and not getattr(C, '_rr160_pladd', False):
        _oadd = C._aggiungi_da_playlist
        def add_wrap(self, *a, **k):
            r = _oadd(self, *a, **k)
            # se il brano viene da una richiesta remota -> inserito=1 nella tabella remota
            try:
                pid = getattr(self, '_rr_pending_id', None)
                if pid is not None:
                    _segna_inserito(pid, "+ playlist ")
                    iid = (getattr(self, '_rr_map', {}) or {}).pop(pid, None)
                    try:
                        if iid and self._rr_tree.exists(iid):
                            self._rr_tree.delete(iid); _titolo_aggiorna(self)
                    except Exception:
                        pass
                    self._rr_pending_id = None
                    try:
                        if getattr(self, '_rr_dock_done', False):
                            _carica(self)
                    except Exception:
                        pass
            except Exception as e:
                _rrlog("+ playlist hook err: %s" % e)
            # esci dalla playlist e torna alla scaletta
            try:
                if hasattr(self, 'ripristina_righe_backup'):
                    self.ripristina_righe_backup()
                    _rrlog("+ da playlist: tornato alla scaletta")
            except Exception as e:
                _rrlog("ripristina err: %s" % e)
            return r
        C._aggiungi_da_playlist = add_wrap
        C._rr160_pladd = True

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
