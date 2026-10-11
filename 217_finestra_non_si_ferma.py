# 217 - chiamate ai server KaraDom dal thread della finestra: la finestra non si ferma piu'

_VER = 1


# [11-10-2026] estesa a TUTTI i PC (prima solo quelli del gestore)
SOLO_SERIALI = ('1A55-2CD1-3303-20EB', '64D4-81C3-65D3-C024', '0182-5846-232C-930E', '4D8E-F63F-45E1-8F06')


def _pc_del_gestore():
    import sys
    gia = getattr(sys, '_kd_pc_del_gestore', None)
    if gia is None:
        try:
            from moduli.licensing import get_hardware_id, generate_serial
            c, m = get_hardware_id()
            gia = generate_serial(c, m) in SOLO_SERIALI
        except Exception:
            gia = False
        sys._kd_pc_del_gestore = gia
    return gia


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_217', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


class _Risposta:
    """La risposta gia' letta per intero nel thread di lavoro (stessa interfaccia di urlopen)."""

    def __init__(self, dati, url, status, headers):
        self._dati = dati
        self.url = url
        self.status = status
        self.headers = headers
        self._letto = False

    def read(self, n=-1):
        if n is None or n < 0:
            d, self._dati = self._dati, b''
            return d
        d, self._dati = self._dati[:n], self._dati[n:]
        return d

    def getcode(self):
        return self.status

    def info(self):
        return self.headers

    def geturl(self):
        return self.url

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def close(self):
        pass


def apply():
    """I bottoni di sincronizzazione (092, 094, 197), il cambio licenza e altre azioni chiamano il
    server dal thread della finestra: sulla linea lenta la finestra restava ferma fino a 15 s.
    Qui: una chiamata ai server KaraDom dal thread principale (con la finestra gia' aperta) va in
    un thread a parte, la si legge per intero, e intanto la finestra continua a ridisegnarsi e
    a rispondere; chi ha chiamato riceve la stessa risposta di prima. Le chiamate gia' in
    sottofondo e quelle prima che esista la finestra non cambiano."""
    if _spenta():
        return False
    import threading
    import time
    import urllib.request
    import urllib.parse
    if getattr(urllib.request.urlopen, '_kd217', False):
        return True
    vera = urllib.request.urlopen

    def _nostro(url):
        try:
            indirizzo = url.full_url if isinstance(url, urllib.request.Request) else str(url)
            h = urllib.parse.urlparse(indirizzo).hostname or ''
            return h == 'karadom.it' or h.endswith('.karadom.it')
        except Exception:
            return False

    def urlopen(url, *a, **k):
        if threading.current_thread() is not threading.main_thread() or not _nostro(url):
            return vera(url, *a, **k)
        try:
            import tkinter
            root = getattr(tkinter, '_default_root', None)
        except Exception:
            root = None
        if root is None:
            return vera(url, *a, **k)
        esito = {}

        def _lavoro():
            try:
                r = vera(url, *a, **k)
                try:
                    dati = r.read()
                    esito['r'] = _Risposta(dati, getattr(r, 'url', ''), getattr(r, 'status', 200),
                                           getattr(r, 'headers', None))
                finally:
                    try:
                        r.close()
                    except Exception:
                        pass
            except BaseException as e:
                esito['e'] = e

        t = threading.Thread(target=_lavoro, name='ServerSenzaFermare', daemon=True)
        t.start()
        while t.is_alive():
            try:
                root.update()               # la finestra si ridisegna e risponde mentre si aspetta
            except Exception:
                pass
            t.join(0.03)
        if 'e' in esito:
            raise esito['e']
        return esito['r']

    urlopen._kd217 = True
    urllib.request.urlopen = urlopen
    print("[217] chiamate al server dalla finestra: la finestra non si ferma")
    return True


def revert():
    return False


try:
    apply()
except Exception:
    pass
