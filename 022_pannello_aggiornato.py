# 022 - lo stato delle patch arriva al pannello anche durante la sessione.

OGNI_SECONDI = 120
_VER = 3
NOME_SORVEGLIA = "StatoPatch022v%d" % _VER
NOMI_THREAD = ("PatchUpdater", "PatchAlloSplash", "PatchAllAvvio")

_ultimo = {'inviato': None}


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_022', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def _perche_spenta(numero):
    """Spenta di proposito: dall'impostazione patch_NNN=0, oppure ha visto che qui non serve."""
    try:
        from moduli.database import Database
        if str(Database.get_config('patch_%s' % numero, '1')).strip() in ('0', 'no', 'off'):
            return 'spenta da impostazione (patch_%s=0)' % numero
    except Exception:
        pass
    return 'non adatta a questo PC (si e\' spenta da sola)'


def _ricorda_le_attive():
    """Una patch che si e' attivata RESTA attiva per tutta la sessione.

    KaraDom esegue le patch piu' volte all'avvio (splash, avvio, a caldo): dalla seconda
    molte trovano l'aggancio gia' fatto e rispondono "no". hotfix tiene l'ULTIMA risposta,
    cosi' una patch che funziona risultava "non attiva" (037, 044 su tutti i PC).
    Vale per TUTTE le patch, presenti e future: nessuna deve gestirlo da se'."""
    from moduli import hotfix
    vera = getattr(hotfix, '_esegui_apply', None)
    if vera is None or getattr(vera, '_ricorda022', False):
        return
    attive = set()

    def _esegui_apply(ns, nome, *a, **k):
        esito = vera(ns, nome, *a, **k)
        try:
            app = getattr(hotfix, 'APPLICATE', None)
            if esito:
                attive.add(nome)
            elif nome in attive or (isinstance(app, set) and nome in app):
                # gia' attiva da un passaggio precedente: il "no" di adesso vuol dire "gia' fatto"
                st = getattr(hotfix, 'STATO', None)
                if isinstance(st, dict):
                    st[nome] = {'ok': True, 'nota': 'attiva'}
                return True
        except Exception:
            pass
        return esito
    _esegui_apply._ricorda022 = True
    hotfix._esegui_apply = _esegui_apply


def _ripara_hotfix():
    """Rimette in piedi APPLICATE e STATO negli eseguibili che non li hanno.

    L'eseguibile del 30 agosto e' di un giorno prima della riga che li ha
    introdotti. Senza quel set: la 018 non applica piu' niente allo splash
    (va nell'except appena legge hotfix.APPLICATE), la 021 non sa dire cosa
    ha preso, e al pannello non arriva nulla. Si riempie con lo stesso metro
    del programma: firma buona = quella patch e' stata eseguita.
    """
    import os
    from moduli import hotfix

    rifatto = False
    if not isinstance(getattr(hotfix, 'STATO', None), dict):
        hotfix.STATO = {}
        rifatto = True
    if isinstance(getattr(hotfix, 'APPLICATE', None), set):
        return rifatto

    hotfix.APPLICATE = set()
    try:
        cartella = hotfix.patches_dir()
        for nome in sorted(os.listdir(cartella)):
            if not nome.endswith('.py'):
                continue
            percorso = os.path.join(cartella, nome)
            sig = percorso + '.sig'
            try:
                if os.path.exists(sig) and hotfix._verify(
                        open(percorso, 'rb').read(), open(sig, 'rb').read()):
                    hotfix.APPLICATE.add(nome)
            except Exception:
                continue
    except Exception:
        pass
    return True


def stato_completo():
    """Cosa e' attivo ADESSO e cosa e' solo sceso sul disco.

    1 = attiva          2 = scaricata, entra al riavvio          0 = non attiva

    Le stesse tre prove della 007, nello stesso ordine. Serve perche' negli
    eseguibili piu' vecchi `hotfix.APPLICATE` non esiste: chiedendolo e basta
    si ottiene un elenco vuoto, e con l'elenco vuoto qui non partiva NIENTE.
    Dal pannello si vedeva solo il PC di chi lavora da sorgente, mentre sul PC
    del cliente le stesse patch erano attive e in elenco.
    """
    import os
    from moduli import hotfix

    try:
        cartella = hotfix.patches_dir()
        file = sorted(f for f in os.listdir(cartella) if f.endswith('.py'))
    except Exception:
        return {}

    applicate = set()
    try:
        applicate = set(getattr(hotfix, 'APPLICATE', None) or ())
    except Exception:
        applicate = set()

    def firma_buona(percorso):
        try:
            sig = percorso + '.sig'
            if not os.path.exists(sig):
                return None                      # non si puo' giudicare
            return bool(hotfix._verify(open(percorso, 'rb').read(),
                                       open(sig, 'rb').read()))
        except Exception:
            return None

    def impronta(percorso):
        """La STESSA impronta che git tiene per quel file.

        Serve a distinguere una patch aggiornata da una vecchia: senza, il
        pannello vede solo il numero e chi ha la 017 di ieri sembra a posto
        come chi ha quella di oggi. Si calcola come git: sha1 di
        'blob <lunghezza>\\0' + contenuto, con i fine riga a LF (e' quello che
        sta sul server). Cosi' il pannello confronta con una sola chiamata."""
        import hashlib
        try:
            d = open(percorso, 'rb').read().replace(b'\r\n', b'\n')
            h = hashlib.sha1()
            h.update(b'blob %d\x00' % len(d))
            h.update(d)
            return h.hexdigest()[:8]
        except Exception:
            return ''

    fuori = {}
    for nome in file:
        corto = (str(nome).split('_', 1)[0] or str(nome))[:16]
        percorso = os.path.join(cartella, nome)
        buona = firma_buona(percorso)

        stato = (getattr(hotfix, 'STATO', None) or {}).get(nome)
        if applicate:                            # la fonte piu' precisa
            if nome in applicate:
                fuori[corto] = [1, '']
            elif buona is False or buona is None:
                fuori[corto] = [0, 'firma mancante o non valida']
            elif isinstance(stato, dict) and not stato.get('ok'):
                nota = str(stato.get('nota') or '')
                if 'errore' in nota:
                    # eseguita e andata in ERRORE: rossa, col messaggio vero
                    fuori[corto] = [0, nota[:160]]
                else:
                    # ha deciso lei di non attivarsi: spenta da impostazione o non adatta a questo PC
                    fuori[corto] = [3, _perche_spenta(corto)]
            else:
                # firmata bene ma in questa sessione non e' ancora stata eseguita: entra al riavvio
                fuori[corto] = [2, 'scaricata, entra al riavvio']
        elif buona:                              # compilato vecchio: vale la firma
            fuori[corto] = [1, '']
        elif buona is False:
            fuori[corto] = [0, 'firma non valida']
        else:
            fuori[corto] = [0, 'firma mancante']

        # terza voce: QUALE versione di quella patch e' su questo PC
        fuori[corto].append(impronta(percorso))

    return fuori


def _contesti_ssl():
    """Gli stessi contesti che usa l'updater, nello stesso ordine.

    Nell'eseguibile compilato Python non trova il magazzino dei certificati di
    Windows: una urlopen() su https fallisce sempre, in silenzio. Ecco perche'
    dal pannello si vedeva solo il PC di chi lavora da sorgente. Niente
    CERT_NONE: un canale non verificato si puo' dirottare.
    """
    import ssl
    fuori = []
    try:
        import certifi
        fuori.append(ssl.create_default_context(cafile=certifi.where()))
    except Exception:
        pass
    try:
        fuori.append(ssl.create_default_context())
    except Exception:
        pass
    return fuori


def manda_al_pannello(forza=False):
    import json
    import urllib.parse
    import urllib.request

    dati = stato_completo()
    if not dati:
        return False
    # INTERO: tagliato a 3000 diventava JSON monco e il server lo buttava (con ~125+ patch
    # il PC spariva dal pannello). Si manda in POST: nessun limite di lunghezza dell'indirizzo.
    compatto = json.dumps(dati, ensure_ascii=False, separators=(',', ':'))
    if not forza and compatto == _ultimo['inviato']:
        return False          # non e' cambiato niente: non si disturba il server

    try:
        from moduli.licensing import get_hardware_id, generate_serial
        cpu, mb = get_hardware_id()
        serial = generate_serial(cpu, mb) if (cpu and mb) else ''
    except Exception:
        serial = ''
    if not serial:
        return False

    ver = ''
    for dove, come in (("moduli.versione", "APP_VERSION"),
                       ("moduli.ui", "APP_VERSION"),
                       ("moduli.updater", "CURRENT_VERSION")):
        try:
            ver = str(getattr(__import__(dove, fromlist=[come]), come) or '')
        except Exception:
            ver = ''
        if ver:
            break

    q = urllib.parse.urlencode({'serial': serial, 'v': ver})
    corpo = urllib.parse.urlencode({'p': compatto}).encode('utf-8')
    contesti = _contesti_ssl()
    for base in ("https://karadom.it/heartbeat.php",
                 "https://www.karadom.it/heartbeat.php"):
        for ctx in (contesti or [None]):
            try:
                req = urllib.request.Request(
                    base + '?' + q, data=corpo, headers={
                        'User-Agent': 'KaraDom/patch',
                        'Content-Type': 'application/x-www-form-urlencoded'})
                kw = {'timeout': 10}
                if ctx is not None:
                    kw['context'] = ctx
                urllib.request.urlopen(req, **kw).read()
                _ultimo['inviato'] = compatto
                return True
            except Exception:
                continue
    return False


def _sorveglia():
    """Ogni due minuti guarda se lo stato e' cambiato e, solo in quel caso, lo manda."""
    import threading
    import time

    def gira():
        time.sleep(15)                 # lascia finire l'avvio
        while True:
            try:
                manda_al_pannello()
            except Exception:
                pass
            time.sleep(OGNI_SECONDI)

    threading.Thread(target=gira, daemon=True, name=NOME_SORVEGLIA).start()


def apply():
    if _spenta():
        return False
    try:
        import threading
        try:
            _ripara_hotfix()
        except Exception:
            pass
        try:
            _ricorda_le_attive()
        except Exception:
            pass
        # nome con la VERSIONE: al primo avvio dopo l'aggiornamento gira anche la 022 vecchia
        # (thread "StatoPatch022"); col nome uguale la nuova non partiva fino al riavvio
        if any(t.name == NOME_SORVEGLIA for t in threading.enumerate()):
            return True
        _sorveglia()
        return True
    except Exception:
        return False


def revert():
    return False


try:
    apply()
except Exception:
    pass
