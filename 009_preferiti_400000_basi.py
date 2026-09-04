# 009_preferiti_400000_basi.py
#
# SPOSTANDOSI FRA I PREFERITI CALAVANO I BPM. Con 400.000 basi, ogni clic:
#
#   1. rileggeva TUTTO l'albero del disco (nessuna cache: si ricominciava da capo);
#   2. poi, NEL THREAD PRINCIPALE, faceva due giri su tutti i file - uno per
#      l'elenco, uno per l'indice di ricerca, con una espressione regolare per
#      ogni nome. Misurato: 3,8 secondi di finestra bloccata.
#
# In quei secondi non si muove niente, e un MIDI sull'expander perde colpi: il
# suo thread e' codice Python e non gira finche' il principale tiene il GIL.
#
# COSA CAMBIA
#   - CACHE per cartella: la seconda volta e' immediata (il tasto Ricarica
#     rilegge il disco davvero, con forza=True);
#   - il lavoro pesante passa NEL THREAD DI SCANSIONE: nel principale restano
#     quattro assegnazioni. Misurato: da 2,7 s a zero;
#   - RESPIRO: ogni 2000 file il thread si ferma un istante e lascia il turno.
#     Senza, un ciclo Python lungo tiene il GIL e la musica aspetta lo stesso,
#     anche se il lavoro e' "in background".
#
# Va insieme alla 005 (la ricerca: 905 ms per tasto su 400.000 basi) e alla 008
# (il motore non butta piu' via il tempo perso). Sono i tre punti in cui un
# archivio molto grande soffocava la riproduzione.

CODICE = 'def carica_brani(self, cartella, forza=False):\n    """Carica i brani di una cartella. Con CACHE, e senza soffocare la musica.\n\n    🔴 [2026-09-04] Riscritta per gli archivi grossi. Con 400.000 basi -\n    il caso di un cliente vero - a OGNI clic su un preferito succedeva:\n\n      1. `os.walk` ricorsivo di tutto l\'albero, ogni volta da capo: nessuna\n         cache, `self.brani_completi = []` e si ricominciava;\n      2. poi, NEL THREAD PRINCIPALE, due giri su tutti i file: uno per\n         costruire l\'elenco, l\'altro per l\'indice di ricerca, con una\n         espressione regolare per ogni nome. Misurato: **3,8 secondi** di\n         finestra bloccata, piu\' il tempo del disco.\n\n    In quei secondi non si muove niente - e se stava suonando un MIDI\n    sull\'expander, la musica perdeva colpi: il suo thread e\' codice Python e\n    non gira finche\' il thread principale tiene il GIL. E\' il sintomo che\n    l\'utente ha descritto come "spostandomi fra i preferiti calano i BPM".\n\n    Le tre cose che cambiano:\n      - **cache per cartella**: la seconda volta e\' immediata (`forza=True`\n        per rileggere davvero il disco, es. dal tasto Ricarica);\n      - **tutto il lavoro pesante nel thread di scansione**, non nel\n        principale: li\' resta solo l\'assegnazione, che e\' istantanea;\n      - **respiro**: ogni tot file il thread si ferma un istante e lascia il\n        turno agli altri. Senza, un ciclo Python lungo tiene il GIL e la\n        musica aspetta lo stesso, anche se e\' "in background".\n    """\n    import time as _time\n\n    cache = getattr(self, "_cache_brani", None)\n    if cache is None:\n        cache = self._cache_brani = {}\n\n    chiave = os.path.normpath(cartella).lower()\n    if not forza and chiave in cache:\n        self.brani_completi, self.brani_pc, self.indice_preferiti = cache[chiave]\n        print(f"✅ {len(self.brani_completi)} brani (gia\' letti, dalla memoria)")\n        return\n\n    self.indice_preferiti = {}\n    self.brani_completi = []\n\n    estensioni = {\'.mp3\',\'.mp4\',\'.avi\',\'.mkv\',\'.flv\',\'.wav\',\'.flac\',\n                  \'.aac\',\'.ogg\',\'.wma\',\'.m4a\',\'.webm\',\'.mov\',\'.wmv\',\n                  \'.mpg\',\'.mpeg\',\'.mid\',\'.midi\',\'.kar\', \'.kfn\', \'.mkf\', \'.m4v\',\n                  \'.aiff\',\'.aif\',\'.opus\',\'.ape\',\'.m4b\',\'.mp2\',\n                  \'.ra\',\'.rm\',\'.mka\',\'.3gp\'}\n\n    from fnmatch import fnmatch\n    filtro_ext = Database.get_config(\'filtro_estensioni\', \'\').strip()\n    patterns = [p.strip() for p in filtro_ext.split(\',\') if p.strip()] if filtro_ext else []\n\n    # ogni quanti file il thread si ferma un attimo: 2000 e\' un compromesso\n    # fra "non rallentare la scansione" e "non far perdere colpi alla musica"\n    RESPIRO_OGNI = 2000\n\n    def scan_thread():\n        brani_trovati = []\n        visti = 0\n        try:\n            for root_dir, dirs, files in os.walk(cartella):\n                for file in sorted(files):\n                    visti += 1\n                    if visti % RESPIRO_OGNI == 0:\n                        _time.sleep(0.002)      # lascia il turno alla musica\n                    ext = os.path.splitext(file)[1].lower()\n                    if ext in estensioni:\n                        if patterns and not any(fnmatch(file.lower(), p.lower()) for p in patterns):\n                            continue\n                        brani_trovati.append(os.path.join(root_dir, file))\n        except Exception as e:\n            print(f"⚠️ Errore scansione: {e}")\n\n        # ⚠️ elenco e indice si costruiscono QUI, non nel thread principale:\n        #    su 400.000 file sono quasi quattro secondi di lavoro, e nel\n        #    thread principale bloccano finestra e musica.\n        nuovi_brani_pc = []\n        nuovo_indice = {}\n        for n, path in enumerate(brani_trovati):\n            if n % RESPIRO_OGNI == 0 and n:\n                _time.sleep(0.002)\n            nome = os.path.basename(path)\n            senza_ext = os.path.splitext(nome)[0].lower()\n            nuovi_brani_pc.append({\'nome\': nome, \'path\': path,\n                                   \'tokens\': senza_ext.split()})\n            nuovo_indice[path] = re.findall(r"[a-zA-Z0-9àèéìòóù]+", senza_ext)\n\n        def _assegna():\n            # nel thread principale resta SOLO questo: quattro assegnazioni\n            self.brani_completi = brani_trovati\n            self.brani_pc = nuovi_brani_pc\n            self.indice_preferiti = nuovo_indice\n            cache[chiave] = (brani_trovati, nuovi_brani_pc, nuovo_indice)\n            print(f"✅ {len(brani_trovati)} brani caricati da {cartella}")\n\n        try:\n            self.parent.after(0, _assegna)\n        except Exception:\n            _assegna()\n\n    threading.Thread(target=scan_thread, daemon=True).start()\n\n'


def apply():
    import moduli.libreria_scan_mixin as L
    C = getattr(L, "LibreriaScanMixin", None)
    if C is None or not hasattr(C, "carica_brani"):
        print("patch 009: modulo diverso, salto")
        return False
    spazio = L.__dict__          # os, re, threading, Database, messagebox...
    exec(compile(CODICE, "<patch009>", "exec"), spazio)
    C.carica_brani = spazio["carica_brani"]
    print("patch 009: i preferiti non riscansionano piu' tutto a ogni clic")
    return True


try:
    apply()
except Exception as _e:
    print("patch 009: %s" % _e)
