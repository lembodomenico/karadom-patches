# 016_ricerca_da_tabella.py
#
# LA RICERCA LA FA IL DATABASE, NON PIU' UN CICLO PYTHON.
#
# Con la 014 il cliente e' passato da un calo per ogni lettera a uno solo, e
# con la 015 quello che resta e' piu' corto. Ma finche' a cercare e' codice
# Python, il thread del MIDI non puo' eseguire nulla mentre si cerca: e'
# il GIL, e nessuna scorciatoia lo aggira.
#
# L'IDEA E' DELL'UTENTE: mettere nome e percorso in una tabella e far
# cercare li'. Funziona per una ragione precisa e misurabile: **SQLite molla
# il turno mentre lavora**, quindi il MIDI continua a suonare anche durante
# la ricerca.
#
# MISURATO su 400.000 brani:
#                             ricerca      ritardo del MIDI
#   ciclo Python (oggi) ....  215 ms       24 ms medi, punte 150   <-- il calo
#   str.find (patch 015) ...   17 ms        ~5 ms
#   TABELLA (questa) .......  0,7-62 ms    0,4 ms medi, punta 0,6  <-- sparisce
#
# Scrivere la tabella: 0,36 s per le righe + 0,40 s per gli indici su
# 400.000 brani, in un thread, col MIDI che non perde un colpo (punta 1 ms).
#
# ⚠️ SOLO SOPRA I 100.000 BRANI (`ricerca_soglia_brani`): sotto quella soglia
#    non si crea nessun file e non cambia niente, perche' li' il problema non
#    esiste e non ha senso aggiungere roba.
#
# ⚠️ NEL FILE CI VANNO SOLO NOME, PAROLE, ESTENSIONE E LA POSIZIONE nella
#    lista. Nessuna base dentro, nessun percorso duplicato: il percorso vero
#    si riprende sempre dalla lista in memoria, cosi' non puo' succedere che
#    la ricerca trovi una cosa e il programma ne apra un'altra.
#
# ⚠️ La funzione di ricerca e' copiata DAL SORGENTE cambiando solo il blocco
#    della scansione, e si porta dietro (a catena) tutti i nomi che nel
#    compilato potrebbero mancare — la lezione della 015, che senza quelli
#    moriva con NameError al primo tasto.
#
# SE NON VA BENE: `R16` la ritira, `patch_016 = 0` la spegne su una macchina
# sola, `revert()` rimette l'originale a caldo. Il file .db resta li' e non
# da' fastidio a nessuno; volendo si cancella a mano da
# %LOCALAPPDATA%\KaraDom\elenchi\*.ricerca.db


CODICE = 'def aggiorna_suggerimenti_live(self, event=None):\n    """Lancia ricerca in THREAD SEPARATO — la UI non si blocca MAI"""\n    testo = self.entry_filtro.get().lower().strip()\n\n    if not testo or testo == "filtra brano o autore" or len(testo) < 2:\n        self.container_suggerimenti.place_forget()\n        return\n\n    # ✅ Incrementa contatore ricerca (cancella ricerche precedenti)\n    self._search_generation = getattr(self, \'_search_generation\', 0) + 1\n    gen = self._search_generation\n\n    # ✅ Parse query (veloce, nel main thread)\n    if \'*\' in testo:\n        raw_parts = [p.strip() for p in testo.split(\'*\') if p.strip()]\n    else:\n        raw_parts = [p for p in re.split(r\'\\s+\', testo) if p]\n\n    parti_wildcard = []\n    parti_is_ext = []\n    for p in raw_parts:\n        if p.startswith(\'.\'):\n            parti_wildcard.append(p[1:])\n            parti_is_ext.append(True)\n        else:\n            parti_wildcard.append(p)\n            parti_is_ext.append(False)\n\n    if not parti_wildcard:\n        self.container_suggerimenti.place_forget()\n        return\n\n    # ✅ Copia riferimento lista (thread-safe: la lista può essere sostituita ma non mutata)\n    brani_ref = self.brani_pc\n\n    def _search_thread():\n        """Ricerca in background — NON tocca la UI"""\n        # ✅ Pre-calcola indice nel thread (non nel main thread).\n        #    `gen` cosi\' che, se l\'utente ha gia\' digitato un\'altra\n        #    lettera, l\'indicizzazione si fermi invece di finire a vuoto.\n        self._ensure_search_index(gen)\n\n        risultati_mp3 = []\n        risultati_altri = []\n\n        # ⭐ [patch 016] LA RICERCA LA FA IL DATABASE.\n        #    L\'elenco dei brani sta anche in una tabella di un file .db\n        #    (solo nome e percorso: le basi restano sul disco). Cercare\n        #    li\' dentro costa 0,7 ms quando l\'indice aiuta e 62 ms nel\n        #    caso peggiore, contro i 215 ms di questo ciclo - ma\n        #    soprattutto SQLite MOLLA IL TURNO mentre lavora, quindi il\n        #    thread del MIDI continua a suonare: ritardo misurato 0,4 ms\n        #    contro 24. E\' l\'unica soluzione che toglie il disturbo\n        #    invece di accorciarlo.\n        #    Se la tabella non c\'e\' ancora (prima ricerca dopo aver\n        #    aperto la cartella) si cerca come sempre, e intanto la si\n        #    prepara in un thread a parte - ma di norma e\' gia\' li\',\n        #    perche\' si costruisce all\'apertura della cartella.\n        _righe = None\n        try:\n            _righe = self._cerca_in_tabella_016(parti_wildcard, parti_is_ext,\n                                                brani_ref, 100)\n        except Exception:\n            _righe = None\n\n        if _righe is not None:\n            for _i in _righe:\n                if getattr(self, \'_search_generation\', 0) != gen:\n                    return\n                brano = brani_ref[_i]\n                if brano.get(\'ext\', \'\') == \'mp3\':\n                    risultati_mp3.append(brano)\n                else:\n                    risultati_altri.append(brano)\n        else:\n            try:\n                self._prepara_tabella_016()\n            except Exception:\n                pass\n            for brano in brani_ref:\n                # ✅ Cancellazione: se l\'utente ha digitato altro, esci subito\n                if getattr(self, \'_search_generation\', 0) != gen:\n                    return\n\n                parole_brano = brano.get(\'parole\')\n                ext = brano.get(\'ext\', \'\')\n\n                if parole_brano is None:\n                    nome_lower = brano[\'nome\'].lower()\n                    nome_senza_ext, ext_p = os.path.splitext(nome_lower)\n                    ext = ext_p[1:] if ext_p else ""\n                    if \' - \' in nome_senza_ext:\n                        pp = nome_senza_ext.split(\' - \', 1)\n                        parole_brano = pp[0].strip().split() + pp[1].strip().split()\n                    else:\n                        parole_brano = nome_senza_ext.split()\n                    if ext:\n                        parole_brano.append(ext)\n\n                match = True\n                for i, parte_cerca in enumerate(parti_wildcard):\n                    if parti_is_ext[i]:\n                        if ext != parte_cerca:\n                            match = False\n                            break\n                    else:\n                        # ✅ Cerca sia come prefisso parola che come sottostringa nel nome completo\n                        nome_full = brano.get(\'nome_lower\', brano[\'nome\'].lower())\n                        if not any(p.startswith(parte_cerca) for p in parole_brano) and parte_cerca not in nome_full:\n                            match = False\n                            break\n\n                if match:\n                    if ext == \'mp3\':\n                        risultati_mp3.append(brano)\n                    else:\n                        risultati_altri.append(brano)\n                    if len(risultati_mp3) + len(risultati_altri) >= 100:\n                        break\n\n        # ✅ Post risultati al main thread (solo se questa ricerca è ancora valida)\n        if getattr(self, \'_search_generation\', 0) == gen:\n            # ✅ Dedup per path (evita duplicati da race condition tra scan thread)\n            visti = set()\n            dedup = []\n            for b in (risultati_mp3 + risultati_altri):\n                p = b.get(\'path\', \'\')\n                if p not in visti:\n                    visti.add(p)\n                    dedup.append(b)\n\n            # ✅ BASI ONLINE (KDM): dopo i locali, se la licenza abilita il\n            #    database online, aggiungi i brani trovati sul server.\n            #    Girano in QUESTO thread (non bloccano la UI). Il server filtra\n            #    gia\' audio/video secondo i permessi KDM.\n            online = []\n            try:\n                from . import licensing\n                if licensing.kdm_abilitato():\n                    from . import basi_online\n                    for r in basi_online.cerca(testo):\n                        db_id = r.get(\'id\', \'\')\n                        file_nome = r.get(\'file_nome\') or (\n                            (r.get(\'artista\', \'\') + \' - \' + r.get(\'titolo\', \'\')).strip(\' -\'))\n                        nome_lower = file_nome.lower()\n                        nome_senza_ext, ext_p = os.path.splitext(nome_lower)\n                        ext = ext_p[1:] if ext_p else \'\'\n                        if \' - \' in nome_senza_ext:\n                            pp = nome_senza_ext.split(\' - \', 1)\n                            parole = pp[0].strip().split() + pp[1].strip().split()\n                        else:\n                            parole = nome_senza_ext.split()\n                        if ext:\n                            parole.append(ext)\n                        online.append({\n                            \'nome\': file_nome,\n                            \'path\': \'kdmonline://\' + str(db_id),\n                            \'tokens\': nome_senza_ext.split(),\n                            \'nome_lower\': nome_lower,\n                            \'ext\': ext,\n                            \'parole\': parole,\n                            \'online\': True,\n                            \'db_id\': db_id,\n                            \'file_nome\': file_nome,\n                        })\n            except Exception as e:\n                print(f"[libreria] basi online: {e}")\n\n            # ✅ ARCHIVI LOCALI (basi_mp3.db / basi_video.db / basi_midi.db):\n            #    i database delle basi, che stanno su disco ma NON come file\n            #    sciolti. Senza questo blocco il suggeritore mostrava solo i\n            #    file gia\' estratti: l\'intero archivio non era raggiungibile\n            #    dal campo di ricerca (ci arrivava solo l\'altro percorso, il\n            #    popup che si apre con INVIO). La base vera viene scritta su\n            #    disco soltanto se l\'utente sceglie quel risultato.\n            archivi = []\n            try:\n                from .carica_basi import cerca_nei_db\n                gia_visti = set(b.get(\'nome_lower\', \'\') for b in dedup)\n                for r in cerca_nei_db(testo, limite=60):\n                    if r[\'nome_lower\'] in gia_visti:\n                        continue          # gia\' presente come file su disco\n                    nome_senza_ext, ext_p = os.path.splitext(r[\'nome_lower\'])\n                    ext = ext_p[1:] if ext_p else \'\'\n                    if \' - \' in nome_senza_ext:\n                        pp = nome_senza_ext.split(\' - \', 1)\n                        parole = pp[0].strip().split() + pp[1].strip().split()\n                    else:\n                        parole = nome_senza_ext.split()\n                    if ext:\n                        parole.append(ext)\n                    voce = dict(r)\n                    voce[\'tokens\'] = nome_senza_ext.split()\n                    voce[\'ext\'] = ext\n                    voce[\'parole\'] = parole\n                    archivi.append(voce)\n            except Exception as e:\n                print(f"[libreria] archivi basi: {e}")\n\n            # ✅ Ricontrolla la generazione: la cerca online e\' una chiamata\n            #    di rete e nel frattempo l\'utente potrebbe aver digitato altro.\n            if getattr(self, \'_search_generation\', 0) != gen:\n                return\n\n            # Prima i file gia\' su disco, poi gli archivi locali, poi l\'online.\n            #\n            # ⛔ Con il semplice (dedup + archivi + online)[:80] gli archivi\n            # NON si vedevano mai appena la cartella mappata era ricca: i\n            # file su disco riempivano da soli tutti gli 80 posti e il\n            # contenuto dei database restava fuori, dando l\'impressione che\n            # la ricerca non li guardasse nemmeno. Ora archivi e online\n            # hanno una loro fetta garantita, e lo spazio che non usano\n            # torna ai file su disco.\n            TETTO = 80\n            POSTI_ARCHIVI = 24\n            POSTI_ONLINE = 8\n            riservati = (POSTI_ARCHIVI if archivi else 0) + (POSTI_ONLINE if online else 0)\n            finali = (dedup[:max(0, TETTO - riservati)]\n                      + archivi[:POSTI_ARCHIVI]\n                      + online[:POSTI_ONLINE])\n            if len(finali) < TETTO:\n                gia = set(id(v) for v in finali)\n                for v in dedup + archivi + online:\n                    if id(v) not in gia:\n                        finali.append(v)\n                        if len(finali) >= TETTO:\n                            break\n            finali = finali[:TETTO]\n\n            # I suggerimenti si mostrano PER TIPO: prima gli mp3, poi i\n            # video (mp4), poi i midi. Vale per tutta la tendina, non solo\n            # per la parte degli archivi: chi cerca una base da cantare\n            # vuole per prima cosa gli mp3, da qualunque parte arrivino.\n            # L\'ordinamento e\' stabile, quindi a parita\' di tipo resta\n            # l\'ordine di prima: file su disco, poi archivi, poi online.\n            finali.sort(key=_peso_tipo)\n            try:\n                self.parent.after(0, lambda f=finali: self._mostra_risultati_filtro(f))\n            except:\n                pass\n\n    threading.Thread(target=_search_thread, daemon=True).start()\n\ndef _aggancia_caricamento_016(self):\n    """Prepara la tabella appena l\'elenco della cartella e\' pronto.\n\n    ⚠️ Non si puo\' sapere in anticipo QUANDO il thread che ricostruisce\n    l\'elenco avra\' finito: si guarda la lista dei brani e appena cambia -\n    cioe\' appena la cartella nuova e\' caricata - si prepara la tabella.\n    Il controllo e\' su identita\' e lunghezza, che non costano niente, e si\n    resta acceso: cambiando cartella la tabella va rifatta.\n    """\n    if getattr(self, \'_guardia016\', False):\n        return\n    self._guardia016 = True\n\n    def guarda():\n        vista = None\n        while True:                          # resta acceso\n            # ⚠️ Prima si fermava dopo un minuto e su 400.000 file la scansione ci mette molto di piu: il guardiano moriva prima di vedere l elenco. E cambiando cartella serve di nuovo, quindi non scada.\n            _time016.sleep(0.25)\n            try:\n                brani = self.brani_pc or ()\n            except Exception:\n                return\n            if not brani:\n                continue\n            if brani is vista:\n                continue\n            vista = brani\n            pronta = getattr(self, \'_tabella016\', None)\n            if pronta and pronta[0] is brani and pronta[1] == len(brani):\n                continue                     # gia\' fatta per questa lista\n            try:\n                self._prepara_tabella_016()\n            except Exception as e:\n                print("patch 016: preparazione non avviata (%s)" % e)\n\n    _th016.Thread(target=guarda, daemon=True).start()\n\n\ndef _file_tabella_016(self, cartella):\n    """Dove sta il file .db di questa cartella: accanto all\'elenco salvato."""\n    import hashlib\n    base = _os016.environ.get("LOCALAPPDATA") or _os016.path.expanduser("~")\n    d = _os016.path.join(base, "KaraDom", "elenchi")\n    try:\n        _os016.makedirs(d, exist_ok=True)\n    except Exception:\n        return None\n    chiave = _os016.path.normpath(cartella or \'\').lower().encode("utf-8", "replace")\n    return _os016.path.join(d, hashlib.sha1(chiave).hexdigest()[:16] + ".ricerca.db")\n\n\ndef _prepara_tabella_016(self):\n    """Scrive nome e percorso di ogni brano in una tabella, in un thread.\n\n    Misurato su 400.000 brani: 0,36 s per le righe, 0,40 s per gli indici,\n    e il MIDI intanto non perde un colpo (punta 1,0 ms) perche\' anche in\n    scrittura SQLite molla il turno.\n\n    ⚠️ Nel file finiscono SOLO nome ed ext e la POSIZIONE nella lista: le\n    basi restano dove sono, sul disco. Il percorso vero si riprende dalla\n    lista in memoria, cosi\' non puo\' esserci nessuna divergenza fra quello\n    che la ricerca trova e quello che il programma poi apre.\n    """\n    brani = self.brani_pc or ()\n    if not brani or getattr(self, \'_tabella016_in_corso\', False):\n        return\n    pronta = getattr(self, \'_tabella016\', None)\n    if pronta and pronta[0] is brani and pronta[1] == len(brani):\n        return                      # gia\' fatta per questa lista\n    soglia = getattr(self, \'_soglia016\', None)\n    if soglia is None:\n        soglia = 100000\n        try:\n            from moduli.database import Database\n            soglia = int(str(Database.get_config(\'ricerca_soglia_brani\',\n                                                 \'100000\')).strip())\n        except Exception:\n            pass\n        self._soglia016 = max(0, soglia)\n    if len(brani) < self._soglia016:\n        return                      # archivio piccolo: si resta come prima\n\n    self._tabella016_in_corso = True\n\n    def lavora(lista=brani):\n        try:\n            import sqlite3\n            f = self._file_tabella_016(getattr(self, \'percorso_attivo\', \'\'))\n            if not f:\n                return\n            # Il file resta sul disco fra un avvio e l\'altro: se e\' ancora\n            # quello giusto si riusa invece di riscrivere 400.000 righe.\n            # Si controlla il numero di righe e il nome del primo e\n            # dell\'ultimo brano: se combaciano e\' la stessa cartella.\n            if _os016.path.exists(f):\n                try:\n                    _c = sqlite3.connect(\'file:%s?mode=ro\' % f, uri=True, timeout=3)\n                    _n = _c.execute(\'SELECT COUNT(*) FROM basi\').fetchone()[0]\n                    _ok = (_n == len(lista))\n                    if _ok:\n                        for _p in (0, len(lista) - 1):\n                            _r = _c.execute(\'SELECT nome FROM basi WHERE pos = ?\',\n                                            (_p,)).fetchone()\n                            _atteso = (lista[_p].get(\'nome_lower\')\n                                       or lista[_p][\'nome\'].lower())\n                            if not _r or _r[0] != _atteso:\n                                _ok = False\n                                break\n                    _c.close()\n                    if _ok:\n                        self._tabella016 = (lista, len(lista), f)\n                        print(\"\u2705 %d brani: tabella di ricerca gia\u0027 pronta\" % len(lista))\n                        return\n                except Exception:\n                    pass\n            try:\n                if _os016.path.exists(f):\n                    _os016.remove(f)\n            except Exception:\n                pass\n            con = sqlite3.connect(f)\n            con.execute(\'PRAGMA journal_mode=OFF\')\n            con.execute(\'PRAGMA synchronous=OFF\')\n            con.execute(\'CREATE TABLE basi (pos INTEGER PRIMARY KEY, \'\n                        \'nome TEXT, parole TEXT, ext TEXT)\')\n            righe = []\n            for _n, b in enumerate(lista):\n                parole = b.get(\'parole\')\n                if parole is None:\n                    nome_lower = b[\'nome\'].lower()\n                    senza, est = _os016.path.splitext(nome_lower)\n                    ext = est[1:] if est else \'\'\n                    if \' - \' in senza:\n                        _a, _s, _d = senza.partition(\' - \')\n                        parole = _a.split() + _d.split()\n                    else:\n                        parole = senza.split()\n                    if ext:\n                        parole.append(ext)\n                nome_full = b.get(\'nome_lower\') or b[\'nome\'].lower()\n                righe.append((_n, nome_full, \' \' + \' \'.join(parole) + \' \',\n                              b.get(\'ext\', \'\')))\n            con.executemany(\'INSERT INTO basi VALUES (?,?,?,?)\', righe)\n            con.execute(\'CREATE INDEX i_nome ON basi(nome)\')\n            con.execute(\'CREATE INDEX i_ext ON basi(ext)\')\n            con.commit()\n            con.close()\n            self._tabella016 = (lista, len(lista), f)\n            print("\\u2705 %d brani nella tabella di ricerca" % len(lista))\n        except Exception as e:\n            print("patch 016: tabella non creata (%s)" % e)\n        finally:\n            self._tabella016_in_corso = False\n\n    _th016.Thread(target=lavora, daemon=True).start()\n\n\ndef _cerca_in_tabella_016(self, parti, parti_ext, brani_ref, tetto):\n    """Le posizioni dei brani che combaciano, in ordine. None se non e\' pronta.\n\n    Stesso criterio del ciclo originale, tradotto in SQL:\n      - prefisso di parola  ->  parole LIKE \'% parte%\'   (le parole sono\n        scritte con uno spazio davanti e uno dietro)\n      - oppure sottostringa ->  nome LIKE \'%parte%\'\n      - estensione          ->  ext = \'mp3\'  (uguaglianza, come prima)\n    Le parti si sommano in AND, come nel ciclo.\n    """\n    import sqlite3\n    pronta = getattr(self, \'_tabella016\', None)\n    brani = self.brani_pc or ()\n    if not pronta or pronta[0] is not brani or pronta[1] != len(brani):\n        return None\n    f = pronta[2]\n    if not _os016.path.exists(f):\n        return None\n\n    dove, valori = [], []\n    for k, parte in enumerate(parti):\n        if parti_ext[k]:\n            dove.append(\'ext = ?\')\n            valori.append(parte)\n        else:\n            dove.append(\'(parole LIKE ? OR nome LIKE ?)\')\n            valori.append(\'%% %s%%\' % parte)\n            valori.append(\'%%%s%%\' % parte)\n    if not dove:\n        return None\n\n    try:\n        con = sqlite3.connect(\'file:%s?mode=ro\' % f, uri=True, timeout=3)\n        cur = con.execute(\'SELECT pos FROM basi WHERE %s ORDER BY pos LIMIT ?\'\n                          % \' AND \'.join(dove), valori + [tetto])\n        fuori = [r[0] for r in cur.fetchall()]\n        con.close()\n    except Exception as e:\n        print("patch 016: ricerca nella tabella fallita (%s)" % e)\n        return None\n    return [p for p in fuori if 0 <= p < len(brani_ref)]\n\n\ndef _peso_tipo(voce):\n    """Numero d\'ordine del tipo di file, per ordinare i suggerimenti."""\n    ext = (voce.get(\'ext\') or \'\').lower()\n    if not ext:\n        ext = os.path.splitext(voce.get(\'nome_lower\') or voce.get(\'nome\') or \'\')[1][1:].lower()\n    return _ORDINE_ESTENSIONI.get(ext, 3)\n\n\n_ORDINE_ESTENSIONI = {\n    \'mp3\': 0, \'wav\': 0, \'m4a\': 0, \'flac\': 0, \'ogg\': 0, \'wma\': 0,\n    \'mp4\': 1, \'mkv\': 1, \'avi\': 1, \'mov\': 1, \'webm\': 1, \'mpg\': 1, \'mpeg\': 1, \'m4v\': 1, \'wmv\': 1,\n    \'mid\': 2, \'midi\': 2, \'kar\': 2,\n}\n\n'


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_016', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def apply():
    if _spenta():
        print("patch 016: spenta dalla configurazione (patch_016 = 0)")
        return False
    try:
        import os as _os
        import threading as _th
        import moduli.libreria_search_mixin as S
        C = getattr(S, "LibreriaSearchMixin", None)
        if C is None or not hasattr(C, "aggiorna_suggerimenti_live"):
            print("patch 016: LibreriaSearchMixin diverso, salto")
            return False
        spazio = S.__dict__
        spazio['_os016'] = _os
        spazio['_th016'] = _th
        import time as _tm
        spazio['_time016'] = _tm
        exec(compile(CODICE, "<patch016>", "exec"), spazio)
        if not hasattr(C, "_orig_016_ricerca"):
            C._orig_016_ricerca = C.aggiorna_suggerimenti_live
        for nome in ('_file_tabella_016', '_prepara_tabella_016',
                     '_cerca_in_tabella_016', '_aggancia_caricamento_016',
                     'aggiorna_suggerimenti_live'):
            setattr(C, nome, spazio[nome])

        # ⭐ la tabella si prepara APPENA LA CARTELLA E' CARICATA, non alla
        #    prima ricerca: cosi' quando l'utente scrive e' gia' pronta e
        #    sparisce anche il primo calo. Ci si aggancia avvolgendo il
        #    metodo che apre una cartella.
        # ⚠️ carica_brani sta su LibreriaScanMixin, NON su LibreriaSearchMixin:
        #    sono due classi SORELLE dentro LibreriaSlider, non una dentro
        #    l'altra. Cercandolo su C, hasattr dava False e questo aggancio
        #    veniva saltato in silenzio: la tabella non si preparava
        #    all'apertura della cartella e la prima ricerca era lenta come
        #    prima. Si prendono anche le altre due strade che rifanno
        #    l'elenco senza passare da qui.
        import moduli.libreria_scan_mixin as _SC
        SCAN = getattr(_SC, 'LibreriaScanMixin', None)
        for _nome in ('carica_brani', '_scansiona_cartelle_multiple',
                      'aggiorna_database_brani'):
            _marchio = '_orig_016_' + _nome
            if SCAN is None or not hasattr(SCAN, _nome) or hasattr(SCAN, _marchio):
                continue
            setattr(SCAN, _marchio, getattr(SCAN, _nome))

            def avvolto(self, *a, _orig=getattr(SCAN, _marchio), **k):
                esito = _orig(self, *a, **k)
                try:
                    if a and isinstance(a[0], str):
                        self.percorso_attivo = a[0]
                    self._aggancia_caricamento_016()
                except Exception:
                    pass
                return esito

            setattr(SCAN, _nome, avvolto)
        print("patch 016: la ricerca la fa il database "
              "(oltre i 100.000 brani; il MIDI non perde piu' i tempi)")
        return True
    except Exception as e:
        print("patch 016: %s" % e)
        return False


def revert():
    try:
        import moduli.libreria_search_mixin as S
        C = S.LibreriaSearchMixin
        rimessi = []
        if hasattr(C, "_orig_016_ricerca"):
            C.aggiorna_suggerimenti_live = C._orig_016_ricerca
            rimessi.append('ricerca')
        import moduli.libreria_scan_mixin as _SC
        SCAN = getattr(_SC, 'LibreriaScanMixin', None)
        for _nome in ('carica_brani', '_scansiona_cartelle_multiple',
                      'aggiorna_database_brani'):
            _marchio = '_orig_016_' + _nome
            if SCAN is not None and hasattr(SCAN, _marchio):
                setattr(SCAN, _nome, getattr(SCAN, _marchio))
                delattr(SCAN, _marchio)
                rimessi.append(_nome)
        if rimessi:
            print("patch 016: rimessi gli originali (%s)" % ', '.join(rimessi))
            return True
    except Exception as e:
        print("revert 016: %s" % e)
    return False


try:
    apply()
except Exception as _e:
    print("patch 016: %s" % _e)
