# 030 - su YouTube si puo' cercare anche senza la parola "karaoke".
#
# Alla ricerca veniva aggiunta sempre: va bene quasi sempre, ma quando il
# brano su YouTube esiste solo come originale quella parola in piu' fa
# sparire tutti i risultati. Ora c'e' un interruttore in fondo al campo.
#
# ⚠️ Funzioni COPIATE DAL SORGENTE ed esposte con exec + setattr (come la
#    016): funziona anche nell'eseguibile compilato.
#
# SE NON VA BENE: `patch_030 = 0` la spegne su una macchina sola.

CODICE = 'def _leggi_filtro_karaoke(self):\n    """Acceso, se non e\' stato spento apposta. La scelta si ricorda: chi\n    cerca gli originali non deve rispegnerlo a ogni avvio."""\n    try:\n        from .database import Database\n        return str(Database.get_config(\'yt_filtro_karaoke\', \'1\')).strip() not in (\'0\', \'no\', \'off\')\n    except Exception:\n        return True\n\n\ndef _aggiorna_btn_karaoke(self):\n    """Acceso = verde. Spento = grigio e barrato, cosi\' si capisce a colpo\n    d\'occhio che quella parola NON viene aggiunta."""\n    b = getattr(self, \'btn_karaoke\', None)\n    if b is None:\n        return\n    # ⚠️ NON si usa `BTN`: quello e\' una variabile locale di __init__ e qui\n    #    dentro non esiste. Il font si richiede a F, che e\' importata dal\n    #    modulo e tiene conto del ridimensionamento dello schermo.\n    #\n    # Il testo dice cosa succede PREMENDOLO, non com\'e\' adesso: e\' l\'unico\n    # modo perche\' si capisca senza doverci pensare.\n    try:\n        if self._filtro_karaoke:\n            b.config(text=_("togli filtro\\nkaraoke"),\n                     bg=\'#28a745\', fg=\'white\', font=F(\'Segoe UI\', 9, \'bold\'))\n        else:\n            b.config(text=_("rimetti filtro\\nkaraoke"),\n                     bg=\'#495057\', fg=\'#ffd700\', font=F(\'Segoe UI\', 9, \'bold\'))\n    except Exception:\n        pass\n\n# ---------------- togliere la voce ----------------\n\n\ndef _largh_btn_karaoke(self):\n    """Quanto e\' largo il tasto del filtro con la scritta piu\' lunga.\n\n    Si misura senza toccare quella che si vede: si mette da parte il testo\n    attuale, si provano tutte e due le scritte, e si rimette com\'era.\n    """\n    b = getattr(self, \'btn_karaoke\', None)\n    if b is None:\n        return 0\n    try:\n        adesso = b.cget(\'text\')\n        largo = 0\n        for t in (_("togli filtro\\nkaraoke"), _("rimetti filtro\\nkaraoke")):\n            b.config(text=t)\n            b.update_idletasks()\n            largo = max(largo, b.winfo_reqwidth())\n        b.config(text=adesso)\n        return largo\n    except Exception:\n        return 0\n\n\ndef _cambia_filtro_karaoke(self):\n    self._filtro_karaoke = not self._filtro_karaoke\n    self._aggiorna_btn_karaoke()\n    try:\n        from .database import Database\n        Database.set_config(\'yt_filtro_karaoke\', \'1\' if self._filtro_karaoke else \'0\')\n    except Exception:\n        pass\n\n\ndef _layout_top(self):\n    top = getattr(self, \'_top\', None)\n    if top is None or not top.winfo_exists():\n        return\n    # ⭐ [patch 030] il bottone nasce qui, alla prima disposizione della\n    #    barra: cosi\' la patch non deve rifare __init__, che e\' lungo e\n    #    rischioso. Da qui in poi e\' un widget come gli altri.\n    if getattr(self, \'btn_karaoke\', None) is None:\n        self._filtro_karaoke = self._leggi_filtro_karaoke()\n        self.btn_karaoke = tk.Button(top, text=_("togli filtro karaoke"),\n                                     command=self._cambia_filtro_karaoke,\n                                     relief=\'flat\', cursor=\'hand2\',\n                                     bd=0, highlightthickness=0)\n        self._aggiorna_btn_karaoke()\n        try:\n            from .libreria_widgets import add_tooltip as _tt030\n            _tt030(self.btn_karaoke,\n                   _("Acceso: alla ricerca si aggiunge la parola "\n                     "\\"karaoke\\". Spento: cerca esattamente quello che "\n                     "hai scritto — serve quando il brano su YouTube "\n                     "esiste solo come originale."))\n        except Exception:\n            pass\n    try:\n        top.update_idletasks()\n    except Exception:\n        pass\n    W = top.winfo_width()\n    H = top.winfo_height()\n    if W < 40 or H < 10:\n        return\n    ox = top.winfo_rootx()\n\n    def rel(w):\n        try:\n            if w is None:\n                return None\n            wd = w.winfo_width()\n            if wd < 5:\n                return None\n            return (w.winfo_rootx() - ox, wd)\n        except Exception:\n            return None\n\n    lib = getattr(self.system, \'libreria\', None)\n    cant = rel(getattr(lib, \'entry_cantante\', None))\n    brano = rel(getattr(lib, \'_lbl_brano\', None))\n    filt = rel(getattr(lib, \'entry_filtro\', None))\n    pad = S(4)\n\n    # --- Dest: label allineata a "Cant:", campo allineato/largo come cantante ---\n    if cant:\n        xcant, wcant = cant\n    else:\n        xcant, wcant = S(60), (W // 2) - S(90)\n    # X della label "Cant:" = inizio del frame cantante + padx(5)\n    lbl_x = S(5)\n    try:\n        fc = self.system.libreria.entry_cantante.master\n        lbl_x = (fc.winfo_rootx() - ox) + S(5)\n    except Exception:\n        pass\n    self.lbl_dest.place(x=max(0, lbl_x), y=0, height=H)\n    self.entry_dest.place(x=xcant, y=0, width=wcant, height=H)\n\n    # --- Sfoglia sotto i tasti ▶ 🗑 (tra campo cantante e label brano) ---\n    gap_x0 = xcant + wcant + pad\n    gap_x1 = (brano[0] if brano else (filt[0] if filt else W)) - pad\n    sfw = max(S(70), gap_x1 - gap_x0)\n    self.btn_sfoglia.place(x=gap_x0, y=0, width=sfw, height=H)\n\n    # --- campo ricerca: dalla label "Brano (filtro):" a fine campo filtro ---\n    if brano:\n        xsearch = brano[0]\n    elif filt:\n        xsearch = filt[0]\n    else:\n        xsearch = gap_x0 + sfw + pad\n    filtro_right = (filt[0] + filt[1]) if filt else W\n\n    # --- 3 bottoni (Cerca/Download/Incolla) TUTTI larghi uguali (al piu\' largo) ---\n    # ⚠️ La larghezza si prende sul testo PIU\' LUNGO che ciascun bottone\n    #    puo\' mostrare, non su quello di adesso: il tasto del filtro\n    #    cambia scritta quando lo si preme, e se la misura seguisse il\n    #    testo corrente la barra si riassesterebbe a ogni clic.\n    bw = max(self.btn_cerca.winfo_reqwidth(),\n             self.btn_download.winfo_reqwidth(),\n             self.btn_incolla.winfo_reqwidth(),\n             self.btn_devoc.winfo_reqwidth(),\n             self._largh_btn_karaoke()) + S(4)   # appena un filo d\'aria\n    buttons_w = 4 * bw + 4 * pad     # Cerca, Download, Incolla, Devocalizza\n    search_right = min(filtro_right, W - buttons_w - pad)\n    search_right = max(search_right, xsearch + S(80))\n\n    # ⭐ L\'interruttore "karaoke" sta IN FONDO al campo, dentro il suo\n    #    spazio: il campo si accorcia di quel tanto. Cosi\' si vede mentre\n    #    si scrive, senza rubare posto ai tre bottoni.\n    campo_right = max(xsearch + S(60), search_right - bw - pad)\n    self.entry_search.place(x=xsearch, y=0, width=campo_right - xsearch, height=H)\n    self.btn_karaoke.place(x=campo_right + pad, y=0,\n                           width=search_right - campo_right - pad, height=H)\n\n    bx = search_right + pad\n    self.btn_cerca.place(x=bx, y=0, width=bw, height=H); bx += bw + pad\n    self.btn_download.place(x=bx, y=0, width=bw, height=H); bx += bw + pad\n    self.btn_incolla.place(x=bx, y=0, width=bw, height=H); bx += bw + pad\n    self.btn_devoc.place(x=bx, y=0, width=bw, height=H)\n\n# ---------------- scroll rotellina ----------------\n\n\ndef _cerca_thread(self, query):\n    try:\n        query_clean = re.sub(r"[^\\w\\s\\-àèéìòù]", "", query)[:100]\n        risultati = []\n        # la parola "karaoke" si aggiunge solo se l\'interruttore e\' acceso\n        if getattr(self, \'_filtro_karaoke\', True):\n            query_clean = query_clean + " karaoke"\n        for e in _cerca_youtube(query_clean, 10)[:10]:\n            vid = e.get("id")\n            if not vid:\n                continue\n            url = e.get("url") or f"https://www.youtube.com/watch?v={vid}"\n            thumb = f"https://img.youtube.com/vi/{vid}/hqdefault.jpg"\n            risultati.append((url, thumb, e.get("title") or "Senza titolo"))\n        self.root.after(0, lambda: self._mostra_risultati(risultati))\n    except Exception as ex:\n        self.root.after(0, lambda: self._errore_risultati(str(ex)))'


def _spenta():
    # ⚠️ se la configurazione non risponde NON ci si spegne: nel compilato
    #    quella lettura puo' fallire (lezione della 029)
    try:
        from moduli.database import Database
        if str(Database.get_config('patch_030', '1')).strip() in ('0', 'no', 'off'):
            traccia('spenta a mano (patch_030 = 0)')
            return True
    except Exception:
        pass
    return False


def traccia(testo):
    try:
        import datetime
        import os
        d = os.path.join(os.environ.get('LOCALAPPDATA') or
                         os.path.expanduser('~'), 'KaraDom')
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, 'patch030.log'), 'a', encoding='utf-8') as f:
            f.write('%s  %s' % (
                datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                testo) + chr(10))
    except Exception:
        pass


def apply():
    if _spenta():
        traccia('non mi accendo (vedi la riga qui sopra)')
        return False
    try:
        import moduli.yt2mp3 as m
        C = m.YoutubePanel
        if hasattr(C, '_orig_030'):
            traccia('gia' + chr(39) + ' agganciata')
            return True
        C._orig_030 = C._layout_top
        spazio = m.__dict__
        exec(compile(CODICE, "<patch030>", "exec"), spazio)
        for nome in ('_leggi_filtro_karaoke', '_aggiorna_btn_karaoke',
                     '_largh_btn_karaoke', '_cambia_filtro_karaoke',
                     '_layout_top', '_cerca_thread'):
            setattr(C, nome, spazio[nome])
        # il widget non esiste finche' la barra non si dispone la prima volta
        C.btn_karaoke = None
        traccia('AGGANCIATA: interruttore del filtro "karaoke"')
        print("patch 030: su YouTube si puo' cercare senza \"karaoke\"")
        return True
    except Exception as e:
        traccia('NON agganciata: %s: %s' % (type(e).__name__, e))
        print("patch 030: %s" % e)
        return False


def revert():
    try:
        import sys
        m = sys.modules.get('moduli.yt2mp3')
        C = getattr(m, 'YoutubePanel', None) if m else None
        if C is not None and hasattr(C, '_orig_030'):
            setattr(C, '_layout_top', C._orig_030)
            del C._orig_030
            print("patch 030: rimesso l'originale")
            return True
    except Exception as e:
        print("patch 030: %s" % e)
    return False


try:
    apply()
except Exception:
    pass
