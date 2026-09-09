# 025 - il programma puo' raccontare cosa fa, se glielo si chiede dal pannello.

URL = "https://karadom.it/debug.php"
OGNI = 20               # secondi fra un invio e l'altro
MAX_CODA = 2000         # righe tenute in memoria fra un invio e l'altro


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_025', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def _serial():
    try:
        from moduli.licensing import get_hardware_id, generate_serial
        cpu, mb = get_hardware_id()
        return generate_serial(cpu, mb) if (cpu and mb) else ''
    except Exception:
        return ''


def _contesti():
    """Gli stessi contesti SSL dell'updater: nell'eseguibile compilato una
    urlopen liscia su https puo' non trovare i certificati."""
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
    return fuori or [None]


def _parla(serial, righe=None):
    """Chiede se il debug e' acceso e, gia' che c'e', consegna quello che ha
    da dire.

    Tre risposte, non due:
      True  - il pannello lo vuole acceso
      False - il pannello lo ha spento
      None  - NON CI SONO RIUSCITO (rete, timeout, server giu')

    ⛔ La terza non e' un dettaglio: prima "non ci sono riuscito" tornava
       False come "spento", e al primo intoppo di rete il diario si chiudeva
       per sempre - misurato, un solo errore e il thread muore. Da quel
       momento il programma continuava a lavorare senza che nessuno lo
       ascoltasse piu'.
    """
    import json
    import urllib.parse
    import urllib.request

    corpo = None
    if righe:
        corpo = json.dumps({'righe': righe}, ensure_ascii=False).encode('utf-8')

    q = urllib.parse.urlencode({'serial': serial})
    for ctx in _contesti():
        try:
            req = urllib.request.Request(
                URL + '?' + q, data=corpo,
                headers={'User-Agent': 'KaraDom/debug',
                         'Content-Type': 'application/json'})
            kw = {'timeout': 10}
            if ctx is not None:
                kw['context'] = ctx
            risposta = urllib.request.urlopen(req, **kw).read()
            return bool(json.loads(risposta.decode('utf-8', 'replace')).get('on'))
        except Exception:
            continue
    return None         # nessun contesto ha funzionato: non lo so


class _Eco(object):
    """Si mette in mezzo fra il programma e lo schermo: lascia passare tutto
    com'era e ne tiene una copia da mandare al pannello.

    ⚠️ Non deve MAI rompere una print: se qui dentro va storto qualcosa, il
    testo deve arrivare comunque dove sarebbe andato."""

    def __init__(self, vero, coda):
        self._vero = vero
        self._coda = coda

    def write(self, testo):
        try:
            if self._vero is not None:
                self._vero.write(testo)
        except Exception:
            pass
        try:
            for r in str(testo).splitlines():
                if r.strip():
                    self._coda.append(r[:2000])
                    if len(self._coda) > MAX_CODA:
                        del self._coda[0]
        except Exception:
            pass

    def flush(self):
        try:
            if self._vero is not None:
                self._vero.flush()
        except Exception:
            pass

    def __getattr__(self, nome):
        return getattr(self._vero, nome)


def _accendi(serial):
    import sys
    import threading
    import time

    coda = []
    try:
        sys.stdout = _Eco(sys.stdout, coda)
        sys.stderr = _Eco(sys.stderr, coda)
    except Exception:
        return

    def apri_bocca():
        # cosa c'e' su questo PC, cosi' il diario comincia con le cose utili
        try:
            from moduli import hotfix
            print("[diario] patch attive: %s"
                  % ", ".join(sorted(getattr(hotfix, 'APPLICATE', []) or [])))
        except Exception:
            pass
        try:
            import platform
            print("[diario] %s, Python %s" % (platform.platform(),
                                              platform.python_version()))
        except Exception:
            pass

        # ⭐ I file di traccia scritti PRIMA che il diario si accendesse.
        #    Le patch lavorano all'avvio, quando qui non si stava ancora
        #    ascoltando: senza questo, il pezzo piu' interessante - perche'
        #    una patch non e' entrata in funzione - non si vedrebbe mai.
        import os
        base = os.path.join(os.environ.get('LOCALAPPDATA') or
                            os.path.expanduser('~'), 'KaraDom')
        da_leggere = [os.path.join(base, n) for n in os.listdir(base)
                      if n.endswith('.log')] if os.path.isdir(base) else []
        try:
            from moduli.licensing import _get_base_internal_path
            cartella_log = os.path.join(str(_get_base_internal_path().parent), 'log')
            for n in ('crash_startup.log', 'karadom_debug.log'):
                p = os.path.join(cartella_log, n)
                if os.path.isfile(p):
                    da_leggere.append(p)
        except Exception:
            pass
        for f in da_leggere[:6]:
            try:
                righe = open(f, encoding='utf-8', errors='replace').read().splitlines()
                if not righe:
                    continue
                print("[diario] --- %s (ultime %d righe) ---"
                      % (os.path.basename(f), min(20, len(righe))))
                for r in righe[-20:]:
                    if r.strip():
                        print("[diario]   " + r[:400])
            except Exception:
                pass

    # ⭐ La spia del timing del MIDI scrive su FILE, non a schermo: nel
    #    programma compilato `dbg()` non passa da print, quindi senza seguire
    #    il file quelle misure - le uniche che dicono quanto il MIDI resta
    #    indietro - non arriverebbero mai qui.
    coda_file = {'dove': None, 'letto': 0}

    def segui_il_file():
        import os
        if coda_file['dove'] is None:
            try:
                from moduli.licensing import _get_base_internal_path
                p = os.path.join(str(_get_base_internal_path().parent),
                                 'log', 'karadom_debug.log')
            except Exception:
                return
            if not os.path.isfile(p):
                return
            coda_file['dove'] = p
            coda_file['letto'] = os.path.getsize(p)   # si parte da adesso
            return
        p = coda_file['dove']
        try:
            quanto = os.path.getsize(p)
            if quanto < coda_file['letto']:
                coda_file['letto'] = 0                # il file e' ripartito
            if quanto <= coda_file['letto']:
                return
            with open(p, 'r', encoding='utf-8', errors='replace') as f:
                f.seek(coda_file['letto'])
                nuove = f.read()
                coda_file['letto'] = f.tell()
            for r in nuove.splitlines():
                if r.strip():
                    coda.append(r[:2000])
        except Exception:
            pass

    def gira():
        apri_bocca()
        while True:
            time.sleep(OGNI)
            try:
                segui_il_file()
            except Exception:
                pass
            if not coda:
                continue
            pezzo, coda[:] = list(coda), []
            try:
                esito = _parla(serial, pezzo)
            except Exception:
                esito = None
            if esito is None:
                # ⛔ Non ci sono riuscito: le righe NON si buttano. Tornano
                #    in testa alla coda e si riprova al giro dopo. Prima
                #    sparivano - erano gia' state tolte - e per giunta il
                #    diario si chiudeva, quindi di tutto quello che il
                #    programma faceva dopo non restava traccia.
                coda[:0] = pezzo
                if len(coda) > MAX_CODA:
                    del coda[:len(coda) - MAX_CODA]   # le piu' vecchie cedono
                continue
            if esito is False:
                return              # spento dal pannello: si smette davvero

    threading.Thread(target=gira, daemon=True, name="Diario025").start()


def apply():
    if _spenta():
        return False
    try:
        import threading
        import time

        if any(t.name == "Diario025Avvio" for t in threading.enumerate()):
            return True

        def chiedi():
            # ⚠️ Si chiede al server, quindi in un thread: l'avvio non deve
            #    aspettare la rete. Un attimo di pazienza perche' la licenza
            #    sia pronta, poi si domanda.
            time.sleep(3)
            s = _serial()
            if not s:
                return
            # ⚠️ Se al primo colpo la rete non risponde (None) NON si molla:
            #    all'avvio la connessione puo' non essere ancora pronta, e
            #    rinunciando li' il debug acceso dal pannello non partiva
            #    fino al riavvio successivo. Si riprova qualche volta,
            #    aspettando un po' di piu' ogni giro, poi basta.
            for attesa in (0, 20, 40, 80, 160):
                if attesa:
                    time.sleep(attesa)
                try:
                    esito = _parla(s)
                except Exception:
                    esito = None
                if esito is True:
                    _accendi(s)
                    return
                if esito is False:
                    return          # il pannello dice di stare zitti

        threading.Thread(target=chiedi, daemon=True, name="Diario025Avvio").start()
        return True
    except Exception:
        return False


def revert():
    return False


try:
    apply()
except Exception:
    pass
