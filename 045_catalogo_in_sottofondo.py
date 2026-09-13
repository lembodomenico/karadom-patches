# 045 - catalogo in sottofondo

import sys


def traccia(testo):
    riga = '[045] %s' % testo
    try:
        print(riga)
    except Exception:
        pass
    try:
        import datetime
        import os
        d = os.path.join(os.environ.get('LOCALAPPDATA') or
                         os.path.expanduser('~'), 'KaraDom')
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, 'patch045.log'), 'a', encoding='utf-8') as f:
            f.write('%s  %s%s' % (
                datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                riga, chr(10)))
    except Exception:
        pass


CODICE_SFONDO = '# -*- coding: utf-8 -*-\n"""Il catalogo remoto lavora IN SOTTOFONDO.\n\n"se riusciamo a farglielo fare anche in background sarebbe favoloso" e\n"chiuderla non lo ferma ma il tasto ferma si\'" (utente, 13-09).\n\nIl lavoro (leggere la cartella, controllare i nomi — prima nei nostri\ndatabase, poi fuori — e mandare i brani al catalogo) prima viveva DENTRO la\nfinestra delle Opzioni e scriveva direttamente sulla sua etichetta: chiudendo\nla finestra andava a sbattere. Ora vive qui:\n\n  * il lavoro NON tocca nessuna finestra: aggiorna `LAVORO` (e `STATO` del\n    controllo dei nomi), e chi vuole mostrarlo — le Opzioni, la barra in basso\n    — lo RILEGGE da se\' ogni mezzo secondo. Se una delle due non c\'e\' piu\',\n    non succede niente;\n  * lo ferma SOLO il tasto Ferma (`ferma()`), e quello e\' una decisione: il\n    promemoria si cancella e al prossimo avvio non riparte;\n  * se invece il programma si chiude a lavoro in corso, il promemoria resta\n    (`%LOCALAPPDATA%\\\\KaraDom\\\\catalogo_in_corso.json`) e al prossimo avvio\n    riparte da solo (`riprendi_se_serve`), dopo qualche secondo per non\n    rallentare l\'apertura. Non si perde niente: i nomi controllati stanno in\n    memoria, i brani mandati in `catalogo_mandati.txt`.\n"""\nimport json\nimport os\nimport threading\nimport time\n\ntry:\n    from .i18n import _\nexcept Exception:                                   # pragma: no cover\n    def _(s):\n        return s\n\nLAVORO = {\'acceso\': False, \'fermo\': False, \'fase\': \'\', \'fine\': \'\',\n          \'colore\': \'#ffffff\', \'partito\': 0.0, \'finito_alle\': 0.0,\n          \'conto_nomi\': {}, \'invio\': {}}\n\nGIRA = (\'|\', \'/\', \'-\', \'\\\\\')\n\n\n# ------------------------------ il promemoria ------------------------------\n\ndef _promemoria():\n    d = os.path.join(os.environ.get(\'LOCALAPPDATA\') or\n                     os.path.expanduser(\'~\'), \'KaraDom\')\n    try:\n        os.makedirs(d, exist_ok=True)\n    except Exception:\n        pass\n    return os.path.join(d, \'catalogo_in_corso.json\')\n\n\ndef _segna(cartella, incrociato):\n    try:\n        with open(_promemoria(), \'w\', encoding=\'utf-8\') as f:\n            json.dump({\'cartella\': cartella, \'incrociato\': bool(incrociato),\n                       \'quando\': time.time()}, f)\n    except Exception:\n        pass\n\n\ndef _dimentica():\n    try:\n        os.remove(_promemoria())\n    except Exception:\n        pass\n\n\ndef promemoria():\n    """Il lavoro rimasto a meta\' l\'ultima volta, o None."""\n    try:\n        with open(_promemoria(), encoding=\'utf-8\') as f:\n            d = json.load(f)\n        return d if d.get(\'cartella\') else None\n    except Exception:\n        return None\n\n\n# -------------------------------- il lavoro --------------------------------\n\ndef in_corso():\n    return bool(LAVORO[\'acceso\'])\n\n\ndef ferma():\n    """Il tasto Ferma. ⚠️ E\' una decisione dell\'utente: il promemoria si\n    cancella, e al prossimo avvio il lavoro NON riparte da solo."""\n    LAVORO[\'fermo\'] = True\n    _dimentica()\n\n\ndef avvia(cartella, incrociato=True):\n    """Parte, se non sta gia\' lavorando. Torna True se e\' partito adesso."""\n    if LAVORO[\'acceso\']:\n        return False\n    LAVORO.update({\'acceso\': True, \'fermo\': False, \'fase\': \'leggo\',\n                   \'fine\': \'\', \'colore\': \'#ffffff\', \'partito\': time.time(),\n                   \'finito_alle\': 0.0, \'conto_nomi\': {}, \'invio\': {}})\n    _segna(cartella, incrociato)\n    threading.Thread(target=_lavora, args=(cartella, incrociato),\n                     daemon=True, name=\'catalogo-sottofondo\').start()\n    return True\n\n\ndef _fine(testo, colore, dimentica=True):\n    LAVORO.update({\'fine\': testo, \'colore\': colore, \'finito_alle\': time.time()})\n    if dimentica:\n        _dimentica()\n\n\ndef _lavora(cartella, incrociato):\n    def fermati():\n        return LAVORO[\'fermo\']\n\n    try:\n        from .catalogo_remoto import leggi_cartella, manda\n        scartati = []\n        if incrociato:\n            from . import catalogo_conferma as cc\n            LAVORO[\'fase\'] = \'nomi\'\n\n            def _chiedendo(fatti, totali, conto):\n                LAVORO[\'conto_nomi\'] = dict(conto)\n\n            # il catalogo si riempie SUBITO: i nomi controllati partono a\n            # blocchi mentre il controllo va avanti\n            brani, scartati, conto_c = cc.leggi_cartella_confermata(\n                cartella, avviso=_chiedendo, fermati=fermati,\n                a_blocchi=lambda righe: manda(righe, fermati=fermati))\n            if LAVORO[\'fermo\']:\n                return _fine(_("Fermato: i nomi già controllati restano sul "\n                               "computer, ripremendo riparte da lì."),\n                             \'#ffcc00\')\n        else:\n            brani, scartati = leggi_cartella(cartella)\n        if not brani:\n            return _fine(_("Nessun brano: nei nomi dei file manca il trattino "\n                           "fra artista e titolo"), \'#ff6666\')\n        LAVORO[\'fase\'] = \'mando\'\n        LAVORO[\'invio\'] = {\'fatti\': 0, \'totali\': len(brani), \'conto\': {},\n                           \'partito\': time.time()}\n\n        def _avanti(fatti, totali, conto):\n            LAVORO[\'invio\'].update({\'fatti\': fatti, \'totali\': totali or 1,\n                                    \'conto\': dict(conto)})\n\n        conto = manda(brani, avviso=_avanti, fermati=fermati)\n        if LAVORO[\'fermo\']:\n            return _fine(_("Fermato: %d brani sono già arrivati e non verranno "\n                           "rimandati. Ripremendo riparte da lì.")\n                         % (conto[\'inseriti\'] + conto[\'gia_presenti\']),\n                         \'#ffcc00\')\n        testo = _("Fatto: %d nuovi, %d c\'erano gia\'. Nel catalogo ora "\n                  "ci sono %d brani.") % (conto[\'inseriti\'],\n                                          conto[\'gia_presenti\'],\n                                          conto[\'totale\'])\n        if conto.get(\'saltati\'):\n            testo += _("  (%d già mandati in un giro precedente)") \\\n                % conto[\'saltati\']\n        if scartati:\n            testo += _("  (%d file saltati: nome senza trattino)") \\\n                % len(scartati)\n        _fine(testo, \'#66ff99\')\n    except Exception as e:\n        # ⚠️ un errore (rete, server) NON cancella il promemoria: al prossimo\n        #    avvio si riprova da dove si era arrivati\n        _fine(_("Non ha funzionato: %s") % str(e)[:90], \'#ff6666\',\n              dimentica=False)\n    finally:\n        LAVORO[\'acceso\'] = False\n\n\n# ------------------------------- le scritte --------------------------------\n\ndef _stato_nomi():\n    try:\n        from . import catalogo_conferma as cc\n        return cc.STATO\n    except Exception:\n        return {}\n\n\ndef riga(n=0):\n    """`(testo, colore)` per la riga delle Opzioni, adesso."""\n    if not LAVORO[\'acceso\']:\n        return LAVORO[\'fine\'], LAVORO[\'colore\']\n    g = GIRA[n % 4]\n    if LAVORO[\'fase\'] == \'mando\':\n        v = LAVORO[\'invio\']\n        c = v.get(\'conto\') or {}\n        passato = time.time() - v.get(\'partito\', time.time())\n        fatti, totali = v.get(\'fatti\', 0), v.get(\'totali\', 1)\n        manca = \'\'\n        if fatti > 300 and passato > 4 and totali > fatti:\n            resta = (totali - fatti) * (passato / fatti)\n            manca = (_(" — mancano %d min") % (resta / 60) if resta >= 90\n                     else _(" — mancano %d s") % resta)\n        return (_("%s Mando: %d su %d brani — richiesta %d di %d, "\n                  "%d in volo — nuovi %d — %d s%s")\n                % (g, fatti, totali, c.get(\'partiti\', 0), c.get(\'gruppi\', 0),\n                   c.get(\'in_volo\', 0), c.get(\'inseriti\', 0), passato, manca),\n                \'#ffffff\')\n    s = _stato_nomi()\n    c = LAVORO[\'conto_nomi\']\n    passato = time.time() - LAVORO[\'partito\']\n    fatti, totali = s.get(\'fatti\', 0), s.get(\'totali\', 0)\n    if not totali:\n        return (_("%s Leggo la cartella: %d file — %d s")\n                % (g, s.get(\'letti\', 0), passato), \'#ffffff\')\n    if s.get(\'fase\') == \'nostri\':\n        return (_("%s Nei nostri database: %d su %d nomi "\n                  "— riconosciuti %d — %d s")\n                % (g, s.get(\'nostri_visti\', 0), s.get(\'nostri_da\', 0),\n                   s.get(\'nostri_ok\', 0), passato), \'#ffffff\')\n    manca = \'\'\n    if fatti > 20 and passato > 10 and totali > fatti:\n        resta = (totali - fatti) * (passato / fatti)\n        manca = (_(" — mancano %d h") % (resta / 3600) if resta >= 5400\n                 else _(" — mancano %d min") % max(1, resta / 60))\n    testo = (_("%s Nomi: %d su %d — riconosciuti %d, già noti %d — %d s%s")\n             % (g, fatti, totali, c.get(\'confermati\', 0),\n                c.get(\'da_memoria\', 0), passato, manca))\n    if s.get(\'mandati\'):\n        testo += _(" — nel catalogo %d") % s[\'mandati\']\n    if s.get(\'ora\'):\n        testo += \'\\n\' + _("ora: %s") % s[\'ora\'][:70]\n    if s.get(\'genius_spento\'):\n        testo += \'  \' + _("(Genius ha finito la quota: solo LRCLIB)")\n    return testo, \'#ffffff\'\n\n\ndef riga_corta():\n    """Una riga sola, corta, per la barra in basso. \'\' se non c\'e\' niente da\n    dire (e allora la scritta sparisce)."""\n    if not LAVORO[\'acceso\']:\n        # l\'esito resta visibile un minuto, poi si toglie di mezzo\n        if LAVORO[\'fine\'] and time.time() - LAVORO[\'finito_alle\'] < 60:\n            return (_("Catalogo: %s") % LAVORO[\'fine\'].split(\'.\')[0])[:90]\n        return \'\'\n    if LAVORO[\'fase\'] == \'mando\':\n        v = LAVORO[\'invio\']\n        return _("Catalogo: mando %d su %d") % (v.get(\'fatti\', 0),\n                                                v.get(\'totali\', 0))\n    s = _stato_nomi()\n    if not s.get(\'totali\'):\n        return _("Catalogo: leggo la cartella (%d file)") % s.get(\'letti\', 0)\n    if s.get(\'fase\') == \'nostri\':\n        return _("Catalogo: nostri database %d su %d") % (\n            s.get(\'nostri_visti\', 0), s.get(\'nostri_da\', 0))\n    testo = _("Catalogo: nomi %d su %d") % (s.get(\'fatti\', 0), s[\'totali\'])\n    if s.get(\'mandati\'):\n        testo += _(" — nel catalogo %d") % s[\'mandati\']\n    return testo\n\n\n# --------------------------- la barra e l\'avvio ----------------------------\n\ndef aggancia_barra(contenitore):\n    """Una riga piccola in fondo a `contenitore` — il riquadro informazioni\n    della barra in basso, sotto cantante e brano — che si ridisegna da sola\n    ogni secondo e SPARISCE quando non c\'e\' niente da dire.\n\n    ⚠️ Nel riquadro informazioni e non nell\'angolo della barra: a destra ci\n       sono i tasti (SCA, PLA, YTD...) e non si sa fin dove arrivano; una\n       scritta li\' ne coprirebbe uno. E la barra dei comandi a schermo intero\n       si nasconde: la scritta non finisce mai sullo schermo del pubblico.\n    """\n    import tkinter as tk\n    try:\n        fondo = contenitore.cget(\'bg\')\n    except Exception:\n        fondo = \'#060c1c\'\n    lbl = tk.Label(contenitore, text=\'\', bg=fondo, fg=\'#ffffff\',\n                   font=(\'Segoe UI\', 8), bd=0, padx=0, pady=0, anchor=\'w\')\n    visibile = [False]\n\n    def _batti():\n        try:\n            testo = riga_corta()\n            if testo:\n                lbl.config(text=testo, fg=LAVORO[\'colore\']\n                           if not LAVORO[\'acceso\'] else \'#ffffff\')\n                if not visibile[0]:\n                    lbl.pack(anchor=\'w\', fill=\'x\', pady=(2, 0))\n                    visibile[0] = True\n            elif visibile[0]:\n                lbl.pack_forget()\n                visibile[0] = False\n            contenitore.after(1000, _batti)\n        except Exception:\n            pass                        # la barra non c\'e\' piu\': basta\n\n    contenitore.after(1000, _batti)\n    return lbl\n\n\ndef riprendi_se_serve(root, dopo_ms=20000):\n    """Se l\'ultima volta il programma si e\' chiuso a lavoro in corso, riparte\n    da solo. ⚠️ Dopo qualche secondo: all\'avvio il programma ha gia\' tanto da\n    fare, e il catalogo puo\' aspettare."""\n    p = promemoria()\n    if not p or LAVORO[\'acceso\']:\n        return False\n    if not os.path.isdir(p.get(\'cartella\', \'\')):\n        _dimentica()\n        return False\n\n    def _parti():\n        if not LAVORO[\'acceso\']:\n            avvia(p[\'cartella\'], p.get(\'incrociato\', True))\n\n    try:\n        root.after(int(dopo_ms), _parti)\n        return True\n    except Exception:\n        return False\n'

CODICE_OPZ = 'def _popola_catalogo_remoto(self):\n    """Legge la cartella delle basi e manda i brani al catalogo remoto.\n\n    ⚠️ Il lavoro gira in un filo suo: una cartella con migliaia di basi\n       tiene occupato qualche minuto, e la finestra deve restare viva e\n       dire a che punto e\'.\n    ⛔ Le password del database NON stanno qui: si passa dall\'API, che\n       controlla la licenza (vedi `catalogo_remoto.py`).\n    """\n    from . import catalogo_sfondo as _cs\n    cartella = self.entry_cartella_brani.get().strip()\n    if not cartella or not os.path.isdir(cartella):\n        messagebox.showwarning(_("Catalogo"),\n                               _("Scegli prima la cartella con le basi."),\n                               parent=self.window)\n        return\n    Database.set_config(\'catalogo_cartella\', cartella)\n    # la spunta del controllo incrociato (e si ricorda com\'era)\n    incrociato = True\n    try:\n        incrociato = bool(self.var_catalogo_conferma.get())\n        Database.set_config(\'catalogo_controllo_incrociato\',\n                            \'1\' if incrociato else \'0\')\n    except Exception:\n        pass\n    # ⭐⭐ IN SOTTOFONDO ("se riusciamo a farglielo fare anche in background\n    #    sarebbe favoloso"; "chiuderla non lo ferma ma il tasto ferma si\'"\n    #    — utente, 13-09). Il lavoro vive in `catalogo_sfondo`, non in\n    #    questa finestra: qui si fa solo partire, se non sta gia\' andando,\n    #    e poi si guarda a che punto e\'.\n    if not _cs.in_corso():\n        _cs.avvia(cartella, incrociato)\n    self._catalogo_segui()\n\ndef _catalogo_segui(self, n=0):\n    """Ridisegna la riga ogni mezzo secondo leggendo il lavoro in\n    sottofondo. Se la finestra si chiude, si smette di guardare e basta:\n    il lavoro va avanti per conto suo."""\n    from . import catalogo_sfondo as _cs\n    try:\n        testo, colore = _cs.riga(n)\n        self.lbl_catalogo.config(text=testo, fg=colore)\n        if _cs.in_corso():\n            self.window.after(500, self._catalogo_segui, n + 1)\n    except Exception:\n        pass\n\ndef _catalogo_ferma_ora(self):\n    """Il tasto Ferma: ferma il lavoro in sottofondo (non perde niente).\n\n    ⚠️ E\' una DECISIONE: il promemoria si cancella e al prossimo avvio il\n       lavoro NON riparte da solo ("chiuderla non lo ferma ma il tasto\n       ferma si\'" — utente, 13-09).\n    """\n    self._catalogo_fermo = True\n    try:\n        from . import catalogo_sfondo as _cs\n        _cs.ferma()\n    except Exception:\n        pass\n    try:\n        self.lbl_catalogo.config(text=_("Mi fermo…"), fg=\'#ffcc00\')\n    except Exception:\n        pass\n'

NOMI_OPZ = ('_popola_catalogo_remoto', '_catalogo_segui', '_catalogo_ferma_ora')

FATTO = {'barra': False, 'ripresa': False}


def _classe_opzioni():
    mo = sys.modules.get('moduli.opzioni')
    if mo is None:
        try:
            import moduli.opzioni as mo
        except Exception:
            return None, None
    for nome in dir(mo):
        o = getattr(mo, nome)
        if isinstance(o, type) and hasattr(o, '_popola_catalogo_remoto') \
                and hasattr(o, 'create_tab_database'):
            return mo, o
    return mo, None


def _sottofondo():
    m = sys.modules.get('moduli.catalogo_sfondo')
    if m is not None and hasattr(m, 'aggancia_barra'):
        return m
    import types
    import moduli
    m = types.ModuleType('moduli.catalogo_sfondo')
    m.__package__ = 'moduli'
    m.__file__ = '<patch045>'
    exec(compile(CODICE_SFONDO, '<patch045_sfondo>', 'exec'), m.__dict__)
    sys.modules['moduli.catalogo_sfondo'] = m
    setattr(moduli, 'catalogo_sfondo', m)
    return m


def _info(root):
    s = getattr(root, '_karadom_system', None)
    d = getattr(s, 'info_brano_ref', None)
    if isinstance(d, dict) and d.get('brano') is not None:
        return d
    import gc
    for o in gc.get_objects():
        if type(o) is dict and 'brano' in o and 'cantante' in o:
            b = o.get('brano')
            if hasattr(b, 'cget') and hasattr(b, 'master'):
                return o
    return None


def _riprendi(root, cs):
    if FATTO['ripresa']:
        return
    FATTO['ripresa'] = True
    try:
        if cs.riprendi_se_serve(root):
            traccia('lavoro rimasto a meta: riparte fra 20 secondi')
    except Exception as e:
        traccia('ripresa non riuscita: %s' % e)


def _cerca(root, cs, n):
    if FATTO['barra']:
        return
    try:
        if not root.winfo_exists():
            return
    except Exception:
        return
    d = _info(root)
    if d is not None:
        FATTO['barra'] = True
        try:
            cs.aggancia_barra(d['brano'].master)
            traccia('riga del catalogo sotto il brano')
        except Exception as e:
            traccia('riga non agganciata: %s' % e)
        _riprendi(root, cs)
        return
    if n < 20:
        try:
            root.after(3000, _cerca, root, cs, n + 1)
        except Exception:
            pass
    else:
        _riprendi(root, cs)


def _aggancia_avvio(cs):
    import tkinter
    vera = tkinter.Tk.mainloop
    if getattr(vera, '_s045', False):
        return

    def mainloop(self, n=0, _v=vera):
        if not FATTO['barra']:
            try:
                self.after(3000, _cerca, self, cs, 0)
            except Exception:
                pass
        return _v(self, n)

    mainloop._s045 = True
    tkinter.Tk.mainloop = mainloop
    try:
        r = tkinter._default_root
        if r is not None:
            r.after(3000, _cerca, r, cs, 0)
    except Exception:
        pass


def apply():
    try:
        mo, cls = _classe_opzioni()
        if cls is None:
            traccia('finestra delle opzioni non trovata')
            return False
        segui = vars(cls).get('_catalogo_segui')
        if segui is not None and not getattr(segui, '_s045', False):
            traccia('il programma lo fa gia da se')
            return True
        if getattr(cls._popola_catalogo_remoto, '_s045', False):
            return True
        cs = _sottofondo()
        sp = {}
        exec(compile(CODICE_OPZ, '<patch045_opz>', 'exec'), mo.__dict__, sp)
        for n in NOMI_OPZ:
            sp[n]._s045 = True
            setattr(cls, n, sp[n])
        vecchia = cls.create_tab_database
        if not getattr(vecchia, '_s045', False):
            def create_tab_database(self, *a, _v=vecchia, **k):
                r = _v(self, *a, **k)
                try:
                    if cs.in_corso() or cs.LAVORO.get('fine'):
                        self.window.after(200, self._catalogo_segui)
                except Exception:
                    pass
                return r

            create_tab_database._s045 = True
            cls.create_tab_database = create_tab_database
        _aggancia_avvio(cs)
        traccia('catalogo in sottofondo: chiudere le opzioni non lo ferma, '
                'il tasto Ferma si')
        return True
    except Exception as e:
        traccia('non agganciata: %s: %s' % (type(e).__name__, e))
        return False


def revert():
    return False


try:
    apply()
except Exception:
    pass
