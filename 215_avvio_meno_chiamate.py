# 215 - avvio: meno chiamate di controllo al pannello, e "sono online?" che non sbaglia sulle reti filtrate

_VER = 1
VALE_PER = 60          # una domanda di stato a debug.php fatta di nuovo entro 60 s riceve la stessa risposta


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
        return str(Database.get_config('patch_215', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


class _Risposta:
    """Risposta gia' avuta, restituita di nuovo (stessa interfaccia minima di urlopen)."""

    def __init__(self, dati, url):
        self._dati = dati
        self.url = url
        self.status = 200

    def read(self, *a):
        return self._dati

    def getcode(self):
        return 200

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def close(self):
        pass


def _urlopen():
    """All'avvio 3 patch (025 diario, 027 spia MIDI, 118 riscarica) chiedono a debug.php la
    stessa cosa, e la 018 manda a heartbeat.php l'elenco patch che la 022 manda (completo)
    pochi secondi dopo. Qui: domanda di stato uguale entro 60 s = una sola in rete; il
    heartbeat della 018 (GET con 'p=') si salta. Tutto il resto passa com'e'."""
    import time
    import threading
    import urllib.request
    import urllib.parse
    if getattr(urllib.request.urlopen, '_kd215', False):
        return
    vera = urllib.request.urlopen
    ricordo = {}
    blocco = threading.Lock()

    def urlopen(url, *a, **k):
        try:
            req = url if isinstance(url, urllib.request.Request) else None
            indirizzo = req.full_url if req is not None else str(url)
            get = (req is None or req.data is None) and not (len(a) >= 1 and a[0] is not None) and k.get('data') is None
            u = urllib.parse.urlparse(indirizzo)
            if get and u.hostname in ('karadom.it', 'www.karadom.it'):
                if u.path == '/heartbeat.php' and 'p' in urllib.parse.parse_qs(u.query):
                    return _Risposta(b'{"ok":true,"saltato":"215: lo manda la 022"}', indirizzo)
                if u.path == '/debug.php':
                    chiave = u.query
                    with blocco:
                        r = ricordo.get(chiave)
                        if r and time.time() - r[0] < VALE_PER:
                            return _Risposta(r[1], indirizzo)
                    risposta = vera(url, *a, **k)
                    dati = risposta.read()
                    with blocco:
                        ricordo[chiave] = (time.time(), dati)
                    return _Risposta(dati, indirizzo)
        except Exception:
            pass
        return vera(url, *a, **k)

    urlopen._kd215 = True
    urllib.request.urlopen = urlopen


def _online():
    """"Sono online?" provava solo i DNS 1.1.1.1:53 e 8.8.8.8:53: sulle reti che li bloccano
    (hotel, aziende) KaraDom si credeva offline e saltava licenza, patch e aggiornamenti.
    Se quelli non rispondono si prova anche il server KaraDom (porta 443)."""
    import socket

    def _karadom(timeout=1.5):
        try:
            socket.create_connection(('karadom.it', 443), timeout=timeout).close()
            return True
        except Exception:
            return False

    for nome_mod, nome_fun in (('moduli.updater', '_is_online'), ('moduli.licensing', '_is_online_quick')):
        try:
            mod = __import__(nome_mod, fromlist=[nome_fun])
            vera = getattr(mod, nome_fun, None)
            if vera is None or getattr(vera, '_kd215', False):
                continue

            def nuova(*a, __vera=vera, **k):
                return __vera(*a, **k) or _karadom()

            nuova._kd215 = True
            setattr(mod, nome_fun, nuova)
        except Exception:
            continue


def apply():
    if _spenta():
        return False
    try:
        _urlopen()
    except Exception as e:
        print('[215] chiamate di avvio: %s' % e)
    try:
        _online()
    except Exception as e:
        print('[215] online: %s' % e)
    print('[215] avvio: domande di stato unite, online anche sulle reti filtrate')
    return True


def revert():
    return False


try:
    apply()
except Exception:
    pass
