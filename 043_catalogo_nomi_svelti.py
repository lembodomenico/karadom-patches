# 043 - catalogo nomi svelti

import os
import sys
import time


def traccia(testo):
    riga = '[043] %s' % testo
    try:
        print(riga)
    except Exception:
        pass
    try:
        import datetime
        d = os.path.join(os.environ.get('LOCALAPPDATA') or
                         os.path.expanduser('~'), 'KaraDom')
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, 'patch043.log'), 'a', encoding='utf-8') as f:
            f.write('%s  %s%s' % (
                datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                riga, chr(10)))
    except Exception:
        pass


CODICE = '# ⭐ A che punto e\' il controllo, per chi guarda: la finestra delle Opzioni lo\n#    rilegge ogni mezzo secondo. Senza, sui 341.982 file di C:\\KARAOKE\\Basi la\n#    scritta restava ferma undici secondi di fila ("rimane fermo per una\n#    vita" — utente, 13-09).\nSTATO = {\'letti\': 0, \'fatti\': 0, \'totali\': 0, \'ora\': \'\', \'domande\': 0,\n         \'risparmiate\': 0, \'genius_spento\': False, \'mandati\': 0}\n\n# ⚠️ i blocchi per il catalogo partono UNO PER VOLTA: due invii insieme\n#    scriverebbero lo stesso file dei gia\' mandati\n_INVIO = threading.Lock()\n\n# ⛔⛔ VERSO L\'ESTERNO UNA RICHIESTA ALLA VOLTA ("le verifiche le deve fare 1\n#     alla volta con l\'esterno" — utente, 13-09). I fili che controllano i\n#     nomi restano quattro — cosi\' chi trova la risposta in memoria non\n#     aspetta — ma a LRCLIB e a Genius si parla uno per volta, in fila.\n#     RLock: `cerca_*` lo tiene durante la pausa del ritmo e `_scarica` lo\n#     riprende, e lo stesso filo non deve bloccarsi da solo.\n_UNA_ALLA_VOLTA = threading.RLock()\n\n# ⭐⭐ LE DOMANDE GIA\' FATTE NON SI RIFANNO. Tagliando i nomi a ritroso, per\n#     ogni base di Vasco si finisce a chiedere "Vasco Rossi": misurato sui\n#     341.982 file veri, il 68% delle domande a LRCLIB e\' una RIPETIZIONE\n#     (2.556.198 nel caso peggiore, 826.276 diverse). Si tengono le risposte\n#     della sessione; il tetto evita di riempire la memoria del PC.\nfrom collections import OrderedDict as _OrderedDict\n_RISPOSTE = _OrderedDict()\n_RISPOSTE_MAX = 200000\n_RISPOSTE_CHIAVE = threading.Lock()\n\n\ndef _dalla_cache(fonte, q):\n    k = (fonte, (q or \'\').lower())\n    with _RISPOSTE_CHIAVE:\n        r = _RISPOSTE.get(k)\n        if r is not None:\n            _RISPOSTE.move_to_end(k)\n            STATO[\'risparmiate\'] += 1\n        return r\n\n\ndef _nella_cache(fonte, q, risultati):\n    k = (fonte, (q or \'\').lower())\n    with _RISPOSTE_CHIAVE:\n        _RISPOSTE[k] = list(risultati)\n        _RISPOSTE.move_to_end(k)\n        while len(_RISPOSTE) > _RISPOSTE_MAX:\n            _RISPOSTE.popitem(last=False)\n\n\ndef _scarica(url, headers, timeout=20):\n    with _UNA_ALLA_VOLTA:\n        req = urllib.request.Request(url, headers=headers)\n        with urllib.request.urlopen(req, timeout=timeout) as r:\n            return json.loads(r.read().decode(\'utf-8\', \'replace\'))\n\n\ndef cerca_lrclib(q):\n    """[(artista, titolo)] da LRCLIB. Senza chiavi, gratis.\n\n    ⛔ IL TRATTINO AZZERA LA RICERCA: "Vasco Rossi - Albachiara" non trova\n       niente, "Vasco Rossi Albachiara" trova tre volte il brano (provato il\n       12-09). Quindi i trattini diventano spazi.\n    """\n    q2 = _per_la_ricerca(q)\n    gia = _dalla_cache(\'lrclib\', q2)\n    if gia is not None:\n        return gia\n    with _UNA_ALLA_VOLTA:\n        # un altro filo puo\' averla chiesta mentre questo aspettava il turno\n        gia = _dalla_cache(\'lrclib\', q2)\n        if gia is not None:\n            return gia\n        _RITMO.aspetta(\'lrclib\')\n        d = _scarica(LRCLIB % urllib.parse.quote(q2),\n                     {\'User-Agent\': \'KaraDom (catalogo)\'})\n        STATO[\'domande\'] += 1\n    fuori = [(x.get(\'artistName\') or \'\', x.get(\'trackName\') or \'\')\n             for x in (d or [])[:8]]\n    _nella_cache(\'lrclib\', q2, fuori)\n    return fuori\n\n\nNOSTRI = \'https://lyrics.karadom.it/lyrics_api.php?riconosci=1\'\nNOSTRI_PRIMA = True\n_FIDUCIA = {\'genius\': 3, \'nostri\': 3, \'lrclib\': 2, \'regole\': 1, \'\': 0}\n\n\ndef cerca_genius(q, token=\'\'):\n    """[(artista, titolo)] dall\'API ufficiale di Genius.\n\n    ⚠️ Si usa `api.genius.com/search`, che per CERCARE funziona benissimo.\n       (`genius.com/api/search/multi` risponde 403: Cloudflare.)\n\n    ⛔⛔ QUANDO GENIUS HA FINITO LA QUOTA SI SMETTE DI CHIEDERGLIELO. Il tetto\n       e\' di 10.000 richieste al giorno PER IP, non per token (vedi la memoria\n       del dump di Genius). Sul PC dell\'utente il 13-09 aveva riconosciuto 19\n       nomi su 2.266 e ZERO nelle ultime due ore, eppure il controllo glielo\n       chiedeva ancora per ogni nome: un\'attesa e una richiesta a vuoto a ogni\n       giro. Al primo 429 (quota) o 401/403 (token) si spegne per la sessione.\n    """\n    if STATO.get(\'genius_spento\'):\n        return []\n    token = token or token_genius()\n    if not token:\n        return []\n    q2 = _per_la_ricerca(q)\n    gia = _dalla_cache(\'genius\', q2)\n    if gia is not None:\n        return gia\n    with _UNA_ALLA_VOLTA:\n        gia = _dalla_cache(\'genius\', q2)\n        if gia is not None:\n            return gia\n        if STATO.get(\'genius_spento\'):\n            return []\n        _RITMO.aspetta(\'genius\')\n        try:\n            d = _scarica(GENIUS % urllib.parse.quote(q2),\n                         {\'Authorization\': \'Bearer \' + token,\n                          \'User-Agent\': \'KaraDom (catalogo)\'})\n        except Exception as e:\n            if getattr(e, \'code\', None) in (401, 403, 429):\n                STATO[\'genius_spento\'] = True\n                return []\n            raise\n        STATO[\'domande\'] += 1\n    fuori = []\n    for h in (d or {}).get(\'response\', {}).get(\'hits\', [])[:8]:\n        if h.get(\'type\') != \'song\':\n            continue\n        r = h.get(\'result\', {})\n        fuori.append(((r.get(\'primary_artist\') or {}).get(\'name\') or \'\',\n                      r.get(\'title\') or \'\'))\n    _nella_cache(\'genius\', q2, fuori)\n    return fuori\n\n\ndef _solo_un_refuso(a, b, quante=2):\n    """Fra i due c\'e\' soltanto un errore di battitura?\n\n    ⛔⛔ QUESTO NON E\' UN DOPPIONE (utente, 12-09):\n          "Morandi - C\'era un ragazzo che come me amava i Beatles..."\n          "Baglioni ft Morandi - C\'era un ragazzo che come me amava i..."\n        sono DUE BRANI: l\'artista e\' diverso. Per questo l\'artista non si\n        confronta mai "a somiglianza", solo il titolo, e solo se le parole sono\n        le stesse in numero e cambiano pochissime lettere: cosi\' "coppia" e\n        "coppiia" si uniscono, mentre un titolo con una parola in piu\' resta un\n        brano a se\'.\n    """\n    pa, pb = _parole(a), _parole(b)\n    if len(pa) != len(pb):\n        return False\n    sa, sb = \' \'.join(pa), \' \'.join(pb)\n    if sa == sb:\n        return True\n    # ⛔⛔ UN NUMERO DIVERSO E\' UN BRANO DIVERSO. "Parsifal parte 1" e "parte 2",\n    #     "Vol 1" e "Vol 2" differiscono di una lettera sola e venivano fusi\n    #     come refusi: nel catalogo ne restava uno (provato il 13-09). Come per\n    #     l\'artista, i numeri si confrontano per uguaglianza, mai a somiglianza.\n    if re.findall(r\'\\d+\', sa) != re.findall(r\'\\d+\', sb):\n        return False\n    if abs(len(sa) - len(sb)) > quante:\n        return False\n    diverse = sum(1 for x in difflib.ndiff(sa, sb) if x[0] in \'+-\')\n    return diverse <= quante * 2\n\n\ndef _coppie_candidate(nome):\n    """Le coppie (artista, titolo) da provare nei NOSTRI database, nello\n    stesso ordine a ritroso del controllo esterno (`candidati`).\n\n    ⚠️ Anche col solo primo artista: "Adriano Celentano ft Claudia Mori" nel\n       database puo\' stare sotto "Adriano Celentano".\n    """\n    fuori = []\n    for cand in candidati(nome):\n        a, t = artista_titolo(cand)\n        if not a or not t:\n            continue\n        for aa in (a, a.split(\' ft \')[0]):\n            c = (aa.strip(), t.strip())\n            if c[0] and c[1] and c not in fuori:\n                fuori.append(c)\n    return fuori\n\n\ndef riconosci_nostri(nomi, per_volta=150, fili=4, fermati=None, avviso=None):\n    """`{nome: esito}` per i nomi che i NOSTRI database riconoscono.\n\n    ⭐⭐ PRIMA I NOSTRI DATABASE, POI FUORI ("in primo acchito devi guardare\n       nei nostri db e poi in esterno" — utente, 13-09). Sul VPS c\'e\' il dump\n       di Genius (3,6 milioni di brani, indice su artista+titolo): una\n       richiesta sola risponde per `per_volta` nomi, invece di una domanda a\n       LRCLIB per ogni pezzo tagliato. A LRCLIB, una alla volta, va solo\n       quello che qui non si trova.\n    ⚠️ Il cliente i database NON li ha ([[chi-ha-quale-hardware]]): si passa\n       sempre dal server (`lyrics_api.php?riconosci=1`).\n    ⭐ Qui le richieste possono andare in parallelo (`fili`): il server e\'\n       nostro, la regola "una alla volta" vale verso l\'esterno.\n    ⚠️ La grafia: se la chiave e\' uguale si tiene quella del FILE (regola del\n       catalogo); se il server l\'ha trovata ignorando accenti e segni, si\n       prende la SUA ("Berte" -> "Bertè").\n    """\n    from concurrent.futures import ThreadPoolExecutor\n    nomi = list(dict.fromkeys(n for n in nomi if n))\n    gruppi = [nomi[i:i + per_volta] for i in range(0, len(nomi), per_volta)]\n    fuori = {}\n    chiave = threading.Lock()\n    fatti = [0]\n\n    def _gruppo(gruppo):\n        if fermati and fermati():\n            return\n        coppie, dove = [], []\n        for gi, nome in enumerate(gruppo):\n            for a, t in _coppie_candidate(nome):\n                dove.append(nome)\n                # il terzo campo e\' il GRUPPO (= il nome): il server si ferma\n                # alla prima coppia trovata del nome, e fa il confronto lento\n                # senza accenti solo se nessuna ha la chiave esatta\n                coppie.append([a, t, gi])\n        trovati = {}\n        if coppie:\n            req = urllib.request.Request(\n                NOSTRI, data=json.dumps({\'coppie\': coppie}).encode(\'utf-8\'),\n                headers={\'Content-Type\': \'application/json\',\n                         \'User-Agent\': \'KaraDom (catalogo)\'}, method=\'POST\')\n            with urllib.request.urlopen(req, timeout=120) as r:\n                d = json.loads(r.read().decode(\'utf-8\', \'replace\'))\n            trovati = (d or {}).get(\'trovati\') or {}\n        scelti = {}\n        for i, (a, t, _g) in enumerate(coppie):\n            nome = dove[i]\n            if nome in scelti:\n                continue                      # vince la PRIMA a ritroso\n            h = trovati.get(str(i))\n            if not h:\n                continue\n            if len(h) > 2 and h[2] == \'esatta\':\n                art, tit = a, t\n            else:\n                # ⚠️ dal server si prende solo l\'ARTISTA, che e\' dove servono\n                #    gli accenti ("Berte" -> "Bertè"); il titolo resta quello\n                #    del file: preso dal server, "Il mare d\'inverno" diventava\n                #    "... (feat. Fiorella Mannoia)", un\'altra versione (13-09)\n                art, tit = apostrofi_normali(h[0]), t\n            scelti[nome] = {\'artista\': art, \'titolo\': tit, \'fonte\': \'nostri\'}\n        with chiave:\n            fuori.update(scelti)\n            fatti[0] += len(gruppo)\n            STATO[\'nostri_fatti\'] = fatti[0]\n            STATO[\'nostri_trovati\'] = len(fuori)\n            if avviso:\n                avviso(fatti[0], len(nomi), len(fuori))\n\n    with ThreadPoolExecutor(max_workers=max(1, int(fili))) as squadra:\n        for _ in squadra.map(_gruppo, gruppi):\n            pass\n    return fuori\n\n\ndef _in_riga(radice, f, esito):\n    """La riga del catalogo per un file: `(riga, fonte)`, o `(None, None)` se\n    dal nome non si ricavano artista e titolo.\n\n    ⭐ UNA funzione sola per le due strade: i blocchi mandati SUBITO mentre si\n       controlla e il conto finale devono fare la stessa riga dallo stesso\n       nome, o lo stesso brano entrerebbe due volte con due grafie.\n    """\n    artista = (esito or {}).get(\'artista\')\n    titolo = (esito or {}).get(\'titolo\')\n    fonte = (esito or {}).get(\'fonte\') or \'\'\n    if not artista or not titolo:\n        # ⭐ nessuna fonte l\'ha riconosciuto: valgono le regole di sempre\n        artista, titolo = artista_titolo(f)\n        fonte = \'regole\'\n    if not artista or not titolo:\n        return None, None\n    # anche a quello confermato si tolgono le sigle rimaste in coda: la\n    # fonte dice dove finisce il titolo, non sempre lo ripulisce\n    titolo = togli_suppellettili(titolo) or titolo\n    return ({\'artista\': artista[:255], \'titolo\': titolo[:255],\n             \'percorso\': os.path.basename(radice)[:255],\n             \'ext\': os.path.splitext(f)[1].lower().lstrip(\'.\')[:10],\n             \'fonte\': fonte}, fonte)\n\n\ndef leggi_cartella_confermata(cartella, dentro_le_sottocartelle=True,\n                              avviso=None, fili=4, con_genius=True,\n                              diario=None, fermati=None, memoria_in=None,\n                              a_blocchi=None, ogni=1500, ogni_s=30):\n    """Come `leggi_cartella`, ma ogni nome passa dal controllo incrociato.\n\n    Torna `(brani, scartati, conto)`; in `conto` quanti sono stati confermati\n    dalle fonti, quanti vengono dalla memoria e quanti sono rimasti alle regole\n    scritte a mano.\n\n    ⚠️ `fili=4`: quattro nomi in lavorazione insieme, ma verso l\'esterno UNA\n       richiesta alla volta (`_UNA_ALLA_VOLTA`, regola dell\'utente).\n    ⭐ Chi non viene riconosciuto NON si butta: entra in catalogo con artista e\n       titolo ricavati dalle regole, come prima. Il controllo aggiunge, non\n       toglie.\n\n    ⭐⭐ IL CATALOGO SI RIEMPIE SUBITO, NON ALLA FINE ("devi popolare subito e\n       non alla fine" — utente, 13-09). Con `a_blocchi` i nomi gia\' controllati\n       si consegnano a pezzi mentre il controllo va avanti: ogni `ogni` nomi o\n       ogni `ogni_s` secondi, quello che arriva prima. Sui 341.982 file\n       dell\'utente il primo giro dura ore: aspettare la fine voleva dire un\n       catalogo vuoto per tutto quel tempo.\n       ⚠️ Se un blocco non parte (rete), non si ferma niente: quei brani non\n          risultano mandati e li riprende l\'invio finale.\n       ⚠️ Fra blocchi diversi i doppioni li toglie il server (stessa chiave,\n          `osso()`), ma tiene il PRIMO arrivato: "vince quello senza refusi"\n          vale dentro un blocco e alla fine, non fra un blocco e l\'altro.\n    """\n    from queue import Queue\n    # si riparte da zero: la finestra legge questi numeri mentre si lavora.\n    # Anche Genius si riprova: la sua quota e\' su 24 ore, domani puo\' esserci.\n    STATO.update({\'letti\': 0, \'fatti\': 0, \'totali\': 0, \'ora\': \'\',\n                  \'domande\': 0, \'risparmiate\': 0, \'genius_spento\': False,\n                  \'mandati\': 0})\n    nomi = []\n    for radice, _dirs, files in os.walk(cartella):\n        for f in sorted(files):\n            if os.path.splitext(f)[1].lower() in ESTENSIONI:\n                nomi.append((radice, f))\n        # ⚠️ solo leggere 341.982 file prende decine di secondi: si conta\n        #    mentre si legge, e si puo\' fermare anche qui\n        STATO[\'letti\'] = len(nomi)\n        if fermati and fermati():\n            break\n        if not dentro_le_sottocartelle:\n            break\n    STATO[\'totali\'] = len(nomi)\n\n    memoria = Memoria(memoria_in)     # `memoria_in` serve solo per le prove\n    token = token_genius() if con_genius else \'\'\n\n    # ⭐⭐ PRIMA I NOSTRI DATABASE, POI FUORI ("in primo acchito devi guardare\n    #    nei nostri db e poi in esterno" — utente, 13-09). I nomi che la\n    #    memoria non conosce si chiedono al nostro server a blocchi; quello\n    #    che riconosce va in memoria, e il giro qui sotto lo trova li\' senza\n    #    chiedere niente a LRCLIB.\n    #    ⚠️ A pezzi di 1500, e si salva dopo OGNI pezzo: fermando qui non si\n    #       perde niente di quello che il server ha gia\' riconosciuto.\n    #    ⚠️ Se il server non risponde si va avanti come prima: fuori, uno\n    #       alla volta. Il controllo non deve fermarsi per questo.\n    STATO.update({\'fase\': \'nostri\', \'nostri_da\': 0, \'nostri_visti\': 0,\n                  \'nostri_ok\': 0})\n    if NOSTRI_PRIMA and not (fermati and fermati()):\n        try:\n            with memoria._chiave:\n                gia = {r[0] for r in memoria._c.execute(\n                    \'SELECT nome FROM conferme WHERE quando > ?\',\n                    (time.time() - Memoria.SCADE,))}\n        except Exception:\n            gia = set()\n        da_chiedere = []\n        for _r, f in nomi:\n            n = pulisci_nome(f)\n            if n not in gia:\n                gia.add(n)\n                da_chiedere.append(n)\n        STATO[\'nostri_da\'] = len(da_chiedere)\n        for k in range(0, len(da_chiedere), 1500):\n            if fermati and fermati():\n                break\n            pezzo = da_chiedere[k:k + 1500]\n            try:\n                trovati = riconosci_nostri(pezzo, fermati=fermati)\n            except Exception as e:\n                if diario:\n                    diario(\'  i nostri database non rispondono (%s): si va \'\n                           \'fuori\' % str(e)[:60])\n                break\n            for n, esito in trovati.items():\n                memoria.scrivi(n, esito)\n            STATO[\'nostri_visti\'] = k + len(pezzo)\n            STATO[\'nostri_ok\'] += len(trovati)\n    STATO[\'fase\'] = \'fuori\'\n\n    conto = {\'confermati\': 0, \'da_memoria\': 0, \'con_le_regole\': 0, \'scartati\': 0}\n    esiti = {}\n    coda = Queue()\n    for i, (radice, f) in enumerate(nomi):\n        coda.put((i, radice, f))\n    fatti = [0]\n    blocco = threading.Lock()\n    pronti = []\n    ultimo_invio = [time.time()]\n\n    def _consegna(lotto):\n        righe = []\n        for radice, f, esito in lotto:\n            riga, _fonte = _in_riga(radice, f, esito)\n            if riga:\n                righe.append(riga)\n        if not righe:\n            return\n        righe, _doppi = togli_doppioni(righe)\n        with _INVIO:\n            try:\n                a_blocchi(righe)\n                STATO[\'mandati\'] += len(righe)\n            except Exception as e:\n                if diario:\n                    diario(\'  blocco non mandato (%s): lo riprende l-invio finale\'\n                           % str(e)[:60])\n\n    def _lavora():\n        while True:\n            try:\n                i, radice, f = coda.get_nowait()\n            except Exception:\n                return\n            lotto = None\n            try:\n                if fermati and fermati():\n                    return\n                nome = pulisci_nome(f)\n                esito = memoria.leggi(nome)\n                if esito is not None:\n                    da = \'da_memoria\'\n                else:\n                    # ⭐ il nome che si sta chiedendo fuori: e\' quello che la\n                    #    finestra mostra, e cambia a ogni nome controllato\n                    STATO[\'ora\'] = nome\n                    esito = conferma(f, con_genius=bool(token), token=token,\n                                     diario=diario) or {}\n                    memoria.scrivi(nome, esito)\n                    da = \'confermati\' if esito.get(\'artista\') else \'\'\n                with blocco:\n                    esiti[i] = (radice, f, esito)\n                    if da:\n                        conto[da] += 1\n                    fatti[0] += 1\n                    STATO[\'fatti\'] = fatti[0]\n                    if avviso and fatti[0] % 10 == 0:\n                        avviso(fatti[0], len(nomi), dict(conto))\n                    if a_blocchi:\n                        pronti.append((radice, f, esito))\n                        adesso = time.time()\n                        if (len(pronti) >= ogni\n                                or adesso - ultimo_invio[0] >= ogni_s):\n                            lotto = pronti[:]\n                            del pronti[:]\n                            ultimo_invio[0] = adesso\n            finally:\n                coda.task_done()\n            # fuori dal lucchetto: mentre questo filo manda, gli altri\n            # continuano a controllare\n            if lotto:\n                _consegna(lotto)\n\n    squadra = [threading.Thread(target=_lavora, daemon=True)\n               for _ in range(max(1, int(fili)))]\n    for t in squadra:\n        t.start()\n    for t in squadra:\n        t.join()\n    memoria.chiudi()\n    # quello che resta, anche se si e\' premuto Ferma: e\' gia\' controllato\n    if a_blocchi and pronti:\n        _consegna(pronti[:])\n        del pronti[:]\n\n    grezzi, scartati = [], []\n    for i, (radice, f) in enumerate(nomi):\n        _r, _f, esito = esiti.get(i, (radice, f, {}))\n        riga, fonte = _in_riga(radice, f, esito)\n        if riga is None:\n            scartati.append(f)\n            conto[\'scartati\'] += 1\n            continue\n        if fonte == \'regole\':\n            conto[\'con_le_regole\'] += 1\n        grezzi.append(riga)\n    trovati, doppi = togli_doppioni(grezzi)\n    conto[\'doppioni\'] = doppi\n    trovati.sort(key=lambda b: (_ordine(b[\'artista\']), _ordine(b[\'titolo\'])))\n    return trovati, scartati, conto\n\n\n'


def apply():
    try:
        mod = sys.modules.get('moduli.catalogo_conferma')
        if mod is None:
            traccia('il controllo dei nomi non c-e- in questa versione')
            return False
        if getattr(mod, '_svelto043', False):
            return True
        exec(compile(CODICE, '<patch043>', 'exec'), mod.__dict__)
        vera = mod.leggi_cartella_confermata

        def leggi_cartella_confermata(*a, _vera=vera, **k):
            if k.get('a_blocchi') is None:
                rem = sys.modules.get('moduli.catalogo_remoto')
                if rem is not None and hasattr(rem, 'manda'):
                    k['a_blocchi'] = (lambda righe, _r=rem, _f=k.get('fermati'):
                                      _r.manda(righe, fermati=_f))
            mod.STATO['in_corso'] = True
            try:
                return _vera(*a, **k)
            finally:
                mod.STATO['in_corso'] = False

        mod.leggi_cartella_confermata = leggi_cartella_confermata
        mod._svelto043 = True
        traccia('nomi: fuori una domanda alla volta, domande ripetute dalla '
                'memoria (fino a %d), Genius si spegne a quota finita'
                % mod._RISPOSTE_MAX)
        _orologio(mod)
        return True
    except Exception as e:
        traccia('non agganciata: %s: %s' % (type(e).__name__, e))
        return False


def _orologio(mod):
    try:
        opz = sys.modules.get('moduli.opzioni')
        if opz is None:
            return
        cls = None
        for nome in dir(opz):
            o = getattr(opz, nome)
            if isinstance(o, type) and hasattr(o, '_popola_catalogo_remoto'):
                cls = o
                break
        if cls is None or getattr(cls._popola_catalogo_remoto, '_nomi043', False):
            return
        originale = cls._popola_catalogo_remoto
        GIRA = ('|', '/', '-', '\\')

        def _popola(self, _orig=originale):
            partito = time.time()

            FINE = ('Fatto', 'Fermato', 'Non ha funzionato', 'Nessun brano',
                    'Scegli prima')
            self._orologio043 = True

            def _batti(n=0):
                s = mod.STATO
                try:
                    attuale = self.lbl_catalogo.cget('text') or ''
                except Exception:
                    return
                if n > 4 and attuale.startswith(FINE):
                    return
                if not s.get('in_corso'):
                    base = attuale.lstrip('|/-\\ ').split('  ·  ')[0]
                    if base.startswith(('Mandati', 'Trovati', 'Riconosciuti')):
                        try:
                            self.lbl_catalogo.config(text='%s %s  ·  %d s' % (
                                GIRA[n % 4], base, time.time() - partito))
                        except Exception:
                            return
                if s.get('in_corso'):
                    passato = time.time() - partito
                    fatti, totali = s.get('fatti', 0), s.get('totali', 0)
                    if not totali:
                        testo = '%s Leggo la cartella: %d file — %d s' % (
                            GIRA[n % 4], s.get('letti', 0), passato)
                    elif s.get('fase') == 'nostri':
                        testo = ('%s Nei nostri database: %d su %d nomi — '
                                 'riconosciuti %d — %d s') % (
                            GIRA[n % 4], s.get('nostri_visti', 0),
                            s.get('nostri_da', 0), s.get('nostri_ok', 0),
                            passato)
                    else:
                        manca = ''
                        if fatti > 20 and passato > 10 and totali > fatti:
                            resta = (totali - fatti) * (passato / fatti)
                            manca = (' — mancano %d h' % (resta / 3600)
                                     if resta >= 5400 else
                                     ' — mancano %d min' % max(1, resta / 60))
                        testo = ('%s Nomi: %d su %d — domande fuori %d, '
                                 'risparmiate %d — %d s%s') % (
                            GIRA[n % 4], fatti, totali, s.get('domande', 0),
                            s.get('risparmiate', 0), passato, manca)
                        if s.get('mandati'):
                            testo += ' — nel catalogo %d' % s['mandati']
                        if s.get('ora'):
                            testo += chr(10) + 'ora: %s' % s['ora'][:70]
                        if s.get('genius_spento'):
                            testo += '  (Genius ha finito la quota: solo LRCLIB)'
                    try:
                        self.lbl_catalogo.config(text=testo, fg='#ffffff')
                    except Exception:
                        return
                try:
                    self.window.after(500, _batti, n + 1)
                except Exception:
                    pass
            try:
                self.window.after(300, _batti)
            except Exception:
                pass
            return _orig(self)

        _popola._nomi043 = True
        cls._popola_catalogo_remoto = _popola
        traccia('i nomi controllati ora scorrono nella finestra')
    except Exception as e:
        traccia('orologio non agganciato: %s' % e)


def revert():
    return False


try:
    apply()
except Exception:
    pass
