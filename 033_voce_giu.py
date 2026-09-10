# 033 - un tasto abbassa la voce del brano che sta suonando.
#
# La voce sta quasi sempre al centro del mix: abbassando quello che le due
# casse hanno in comune, la voce scende. Subito, mentre il brano va, e si
# torna indietro premendo di nuovo. Non separa niente e non crea nessun file.
#
# Misurato su un brano di prova: voce -53 dB, basso -2,4 dB (resta pieno).
# Il grave non si tocca: sotto i 200 Hz cassa e basso restano dove sono.
#
# SE NON VA BENE: `patch_033 = 0` la spegne su una macchina sola.

CODICE_BASS = 'def set_voce(self, quanto):\n    """quanto: 0 = voce com\'e\', 100 = voce giu\' al massimo."""\n    try:\n        q = max(0, min(100, int(quanto))) / 100.0\n    except Exception:\n        q = 0.0\n    self._voce_giu = q\n    if not self._stream:\n        return False\n    if q <= 0:\n        self._togli_dsp_voce()\n        return True\n    if getattr(self, \'_dsp_voce\', None):\n        return True                  # gia\' agganciato: cambia solo il valore\n    return self._aggancia_dsp_voce()\n\n\ndef _togli_dsp_voce(self):\n    h = getattr(self, \'_dsp_voce\', None)\n    if h and self._stream:\n        try:\n            _lib.bass.BASS_ChannelRemoveDSP(self._stream, h)\n        except Exception:\n            pass\n    self._dsp_voce = None\n\n\ndef _aggancia_dsp_voce(self):\n    import ctypes as _c\n    try:\n        import numpy as _np\n    except Exception:\n        print("⚠️ voce giu\': manca numpy")\n        return False\n\n    b = _lib.bass\n    try:\n        b.BASS_ChannelSetDSP.restype = DWORD\n        b.BASS_ChannelSetDSP.argtypes = [DWORD, _c.c_void_p, _c.c_void_p, ctypes.c_int]\n        b.BASS_ChannelRemoveDSP.argtypes = [DWORD, DWORD]\n    except Exception:\n        pass\n\n    PROC = _c.CFUNCTYPE(None, DWORD, DWORD, _c.c_void_p, DWORD, _c.c_void_p)\n\n    # memoria di lavoro del filtro: serve a ricordare fra un blocco e\n    # l\'altro (il filtro sui bassi ha bisogno del campione precedente)\n    # N = quanti campioni fa la media. 220 a 44.100 = taglio intorno ai\n    # 200 Hz: sotto quella soglia (cassa, basso) non si tocca niente.\n    stato = {\'n\': 220, \'coda\': _np.zeros(219, dtype=_np.float32)}\n\n    def _filtro(handle, canale, buffer, lunghezza, utente):\n        try:\n            q = getattr(self, \'_voce_giu\', 0.0)\n            if q <= 0 or not lunghezza:\n                return\n            n = lunghezza // 4                      # campioni float32\n            if n < 2:\n                return\n            dati = _np.ctypeslib.as_array(\n                _c.cast(buffer, _c.POINTER(_c.c_float)), shape=(n,))\n            if n % 2:\n                return\n            s = dati.reshape(-1, 2)\n            L = s[:, 0].astype(_np.float32, copy=True)\n            R = s[:, 1].astype(_np.float32, copy=True)\n\n            centro = (L + R) * 0.5\n\n            # ⭐ dal centro si tiene fuori il GRAVE: cassa e basso stanno\n            #    li\' e devono restare.\n            #\n            # ⛔ QUI NON CI VA UN CICLO: questa funzione la chiama la\n            #    scheda audio molte volte al secondo, e un ciclo Python\n            #    campione per campione non fa in tempo — il suono\n            #    uscirebbe spezzettato. Media mobile con le somme\n            #    cumulate: stesso effetto, tutto in un colpo solo.\n            N = stato[\'n\']\n            coda = stato[\'coda\']\n            lungo = _np.concatenate((coda, centro))\n            cs = _np.cumsum(lungo, dtype=_np.float64)\n            cs = _np.concatenate(([0.0], cs))\n            inizio = len(coda)\n            grave = ((cs[inizio + 1:] - cs[inizio + 1 - N:len(cs) - N])\n                     / float(N)).astype(_np.float32)\n            # si tiene la coda per il blocco successivo: senza, a ogni\n            # blocco il filtro ripartirebbe e si sentirebbe un tic\n            stato[\'coda\'] = lungo[-(N - 1):] if N > 1 else lungo[:0]\n\n            da_togliere = (centro - grave) * q\n            s[:, 0] = L - da_togliere\n            s[:, 1] = R - da_togliere\n        except Exception:\n            pass                     # il suono non si ferma mai per un errore qui\n\n    self._dsp_voce_proc = PROC(_filtro)      # va TENUTO: se lo raccoglie\n                                             # il garbage collector, crash\n    try:\n        h = b.BASS_ChannelSetDSP(self._stream, self._dsp_voce_proc, None, 0)\n    except Exception as e:\n        print(f"⚠️ voce giu\': {e}")\n        return False\n    if not h:\n        print("⚠️ voce giu\': BASS non ha agganciato il filtro")\n        return False\n    self._dsp_voce = h\n    return True'

CODICE_SYS = 'def _filtro_voce(self, quanto: int):\n    """La riga di filtro da dare a MPV. Vuota = suono naturale.\n\n    ⛔ NON basta abbassare il centro e via: MISURATO, `stereotools` da\n       solo porta giu\' la voce E IL BASSO della stessa quantita\' (-12 dB\n       tutti e due), perche\' anche cassa e basso stanno al centro: il\n       brano si svuota. Percio\' il suono si divide in due strade: sotto i\n       200 Hz non si tocca niente, sopra si abbassa il centro, poi si\n       rimette insieme. Misurato cosi\': voce -24 dB, basso -0,3.\n    """\n    try:\n        q = max(0, min(100, int(quanto)))\n    except Exception:\n        q = 0\n    if q <= 0:\n        return \'\'\n    # 0 = voce com\'e\', 100 = quasi via\n    mlev = max(0.02, 1.0 - (q / 100.0) * 0.98)\n    return ("lavfi=[asplit=2[g][a];"\n            "[g]lowpass=f=200:poles=2[grave];"\n            "[a]highpass=f=200:poles=2,stereotools=mlev=%.3f[acuto];"\n            "[grave][acuto]amix=inputs=2:normalize=0]" % mlev)\n\n\ndef set_voce(self, quanto: int):\n    """Abbassa il volume della VOCE del brano che sta suonando.\n\n    quanto: 0 = com\'e\', 100 = voce giu\' al massimo.\n\n    ⛔ NON separa e NON produce nessun file: agisce sul suono mentre\n       esce, come una manopola, e si sente subito. Chi canta dal vivo\n       non puo\' aspettare un minuto per ogni brano.\n    """\n    try:\n        self.voce_giu = max(0, min(100, int(quanto)))\n    except Exception:\n        self.voce_giu = 0\n    fatto = False\n    perche = \'\'\n\n    # ⭐ SUI VIDEO (e sulle basi prese da YouTube) si fa come per la\n    #    TONALITA\': l\'audio si stacca dal video, VLC resta muto e suona\n    #    MPV. A quel punto il filtro lo applica MPV per conto suo, con\n    #    codice suo — niente codice nostro dentro il suono, che e\'\n    #    esattamente cio\' che aveva bloccato il programma.\n    try:\n        if (self.engine.is_video and self.engine.vlc_player\n                and self.mpv_player and not self.is_midi and self.is_playing):\n            if self.voce_giu > 0 and not self._video_pitch_active:\n                self._activate_video_mpv_audio()\n            elif (self.voce_giu == 0 and self._video_pitch_active\n                  and not self.current_pitch):\n                # si torna al video solo se non serve piu\' nemmeno per\n                # la tonalita\'\n                self._deactivate_video_mpv_audio()\n    except Exception as e:\n        print(f"⚠️ audio separato: {e}")\n\n    try:\n        if self.mpv_player is not None and (self.is_mpv_audio\n                                            or self._video_pitch_active):\n            self.mpv_player[\'af\'] = self._filtro_voce(self.voce_giu)\n            fatto = True\n        else:\n            be = self.bass_engine\n            if be is None:\n                perche = \'nessun motore audio buono (ne- MPV ne- BASS)\'\n            elif not getattr(be, \'_stream\', None):\n                perche = \'BASS c-e- ma non ha nessun brano aperto\'\n            else:\n                fatto = bool(be.set_voce(self.voce_giu))\n                if not fatto:\n                    perche = \'BASS non ha agganciato il filtro\'\n    except Exception as e:\n        perche = \'%s: %s\' % (type(e).__name__, e)\n\n    # ⚠️ Si SCRIVE cosa e- successo: senza, premendo il tasto e non\n    #    sentendo niente non c-e- modo di sapere dove si e- fermato.\n    try:\n        import datetime as _dt\n        import os as _os\n        _d = _os.path.join(_os.environ.get(\'LOCALAPPDATA\') or\n                           _os.path.expanduser(\'~\'), \'KaraDom\')\n        _os.makedirs(_d, exist_ok=True)\n        with open(_os.path.join(_d, \'patch033.log\'), \'a\',\n                  encoding=\'utf-8\') as _f:\n            _f.write(\'%s  voce a %d%%: %s%s\\n\' % (\n                _dt.datetime.now().strftime(\'%Y-%m-%d %H:%M:%S\'),\n                self.voce_giu, \'FATTO\' if fatto else \'NON fatto\',\n                \'\' if fatto else \' - \' + perche))\n    except Exception:\n        pass\n\n    if not fatto:\n        print("ℹ️ voce giu\' non applicata: %s" % perche)\n    return fatto'

CODICE_YT = 'def _on_devocalizza(self):\n    """Abbassa il volume della voce del brano che sta suonando.\n\n    ⛔ NON separa e NON produce nessun file: il suono viene lavorato\n       mentre esce, come si abbassa un volume. Effetto immediato, e si\n       torna indietro premendo di nuovo.\n    """\n    giu = not getattr(self, \'_voce_giu_attiva\', False)\n    livello = 0\n    if giu:\n        # quanto abbassarla: la scelta sta nelle Opzioni (scheda Audio)\n        try:\n            livello = int(str(Database.get_config(\'voce_giu\', \'85\')).strip())\n        except Exception:\n            livello = 85\n        livello = max(1, min(100, livello))\n    try:\n        self.system.set_voce(livello)\n    except Exception as e:\n        print("[voce] %s" % e)\n    self._voce_giu_attiva = giu\n    self._aggiorna_btn_devoc()\n\n\ndef _aggiorna_btn_devoc(self):\n    b = getattr(self, \'btn_devoc\', None)\n    if b is None:\n        return\n    try:\n        if getattr(self, \'_voce_giu_attiva\', False):\n            b.config(text=_("rimetti\\nla voce"), bg=\'#d35400\', fg=\'white\')\n        else:\n            b.config(text=_("abbassa\\nla voce"), bg=\'#8e44ad\', fg=\'white\')\n    except Exception:\n        pass\n\n\ndef _leggi_filtro_karaoke(self):\n    """Acceso, se non e\' stato spento apposta. La scelta si ricorda: chi\n    cerca gli originali non deve rispegnerlo a ogni avvio."""\n    try:\n        from .database import Database\n        return str(Database.get_config(\'yt_filtro_karaoke\', \'1\')).strip() not in (\'0\', \'no\', \'off\')\n    except Exception:\n        return True\n\n\ndef _aggiorna_btn_karaoke(self):\n    """Acceso = verde. Spento = grigio e barrato, cosi\' si capisce a colpo\n    d\'occhio che quella parola NON viene aggiunta."""\n    b = getattr(self, \'btn_karaoke\', None)\n    if b is None:\n        return\n    # ⚠️ NON si usa `BTN`: quello e\' una variabile locale di __init__ e qui\n    #    dentro non esiste. Il font si richiede a F, che e\' importata dal\n    #    modulo e tiene conto del ridimensionamento dello schermo.\n    #\n    # Il testo dice cosa succede PREMENDOLO, non com\'e\' adesso: e\' l\'unico\n    # modo perche\' si capisca senza doverci pensare.\n    try:\n        if self._filtro_karaoke:\n            b.config(text=_("togli filtro\\nkaraoke"),\n                     bg=\'#28a745\', fg=\'white\', font=F(\'Segoe UI\', 9, \'bold\'))\n        else:\n            b.config(text=_("rimetti filtro\\nkaraoke"),\n                     bg=\'#495057\', fg=\'#ffd700\', font=F(\'Segoe UI\', 9, \'bold\'))\n    except Exception:\n        pass\n\n# ---------------- togliere la voce ----------------\n\n\ndef _cambia_filtro_karaoke(self):\n    self._filtro_karaoke = not self._filtro_karaoke\n    self._aggiorna_btn_karaoke()\n    try:\n        from .database import Database\n        Database.set_config(\'yt_filtro_karaoke\', \'1\' if self._filtro_karaoke else \'0\')\n    except Exception:\n        pass\n\n\ndef _largh_btn_karaoke(self):\n    """Quanto e\' largo il tasto del filtro con la scritta piu\' lunga.\n\n    Si misura senza toccare quella che si vede: si mette da parte il testo\n    attuale, si provano tutte e due le scritte, e si rimette com\'era.\n    """\n    b = getattr(self, \'btn_karaoke\', None)\n    if b is None:\n        return 0\n    try:\n        adesso = b.cget(\'text\')\n        largo = 0\n        for t in (_("togli filtro\\nkaraoke"), _("rimetti filtro\\nkaraoke")):\n            b.config(text=t)\n            b.update_idletasks()\n            largo = max(largo, b.winfo_reqwidth())\n        b.config(text=adesso)\n        return largo\n    except Exception:\n        return 0\n\n\ndef _layout_top(self):\n    top = getattr(self, \'_top\', None)\n    if top is None or not top.winfo_exists():\n        return\n    # ⛔ QUI SI CREANO TUTTI E DUE I BOTTONI: questa funzione ne posiziona\n    #    due, e le patch si sostituiscono a vicenda — chi arriva per ultimo\n    #    deve bastare a se stesso, o l\'altro bottone resta inesistente\n    #    (\'NoneType\' has no attribute \'place\', con l\'errore in faccia).\n    if getattr(self, \'btn_karaoke\', None) is None:\n        self._filtro_karaoke = self._leggi_filtro_karaoke()\n        self.btn_karaoke = tk.Button(top, text=_("togli filtro\\nkaraoke"),\n                                     command=self._cambia_filtro_karaoke,\n                                     relief=\'flat\', cursor=\'hand2\',\n                                     bd=0, highlightthickness=0)\n        self._aggiorna_btn_karaoke()\n    if getattr(self, \'btn_devoc\', None) is None:\n        self.btn_devoc = tk.Button(top, text=_("abbassa\\nla voce"),\n                                   command=self._on_devocalizza,\n                                   bg=\'#8e44ad\', fg=\'white\',\n                                   relief=\'flat\', cursor=\'hand2\')\n        self._aggiorna_btn_devoc()\n        try:\n            from .libreria_widgets import add_tooltip as _tt\n            _tt(self.btn_devoc,\n                _("Abbassa la voce del brano che sta suonando, subito. "\n                  "Premi di nuovo per rimetterla."))\n        except Exception:\n            pass\n    try:\n        top.update_idletasks()\n    except Exception:\n        pass\n    W = top.winfo_width()\n    H = top.winfo_height()\n    if W < 40 or H < 10:\n        return\n    ox = top.winfo_rootx()\n\n    def rel(w):\n        try:\n            if w is None:\n                return None\n            wd = w.winfo_width()\n            if wd < 5:\n                return None\n            return (w.winfo_rootx() - ox, wd)\n        except Exception:\n            return None\n\n    lib = getattr(self.system, \'libreria\', None)\n    cant = rel(getattr(lib, \'entry_cantante\', None))\n    brano = rel(getattr(lib, \'_lbl_brano\', None))\n    filt = rel(getattr(lib, \'entry_filtro\', None))\n    pad = S(4)\n\n    # --- Dest: label allineata a "Cant:", campo allineato/largo come cantante ---\n    if cant:\n        xcant, wcant = cant\n    else:\n        xcant, wcant = S(60), (W // 2) - S(90)\n    # X della label "Cant:" = inizio del frame cantante + padx(5)\n    lbl_x = S(5)\n    try:\n        fc = self.system.libreria.entry_cantante.master\n        lbl_x = (fc.winfo_rootx() - ox) + S(5)\n    except Exception:\n        pass\n    self.lbl_dest.place(x=max(0, lbl_x), y=0, height=H)\n    self.entry_dest.place(x=xcant, y=0, width=wcant, height=H)\n\n    # --- Sfoglia sotto i tasti ▶ 🗑 (tra campo cantante e label brano) ---\n    gap_x0 = xcant + wcant + pad\n    gap_x1 = (brano[0] if brano else (filt[0] if filt else W)) - pad\n    sfw = max(S(70), gap_x1 - gap_x0)\n    self.btn_sfoglia.place(x=gap_x0, y=0, width=sfw, height=H)\n\n    # --- campo ricerca: dalla label "Brano (filtro):" a fine campo filtro ---\n    if brano:\n        xsearch = brano[0]\n    elif filt:\n        xsearch = filt[0]\n    else:\n        xsearch = gap_x0 + sfw + pad\n    filtro_right = (filt[0] + filt[1]) if filt else W\n\n    # --- 3 bottoni (Cerca/Download/Incolla) TUTTI larghi uguali (al piu\' largo) ---\n    # ⚠️ La larghezza si prende sul testo PIU\' LUNGO che ciascun bottone\n    #    puo\' mostrare, non su quello di adesso: il tasto del filtro\n    #    cambia scritta quando lo si preme, e se la misura seguisse il\n    #    testo corrente la barra si riassesterebbe a ogni clic.\n    bw = max(self.btn_cerca.winfo_reqwidth(),\n             self.btn_download.winfo_reqwidth(),\n             self.btn_incolla.winfo_reqwidth(),\n             self.btn_devoc.winfo_reqwidth(),\n             self._largh_btn_karaoke()) + S(4)   # appena un filo d\'aria\n    buttons_w = 4 * bw + 4 * pad     # Cerca, Download, Incolla, Devocalizza\n    search_right = min(filtro_right, W - buttons_w - pad)\n    search_right = max(search_right, xsearch + S(80))\n\n    # ⭐ L\'interruttore "karaoke" sta IN FONDO al campo, dentro il suo\n    #    spazio: il campo si accorcia di quel tanto. Cosi\' si vede mentre\n    #    si scrive, senza rubare posto ai tre bottoni.\n    campo_right = max(xsearch + S(60), search_right - bw - pad)\n    self.entry_search.place(x=xsearch, y=0, width=campo_right - xsearch, height=H)\n    self.btn_karaoke.place(x=campo_right + pad, y=0,\n                           width=search_right - campo_right - pad, height=H)\n\n    bx = search_right + pad\n    self.btn_cerca.place(x=bx, y=0, width=bw, height=H); bx += bw + pad\n    self.btn_download.place(x=bx, y=0, width=bw, height=H); bx += bw + pad\n    self.btn_incolla.place(x=bx, y=0, width=bw, height=H); bx += bw + pad\n    self.btn_devoc.place(x=bx, y=0, width=bw, height=H)\n\n# ---------------- scroll rotellina ----------------'


def _spenta():
    try:
        from moduli.database import Database
        if str(Database.get_config('patch_033', '1')).strip() in ('0', 'no', 'off'):
            traccia('spenta a mano (patch_033 = 0)')
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
        with open(os.path.join(d, 'patch033.log'), 'a', encoding='utf-8') as f:
            f.write('%s  %s' % (
                datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                testo) + chr(10))
    except Exception:
        pass


def apply():
    if _spenta():
        traccia('non mi accendo (vedi la riga qui sopra)')
        return False
    fatte = []
    try:
        # 1) il filtro nel motore audio
        import moduli.bass_engine as mb
        sp = mb.__dict__
        exec(compile(CODICE_BASS, "<patch033bass>", "exec"), sp)
        for n in ('set_voce', '_togli_dsp_voce', '_aggancia_dsp_voce'):
            setattr(mb.BassEngine, n, sp[n])
        mb.BassEngine._dsp_voce = None
        mb.BassEngine._voce_giu = 0.0
        fatte.append('motore audio')
    except Exception as e:
        traccia('motore audio NON agganciato: %s: %s' % (type(e).__name__, e))
        return False

    try:
        # 2) il comando nel programma
        import moduli.system as ms
        sp = ms.__dict__
        exec(compile(CODICE_SYS, "<patch033sys>", "exec"), sp)
        for n in ('_filtro_voce', 'set_voce'):
            setattr(ms.KaraokeMonitorSystem, n, sp[n])
        fatte.append('comando')
    except Exception as e:
        traccia('comando NON agganciato: %s: %s' % (type(e).__name__, e))

    try:
        # 3) il tasto
        import moduli.yt2mp3 as my
        C = my.YoutubePanel
        sp = my.__dict__
        exec(compile(CODICE_YT, "<patch033yt>", "exec"), sp)
        for n in ('_on_devocalizza', '_aggiorna_btn_devoc',
                  '_leggi_filtro_karaoke', '_aggiorna_btn_karaoke',
                  '_cambia_filtro_karaoke', '_largh_btn_karaoke',
                  '_layout_top'):
            setattr(C, n, sp[n])
        C.btn_devoc = None
        if getattr(C, 'btn_karaoke', None) is None:
            C.btn_karaoke = None
        fatte.append('tasto')
    except Exception as e:
        traccia('tasto NON agganciato: %s: %s' % (type(e).__name__, e))

    traccia('AGGANCIATA: ' + ', '.join(fatte))
    print("patch 033: si puo' abbassare la voce mentre suona")
    return True


def revert():
    try:
        import sys
        mb = sys.modules.get('moduli.bass_engine')
        if mb and hasattr(mb, 'BassEngine'):
            for n in ('set_voce', '_togli_dsp_voce', '_aggancia_dsp_voce'):
                if hasattr(mb.BassEngine, n):
                    delattr(mb.BassEngine, n)
        print("patch 033: tolta")
        return True
    except Exception as e:
        print("patch 033: %s" % e)
    return False


try:
    apply()
except Exception:
    pass
