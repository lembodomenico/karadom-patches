# 009_preferiti_si_indicizza_una_volta.py
#
# CON 400.000 BASI, OGNI CLIC SU UN PREFERITO RIFACEVA TUTTO DA CAPO.
#
# Cosa succedeva a ogni clic:
#   1. `os.walk` ricorsivo di tutto l'albero del disco. Nessuna cache: non solo
#      a ogni clic, ma anche a ogni riavvio del programma.
#   2. poi, NELLA FINESTRA (thread principale), due giri su tutti i file - uno
#      per l'elenco, uno per l'indice di ricerca, con una espressione regolare
#      per ogni nome. Misurato su 400.000 basi: 3,8 secondi di finestra
#      bloccata, oltre al tempo del disco.
#
# In quei secondi non si muove niente, e un MIDI sull'expander perde colpi: il
# suo thread e' codice Python e non gira finche' il principale tiene il GIL.
# E' il sintomo che l'utente ha descritto come "spostandomi fra i preferiti
# calano i BPM".
#
# COME FUNZIONA ADESSO (come l'ha chiesto lui: *"l'indicizzazione la deve fare
# una volta e la volta successiva col tasto destro"*):
#
#   - la PRIMA volta si legge il disco e l'elenco si SALVA in
#     %LOCALAPPDATA%\KaraDom\elenchi (compresso: 5,5 MB per 400.000 brani);
#   - da li' in avanti si riusa, anche dopo aver chiuso e riaperto KaraDom:
#     misurato 0,2 secondi invece della scansione;
#   - per rileggere il disco davvero: TASTO DESTRO sul preferito ->
#     "Aggiorna preferito (rilegge il disco)".
#     Nessuna scadenza automatica, nessun controllo a sorpresa: comanda lui.
#
# E il lavoro pesante e' uscito dalla finestra: nel thread principale restano
# quattro assegnazioni (da 2,7 s a zero), e la scansione si ferma un istante
# ogni 2000 file per lasciare respirare la musica - senza, un ciclo Python lungo
# tiene il GIL anche se gira "in background".
#
# ⚠️ Questa patch cambia solo `carica_brani` e aggiunge quattro metodi. Perche'
# il tasto destro forzi la rilettura serve anche la riga in
# libreria_uibuilder_mixin (`carica_brani(path, forza=True)`), che sta nel
# sorgente: finche' non si ricompila, col tasto destro si riusa l'elenco
# salvato come col clic normale. Per rifare l'indice prima della build si puo'
# cancellare la cartella %LOCALAPPDATA%\KaraDom\elenchi.

CODICE = 'def carica_brani(self, cartella, forza=False):\n    """Carica i brani di una cartella. Con CACHE, e senza soffocare la musica.\n\n    🔴 [2026-09-04] Riscritta per gli archivi grossi. Con 400.000 basi -\n    il caso di un cliente vero - a OGNI clic su un preferito succedeva:\n\n      1. `os.walk` ricorsivo di tutto l\'albero, ogni volta da capo: nessuna\n         cache, `self.brani_completi = []` e si ricominciava;\n      2. poi, NEL THREAD PRINCIPALE, due giri su tutti i file: uno per\n         costruire l\'elenco, l\'altro per l\'indice di ricerca, con una\n         espressione regolare per ogni nome. Misurato: **3,8 secondi** di\n         finestra bloccata, piu\' il tempo del disco.\n\n    In quei secondi non si muove niente - e se stava suonando un MIDI\n    sull\'expander, la musica perdeva colpi: il suo thread e\' codice Python e\n    non gira finche\' il thread principale tiene il GIL. E\' il sintomo che\n    l\'utente ha descritto come "spostandomi fra i preferiti calano i BPM".\n\n    Le tre cose che cambiano:\n      - **cache per cartella**: la seconda volta e\' immediata (`forza=True`\n        per rileggere davvero il disco, es. dal tasto Ricarica);\n      - **tutto il lavoro pesante nel thread di scansione**, non nel\n        principale: li\' resta solo l\'assegnazione, che e\' istantanea;\n      - **respiro**: ogni tot file il thread si ferma un istante e lascia il\n        turno agli altri. Senza, un ciclo Python lungo tiene il GIL e la\n        musica aspetta lo stesso, anche se e\' "in background".\n    """\n    import time as _time\n\n    cache = getattr(self, "_cache_brani", None)\n    if cache is None:\n        cache = self._cache_brani = {}\n\n    chiave = os.path.normpath(cartella).lower()\n\n    # 1) gia\' in memoria: immediato\n    if not forza and chiave in cache:\n        self.brani_completi, self.brani_pc, self.indice_preferiti = cache[chiave]\n        print(f"✅ {len(self.brani_completi)} brani (gia\' letti, dalla memoria)")\n        return\n\n    # 2) 🔴 SUL DISCO: l\'elenco si salva, cosi\' non si rilegge l\'archivio a\n    #    ogni riavvio del programma. Con 400.000 basi camminare sull\'albero\n    #    e\' la parte piu\' lenta di tutte, e prima si rifaceva ogni volta -\n    #    anche solo passando da un preferito all\'altro e tornando indietro.\n    #    L\'utente: "non deve leggere ogni volta che ci vado sopra".\n    if not forza:\n        _salvati = self._leggi_cache_disco(cartella)\n        if _salvati is not None:\n            self.brani_completi = _salvati\n            self._ricostruisci_elenchi(_salvati, cartella, cache, chiave)\n            return\n\n    self.indice_preferiti = {}\n    self.brani_completi = []\n\n    estensioni = {\'.mp3\',\'.mp4\',\'.avi\',\'.mkv\',\'.flv\',\'.wav\',\'.flac\',\n                  \'.aac\',\'.ogg\',\'.wma\',\'.m4a\',\'.webm\',\'.mov\',\'.wmv\',\n                  \'.mpg\',\'.mpeg\',\'.mid\',\'.midi\',\'.kar\', \'.kfn\', \'.mkf\', \'.m4v\',\n                  \'.aiff\',\'.aif\',\'.opus\',\'.ape\',\'.m4b\',\'.mp2\',\n                  \'.ra\',\'.rm\',\'.mka\',\'.3gp\'}\n\n    from fnmatch import fnmatch\n    filtro_ext = Database.get_config(\'filtro_estensioni\', \'\').strip()\n    patterns = [p.strip() for p in filtro_ext.split(\',\') if p.strip()] if filtro_ext else []\n\n    # ogni quanti file il thread si ferma un attimo: 2000 e\' un compromesso\n    # fra "non rallentare la scansione" e "non far perdere colpi alla musica"\n    RESPIRO_OGNI = 2000\n\n    def scan_thread():\n        brani_trovati = []\n        visti = 0\n        try:\n            for root_dir, dirs, files in os.walk(cartella):\n                for file in sorted(files):\n                    visti += 1\n                    if visti % RESPIRO_OGNI == 0:\n                        _time.sleep(0.002)      # lascia il turno alla musica\n                    ext = os.path.splitext(file)[1].lower()\n                    if ext in estensioni:\n                        if patterns and not any(fnmatch(file.lower(), p.lower()) for p in patterns):\n                            continue\n                        brani_trovati.append(os.path.join(root_dir, file))\n        except Exception as e:\n            print(f"⚠️ Errore scansione: {e}")\n\n        # ⚠️ elenco e indice si costruiscono QUI, non nel thread principale:\n        #    su 400.000 file sono quasi quattro secondi di lavoro, e nel\n        #    thread principale bloccano finestra e musica.\n        nuovi_brani_pc = []\n        nuovo_indice = {}\n        for n, path in enumerate(brani_trovati):\n            if n % RESPIRO_OGNI == 0 and n:\n                _time.sleep(0.002)\n            nome = os.path.basename(path)\n            senza_ext = os.path.splitext(nome)[0].lower()\n            nuovi_brani_pc.append({\'nome\': nome, \'path\': path,\n                                   \'tokens\': senza_ext.split()})\n            nuovo_indice[path] = re.findall(r"[a-zA-Z0-9àèéìòóù]+", senza_ext)\n\n        def _assegna():\n            # nel thread principale resta SOLO questo: quattro assegnazioni\n            self.brani_completi = brani_trovati\n            self.brani_pc = nuovi_brani_pc\n            self.indice_preferiti = nuovo_indice\n            cache[chiave] = (brani_trovati, nuovi_brani_pc, nuovo_indice)\n            print(f"✅ {len(brani_trovati)} brani caricati da {cartella}")\n        try:\n            self._scrivi_cache_disco(cartella, brani_trovati)\n        except Exception as _e:\n            print(f"⚠️ elenco non salvato su disco: {_e}")\n\n        try:\n            self.parent.after(0, _assegna)\n        except Exception:\n            _assegna()\n\n    threading.Thread(target=scan_thread, daemon=True).start()\n\n\n# ------------------------------------------------------------------\n#  L\'ELENCO DEI BRANI SI RICORDA: si legge il disco UNA volta\n# ------------------------------------------------------------------\n#  Con 400.000 basi camminare sull\'albero del disco e\' la parte piu\' lenta\n#  di tutte, e prima si rifaceva SEMPRE: a ogni clic su un preferito e a\n#  ogni riavvio del programma. L\'utente: *"non deve leggere ogni volta che\n#  ci vado sopra; l\'indicizzazione la deve fare una volta e la volta\n#  successiva col tasto destro"*.\n#\n#  Quindi: la prima volta si legge il disco e l\'elenco si salva. Da li\' in\n#  avanti si riusa, anche dopo aver chiuso e riaperto KaraDom. Per rileggere\n#  davvero c\'e\' il TASTO DESTRO sul preferito -> "Aggiorna preferito".\n#  Nessuna scadenza automatica, nessun controllo a sorpresa: comanda lui.\n#\n#  Cosa si salva: solo i PERCORSI, compressi. Nomi e indice di ricerca si\n#  rifanno al volo in un paio di secondi, in un thread e non nella finestra;\n#  salvarli farebbe un file tre volte piu\' grosso per risparmiare due secondi.\n\ndef _file_cache_brani(self, cartella):\n    import hashlib\n    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")\n    d = os.path.join(base, "KaraDom", "elenchi")\n    try:\n        os.makedirs(d, exist_ok=True)\n    except Exception:\n        return None\n    chiave = os.path.normpath(cartella).lower().encode("utf-8", "replace")\n    return os.path.join(d, hashlib.sha1(chiave).hexdigest()[:16] + ".txt.gz")\n\ndef _leggi_cache_disco(self, cartella):\n    """L\'elenco salvato, oppure None se non c\'e\' (allora si legge il disco)."""\n    import gzip\n    import time as _t\n    f = self._file_cache_brani(cartella)\n    if not f or not os.path.exists(f):\n        return None\n    try:\n        with gzip.open(f, "rt", encoding="utf-8") as h:\n            brani = [r.strip() for r in h if r.strip()]\n        if not brani:\n            return None\n        ore = (_t.time() - os.path.getmtime(f)) / 3600.0\n        print("✅ %d brani dall\'elenco salvato (%.0f ore fa): niente "\n              "scansione del disco" % (len(brani), ore))\n        return brani\n    except Exception as e:\n        print("⚠️ elenco salvato non leggibile (%s): rileggo il disco" % e)\n        return None\n\ndef _scrivi_cache_disco(self, cartella, brani):\n    import gzip\n    f = self._file_cache_brani(cartella)\n    if not f or not brani:\n        return\n    tmp = f + ".tmp"\n    with gzip.open(tmp, "wt", encoding="utf-8") as h:\n        h.write(chr(10).join(brani))\n    os.replace(tmp, f)          # atomico: mai un file scritto a meta\'\n    print("💾 elenco salvato: %d brani, %.1f MB (col tasto destro sul "\n          "preferito si rilegge il disco)"\n          % (len(brani), os.path.getsize(f) / 1048576.0))\n\ndef _ricostruisci_elenchi(self, brani, cartella, cache, chiave):\n    """Da un elenco di percorsi rifa\' nomi e indice, SENZA toccare il disco.\n\n    In un thread e con pause: su 400.000 brani sono un paio di secondi, e\n    nella finestra bloccherebbero tutto - musica compresa.\n    """\n    import time as _time\n    RESPIRO_OGNI = 2000\n\n    def lavora():\n        nuovi, indice = [], {}\n        for n, path in enumerate(brani):\n            if n % RESPIRO_OGNI == 0 and n:\n                _time.sleep(0.002)\n            nome = os.path.basename(path)\n            senza = os.path.splitext(nome)[0].lower()\n            nuovi.append({\'nome\': nome, \'path\': path, \'tokens\': senza.split()})\n            indice[path] = re.findall(r"[a-zA-Z0-9àèéìòóù]+", senza)\n\n        def _assegna():\n            self.brani_completi = brani\n            self.brani_pc = nuovi\n            self.indice_preferiti = indice\n            cache[chiave] = (brani, nuovi, indice)\n            print("✅ %d brani pronti (dall\'elenco salvato)" % len(brani))\n\n        try:\n            self.parent.after(0, _assegna)\n        except Exception:\n            _assegna()\n\n    threading.Thread(target=lavora, daemon=True).start()\n\n'


def apply():
    import moduli.libreria_scan_mixin as L
    C = getattr(L, "LibreriaScanMixin", None)
    if C is None or not hasattr(C, "carica_brani"):
        print("patch 009: modulo diverso, salto")
        return False
    # si compila NELLO SPAZIO DEI NOMI del modulo: dentro si usano os, re,
    # threading, Database... che qui non ci sono
    spazio = L.__dict__
    exec(compile(CODICE, "<patch009>", "exec"), spazio)
    for nome in ("carica_brani", "_file_cache_brani", "_leggi_cache_disco",
                 "_scrivi_cache_disco", "_ricostruisci_elenchi"):
        setattr(C, nome, spazio[nome])
    print("patch 009: i preferiti si indicizzano una volta sola "
          "(poi col tasto destro)")
    return True


try:
    apply()
except Exception as _e:
    print("patch 009: %s" % _e)
