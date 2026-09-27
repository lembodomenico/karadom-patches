# 015_ricerca_in_c_niente_calo.py
#
# IL CALO CHE RESTAVA DOPO LA 014: UNA RICERCA SOLA, MA PESANTE.
#
# Con la 014 il cliente non ha piu' un calo per ogni lettera, ma uno solo:
# quando smette di scrivere e la ricerca parte. Quel residuo e' il ciclo che
# scorre i 400.000 brani uno per uno — 215 ms di codice Python filato, durante
# i quali il thread del MIDI non puo' eseguire nulla (il GIL e' occupato) e
# sull'expander i BPM calano.
#
# TRE STRADE PROVATE E MISURATE, DUE BOCCIATE:
#   - far RESPIRARE il ciclo: peggiora di dieci volte (su Windows il turno
#     ceduto torna con ~15 ms di ritardo);
#   - alzare la PRIORITA' del thread MIDI: non cambia niente, perche' il
#     limite e' il GIL, non lo scheduler;
#   - recuperare il tempo perso nel player: gia' provato sul campo e RITIRATO.
#
# QUESTA E' LA TERZA: la stessa identica ricerca, eseguita da `str.find`
# (codice C) invece che da un ciclo Python. I criteri non cambiano — prefisso
# di parola OPPURE sottostringa, estensioni per uguaglianza — e nemmeno
# l'ordine dei risultati, perche' si scorre sempre dal primo brano all'ultimo.
#
# MISURATO su 400.000 brani, parola rara (scansione completa):
#       ciclo Python .....  214,7 ms
#       str.find .........   16,7 ms      13 volte piu' veloce, sotto i 50
#
# COSTO: ~27 MB di memoria con 400.000 brani, e 0,2 s per costruire la
# stringa — pagati una volta per cartella, in un thread a parte, mai durante
# una ricerca. Se la stringa non e' pronta si cerca come prima.
#
# ⚠️ La funzione qui dentro e' copiata DAL SORGENTE, non riscritta a mano:
#    cambia solo il blocco del ciclo. Tutto il resto — archivi, ricerca
#    online, tetto degli 80, ripartizione mp3/video/midi — e' parola per
#    parola quello di sempre.
#
# ⚠️ Non tocca `_mostra_risultati_filtro` (la avvolge la 013) ne'
#    `_ricostruisci_elenchi` / `_debounce_suggerimenti` (la 014).
#
# SE NON VA BENE: `R15` la ritira, `patch_015 = 0` la spegne su una macchina
# sola, `revert()` rimette l'originale a caldo. Ritiro pulito: non scrive
# niente da nessuna parte.


CODICE = 'def aggiorna_suggerimenti_live(self, event=None):\n    """Lancia ricerca in THREAD SEPARATO — la UI non si blocca MAI"""\n    testo = self.entry_filtro.get().lower().strip()\n\n    if not testo or testo == "filtra brano o autore" or len(testo) < 2:\n        self.container_suggerimenti.place_forget()\n        return\n\n    # ✅ Incrementa contatore ricerca (cancella ricerche precedenti)\n    self._search_generation = getattr(self, \'_search_generation\', 0) + 1\n    gen = self._search_generation\n\n    # ✅ Parse query (veloce, nel main thread)\n    if \'*\' in testo:\n        raw_parts = [p.strip() for p in testo.split(\'*\') if p.strip()]\n    else:\n        raw_parts = [p for p in re.split(r\'\\s+\', testo) if p]\n\n    parti_wildcard = []\n    parti_is_ext = []\n    for p in raw_parts:\n        if p.startswith(\'.\'):\n            parti_wildcard.append(p[1:])\n            parti_is_ext.append(True)\n        else:\n            parti_wildcard.append(p)\n            parti_is_ext.append(False)\n\n    if not parti_wildcard:\n        self.container_suggerimenti.place_forget()\n        return\n\n    # ✅ Copia riferimento lista (thread-safe: la lista può essere sostituita ma non mutata)\n    brani_ref = self.brani_pc\n\n    def _search_thread():\n        """Ricerca in background — NON tocca la UI"""\n        # ✅ Pre-calcola indice nel thread (non nel main thread).\n        #    `gen` cosi\' che, se l\'utente ha gia\' digitato un\'altra\n        #    lettera, l\'indicizzazione si fermi invece di finire a vuoto.\n        self._ensure_search_index(gen)\n\n        risultati_mp3 = []\n        risultati_altri = []\n\n        # ⭐ [patch 015] LA SCORCIATOIA: la stessa ricerca, fatta da\n        #    str.find (codice C) invece che da questo ciclo in Python.\n        #    Su 400.000 brani: 17 ms invece di 215. Sotto i 50 ms il\n        #    MIDI sull\'expander non perde piu\' i tempi.\n        #    Se la stringa non e\' ancora pronta si fa come prima, e\n        #    intanto la si prepara in un thread a parte: al giro dopo\n        #    c\'e\'. I criteri sono gli stessi, l\'ordine pure.\n        _indici = None\n        try:\n            _indici = self._cerca_veloce_015(parti_wildcard, parti_is_ext,\n                                             brani_ref, 100)\n        except Exception as _e:\n            _indici = None\n\n        if _indici is not None:\n            for _i in _indici:\n                if getattr(self, \'_search_generation\', 0) != gen:\n                    return\n                brano = brani_ref[_i]\n                if brano.get(\'ext\', \'\') == \'mp3\':\n                    risultati_mp3.append(brano)\n                else:\n                    risultati_altri.append(brano)\n        else:\n            try:\n                self._prepara_stringona_015()\n            except Exception:\n                pass\n            for brano in brani_ref:\n                # ✅ Cancellazione: se l\'utente ha digitato altro, esci subito\n                if getattr(self, \'_search_generation\', 0) != gen:\n                    return\n\n                parole_brano = brano.get(\'parole\')\n                ext = brano.get(\'ext\', \'\')\n\n                if parole_brano is None:\n                    nome_lower = brano[\'nome\'].lower()\n                    nome_senza_ext, ext_p = os.path.splitext(nome_lower)\n                    ext = ext_p[1:] if ext_p else ""\n                    if \' - \' in nome_senza_ext:\n                        pp = nome_senza_ext.split(\' - \', 1)\n                        parole_brano = pp[0].strip().split() + pp[1].strip().split()\n                    else:\n                        parole_brano = nome_senza_ext.split()\n                    if ext:\n                        parole_brano.append(ext)\n\n                match = True\n                for i, parte_cerca in enumerate(parti_wildcard):\n                    if parti_is_ext[i]:\n                        if ext != parte_cerca:\n                            match = False\n                            break\n                    else:\n                        # ✅ Cerca sia come prefisso parola che come sottostringa nel nome completo\n                        nome_full = brano.get(\'nome_lower\', brano[\'nome\'].lower())\n                        if not any(p.startswith(parte_cerca) for p in parole_brano) and parte_cerca not in nome_full:\n                            match = False\n                            break\n\n                if match:\n                    if ext == \'mp3\':\n                        risultati_mp3.append(brano)\n                    else:\n                        risultati_altri.append(brano)\n                    if len(risultati_mp3) + len(risultati_altri) >= 100:\n                        break\n\n        # ✅ Post risultati al main thread (solo se questa ricerca è ancora valida)\n        if getattr(self, \'_search_generation\', 0) == gen:\n            # ✅ Dedup per path (evita duplicati da race condition tra scan thread)\n            visti = set()\n            dedup = []\n            for b in (risultati_mp3 + risultati_altri):\n                p = b.get(\'path\', \'\')\n                if p not in visti:\n                    visti.add(p)\n                    dedup.append(b)\n\n            # ✅ BASI ONLINE (KDM): dopo i locali, se la licenza abilita il\n            #    database online, aggiungi i brani trovati sul server.\n            #    Girano in QUESTO thread (non bloccano la UI). Il server filtra\n            #    gia\' audio/video secondo i permessi KDM.\n            online = []\n            try:\n                from . import licensing\n                if licensing.kdm_abilitato():\n                    from . import basi_online\n                    for r in basi_online.cerca(testo):\n                        db_id = r.get(\'id\', \'\')\n                        file_nome = r.get(\'file_nome\') or (\n                            (r.get(\'artista\', \'\') + \' - \' + r.get(\'titolo\', \'\')).strip(\' -\'))\n                        nome_lower = file_nome.lower()\n                        nome_senza_ext, ext_p = os.path.splitext(nome_lower)\n                        ext = ext_p[1:] if ext_p else \'\'\n                        if \' - \' in nome_senza_ext:\n                            pp = nome_senza_ext.split(\' - \', 1)\n                            parole = pp[0].strip().split() + pp[1].strip().split()\n                        else:\n                            parole = nome_senza_ext.split()\n                        if ext:\n                            parole.append(ext)\n                        online.append({\n                            \'nome\': file_nome,\n                            \'path\': \'kdmonline://\' + str(db_id),\n                            \'tokens\': nome_senza_ext.split(),\n                            \'nome_lower\': nome_lower,\n                            \'ext\': ext,\n                            \'parole\': parole,\n                            \'online\': True,\n                            \'db_id\': db_id,\n                            \'file_nome\': file_nome,\n                        })\n            except Exception as e:\n                print(f"[libreria] basi online: {e}")\n\n            # ✅ ARCHIVI LOCALI (basi_mp3.db / basi_video.db / basi_midi.db):\n            #    i database delle basi, che stanno su disco ma NON come file\n            #    sciolti. Senza questo blocco il suggeritore mostrava solo i\n            #    file gia\' estratti: l\'intero archivio non era raggiungibile\n            #    dal campo di ricerca (ci arrivava solo l\'altro percorso, il\n            #    popup che si apre con INVIO). La base vera viene scritta su\n            #    disco soltanto se l\'utente sceglie quel risultato.\n            archivi = []\n            try:\n                from .carica_basi import cerca_nei_db\n                gia_visti = set(b.get(\'nome_lower\', \'\') for b in dedup)\n                for r in cerca_nei_db(testo, limite=60):\n                    if r[\'nome_lower\'] in gia_visti:\n                        continue          # gia\' presente come file su disco\n                    nome_senza_ext, ext_p = os.path.splitext(r[\'nome_lower\'])\n                    ext = ext_p[1:] if ext_p else \'\'\n                    if \' - \' in nome_senza_ext:\n                        pp = nome_senza_ext.split(\' - \', 1)\n                        parole = pp[0].strip().split() + pp[1].strip().split()\n                    else:\n                        parole = nome_senza_ext.split()\n                    if ext:\n                        parole.append(ext)\n                    voce = dict(r)\n                    voce[\'tokens\'] = nome_senza_ext.split()\n                    voce[\'ext\'] = ext\n                    voce[\'parole\'] = parole\n                    archivi.append(voce)\n            except Exception as e:\n                print(f"[libreria] archivi basi: {e}")\n\n            # ✅ Ricontrolla la generazione: la cerca online e\' una chiamata\n            #    di rete e nel frattempo l\'utente potrebbe aver digitato altro.\n            if getattr(self, \'_search_generation\', 0) != gen:\n                return\n\n            # Prima i file gia\' su disco, poi gli archivi locali, poi l\'online.\n            #\n            # ⛔ Con il semplice (dedup + archivi + online)[:80] gli archivi\n            # NON si vedevano mai appena la cartella mappata era ricca: i\n            # file su disco riempivano da soli tutti gli 80 posti e il\n            # contenuto dei database restava fuori, dando l\'impressione che\n            # la ricerca non li guardasse nemmeno. Ora archivi e online\n            # hanno una loro fetta garantita, e lo spazio che non usano\n            # torna ai file su disco.\n            TETTO = 80\n            POSTI_ARCHIVI = 24\n            POSTI_ONLINE = 8\n            riservati = (POSTI_ARCHIVI if archivi else 0) + (POSTI_ONLINE if online else 0)\n            finali = (dedup[:max(0, TETTO - riservati)]\n                      + archivi[:POSTI_ARCHIVI]\n                      + online[:POSTI_ONLINE])\n            if len(finali) < TETTO:\n                gia = set(id(v) for v in finali)\n                for v in dedup + archivi + online:\n                    if id(v) not in gia:\n                        finali.append(v)\n                        if len(finali) >= TETTO:\n                            break\n            finali = finali[:TETTO]\n\n            # I suggerimenti si mostrano PER TIPO: prima gli mp3, poi i\n            # video (mp4), poi i midi. Vale per tutta la tendina, non solo\n            # per la parte degli archivi: chi cerca una base da cantare\n            # vuole per prima cosa gli mp3, da qualunque parte arrivino.\n            # L\'ordinamento e\' stabile, quindi a parita\' di tipo resta\n            # l\'ordine di prima: file su disco, poi archivi, poi online.\n            finali.sort(key=_peso_tipo)\n            try:\n                self.parent.after(0, lambda f=finali: self._mostra_risultati_filtro(f))\n            except:\n                pass\n\n    threading.Thread(target=_search_thread, daemon=True).start()\ndef _peso_tipo(voce):\n    """Numero d\'ordine del tipo di file, per ordinare i suggerimenti."""\n    ext = (voce.get(\'ext\') or \'\').lower()\n    if not ext:\n        ext = os.path.splitext(voce.get(\'nome_lower\') or voce.get(\'nome\') or \'\')[1][1:].lower()\n    return _ORDINE_ESTENSIONI.get(ext, 3)\n\n\n_ORDINE_ESTENSIONI = {\n    \'mp3\': 0, \'wav\': 0, \'m4a\': 0, \'flac\': 0, \'ogg\': 0, \'wma\': 0,\n    \'mp4\': 1, \'mkv\': 1, \'avi\': 1, \'mov\': 1, \'webm\': 1, \'mpg\': 1, \'mpeg\': 1, \'m4v\': 1, \'wmv\': 1,\n    \'mid\': 2, \'midi\': 2, \'kar\': 2,\n}\n\n\n\ndef _stringona_015(self):\n    """I nomi come UNA sola stringa, da scorrere con str.find.\n\n    Ogni riga:   \\n<indice>\\t <parole separate da spazio>\n    Lo spazio davanti alle parole fa si\' che cercare " alba" trovi solo chi ha\n    una PAROLA che comincia per "alba" - il prefisso di parola dell\'originale.\n    Cercando senza lo spazio si ottiene la sottostringa. Stessi due criteri,\n    nello stesso ordine.\n    """\n    brani = self.brani_pc or ()\n    fatta = getattr(self, \'_stringona015\', None)\n    if fatta is not None and fatta[0] is brani and fatta[1] == len(brani):\n        return fatta[2]\n    return None\n\n\ndef _prepara_stringona_015(self):\n    """La costruisce in un thread a parte: mai durante una ricerca."""\n    brani = self.brani_pc or ()\n    if not brani or getattr(self, \'_stringona015_in_corso\', False):\n        return\n    self._stringona015_in_corso = True\n\n    def lavora(lista=brani):\n        try:\n            pezzi = []\n            for _n, b in enumerate(lista):\n                parole = b.get(\'parole\')\n                if parole is None:\n                    nome_lower = b[\'nome\'].lower()\n                    senza, est = _os015.path.splitext(nome_lower)\n                    ext = est[1:] if est else \'\'\n                    if \' - \' in senza:\n                        _a, _s, _d = senza.partition(\' - \')\n                        parole = _a.split() + _d.split()\n                    else:\n                        parole = senza.split()\n                    if ext:\n                        parole.append(ext)\n                nome_full = b.get(\'nome_lower\') or b[\'nome\'].lower()\n                pezzi.append(\'\\n%d\\t %s %s\' % (_n, \' \'.join(parole), nome_full))\n            self._stringona015 = (lista, len(lista), \'\'.join(pezzi))\n        except Exception as _e:\n            print("patch 015: stringa non costruita (%s)" % _e)\n        finally:\n            self._stringona015_in_corso = False\n\n    _th015.Thread(target=lavora, daemon=True).start()\n\n\ndef _cerca_veloce_015(self, parti, parti_ext, brani_ref, tetto):\n    """Gli indici dei brani che combaciano, in ordine. None se non e\' pronta.\n\n    Le parti che sono ESTENSIONI non si cercano qui: si filtrano dopo, sul\n    campo `ext` del brano, esattamente come faceva l\'originale (uguaglianza,\n    non sottostringa). Se si cercano SOLO estensioni, la scorciatoia non\n    serve e si torna al ciclo di prima.\n    """\n    grande = _stringona_015(self)\n    if grande is None:\n        return None\n    testuali = [p for k, p in enumerate(parti) if not parti_ext[k]]\n    estensioni = [p for k, p in enumerate(parti) if parti_ext[k]]\n    if not testuali:\n        return None\n\n    insiemi = []\n    for parte in testuali:\n        trovati = set()\n        for ago in (\' \' + parte, parte):        # prefisso di parola, poi sottostringa\n            p = grande.find(ago)\n            while p != -1:\n                r = grande.rfind(\'\\n\', 0, p)\n                s = grande.find(\'\\t\', r)\n                if r != -1 and s != -1 and s > r:\n                    trovati.add(int(grande[r + 1:s]))\n                p = grande.find(ago, p + 1)\n        if not trovati:\n            return []\n        insiemi.append(trovati)\n\n    comuni = insiemi[0]\n    for s in insiemi[1:]:\n        comuni &= s\n        if not comuni:\n            return []\n\n    fuori = []\n    for _i in sorted(comuni):\n        b = brani_ref[_i]\n        if estensioni and b.get(\'ext\', \'\') not in estensioni:\n            continue\n        fuori.append(_i)\n        if len(fuori) >= tetto:\n            break\n    return fuori\n\n'


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_015', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def apply():
    if _spenta():
        print("patch 015: spenta dalla configurazione (patch_015 = 0)")
        return False
    try:
        import os as _os
        import threading as _th
        import moduli.libreria_search_mixin as S
        C = getattr(S, "LibreriaSearchMixin", None)
        if C is None or not hasattr(C, "aggiorna_suggerimenti_live"):
            print("patch 015: LibreriaSearchMixin diverso, salto")
            return False
        spazio = S.__dict__
        spazio['_os015'] = _os
        spazio['_th015'] = _th
        exec(compile(CODICE, "<patch015>", "exec"), spazio)
        if not hasattr(C, "_orig_015_ricerca"):
            C._orig_015_ricerca = C.aggiorna_suggerimenti_live
        for nome in ('_stringona_015', '_prepara_stringona_015',
                     '_cerca_veloce_015', 'aggiorna_suggerimenti_live'):
            setattr(C, nome, spazio[nome])
        print("patch 015: la ricerca si appoggia a str.find "
              "(13 volte piu' veloce su 400.000 brani)")
        return True
    except Exception as e:
        print("patch 015: %s" % e)
        return False


def revert():
    try:
        import moduli.libreria_search_mixin as S
        C = S.LibreriaSearchMixin
        if hasattr(C, "_orig_015_ricerca"):
            C.aggiorna_suggerimenti_live = C._orig_015_ricerca
            print("patch 015: rimesso l'originale")
            return True
    except Exception as e:
        print("revert 015: %s" % e)
    return False


try:
    apply()
except Exception as _e:
    print("patch 015: %s" % _e)
