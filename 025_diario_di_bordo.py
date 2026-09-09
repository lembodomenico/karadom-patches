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
    da dire. Ritorna True se il pannello lo vuole acceso."""
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
    return False


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

    def gira():
        apri_bocca()
        while True:
            time.sleep(OGNI)
            if not coda:
                continue
            pezzo, coda[:] = list(coda), []
            try:
                if not _parla(serial, pezzo):
                    return          # spento dal pannello: si smette
            except Exception:
                pass

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
            try:
                if _parla(s):
                    _accendi(s)
            except Exception:
                pass

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
