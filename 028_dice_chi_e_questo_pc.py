# 028 - il programma dice al server su quale computer sta girando.

URLS = ("https://karadom.it/heartbeat.php",
        "https://www.karadom.it/heartbeat.php")


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_028', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def traccia(testo):
    try:
        import datetime
        import os
        d = os.path.join(os.environ.get('LOCALAPPDATA') or
                         os.path.expanduser('~'), 'KaraDom')
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, 'patch028.log'), 'a', encoding='utf-8') as f:
            f.write('%s  %s' % (
                datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                testo) + chr(10))
    except Exception:
        pass


def _contesti():
    """Gli stessi contesti SSL dell'updater: nel programma compilato una
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


def chi_sono():
    """(serial, nome del PC, impronta dell'hardware).

    Sono gli stessi tre valori che il programma calcola gia' per la licenza:
    qui non se ne inventa nessuno, si rileggono e basta.
    """
    import hashlib
    import socket
    from moduli.licensing import get_hardware_id, generate_serial

    cpu, mb = get_hardware_id()
    serial = generate_serial(cpu, mb) if (cpu and mb) else ''

    pc = hw = ''
    try:
        # La strada buona: la funzione che usa la licenza.
        from moduli.licensing import _get_pc_fingerprint_from_current_pc
        hw, pc = _get_pc_fingerprint_from_current_pc()
    except Exception:
        pass
    # Se in questo eseguibile quella funzione non c'e', si rifa' lo stesso
    # conto a mano: deve venire IDENTICA a quella scritta sulla licenza, se no
    # nel pannello lo stesso computer comparirebbe due volte.
    if not hw:
        try:
            if cpu or mb:
                grezzo = '%s|%s' % (cpu or '', mb or '')
                hw = hashlib.sha256(grezzo.encode('utf-8')).hexdigest()[:32].upper()
        except Exception:
            hw = ''
    if not pc:
        try:
            pc = socket.gethostname() or ''
        except Exception:
            pc = ''
    return serial, pc, hw


def _versione():
    for dove, come in (("moduli.versione", "APP_VERSION"),
                       ("moduli.ui", "APP_VERSION"),
                       ("moduli.updater", "CURRENT_VERSION")):
        try:
            v = str(getattr(__import__(dove, fromlist=[come]), come) or '')
            if v:
                return v
        except Exception:
            continue
    return ''


def presentati():
    """Un solo colpo: nome del PC e impronta al server.

    Durante una sessione questi valori non cambiano mai, quindi si mandano una
    volta e basta. Il battito normale continua per conto suo.
    """
    import urllib.parse
    import urllib.request

    serial, pc, hw = chi_sono()
    if not serial:
        traccia('niente seriale: non si manda niente')
        return False
    if not pc and not hw:
        traccia('ne' + chr(39) + ' nome PC ne' + chr(39) + ' impronta: niente da dire')
        return False

    q = urllib.parse.urlencode({'serial': serial, 'v': _versione(),
                                'pc': pc, 'hw': hw})
    contesti = _contesti()
    for base in URLS:
        for ctx in contesti:
            try:
                req = urllib.request.Request(
                    base + '?' + q, headers={'User-Agent': 'KaraDom/chisono'})
                kw = {'timeout': 10}
                if ctx is not None:
                    kw['context'] = ctx
                urllib.request.urlopen(req, **kw).read()
                traccia('detto al server: pc=%s hw=%s' % (pc, hw[:8]))
                return True
            except Exception as e:
                ultimo = '%s: %s' % (type(e).__name__, e)
                continue
    traccia('non ci sono riuscito (%s)' % locals().get('ultimo', 'boh'))
    return False


def apply():
    if _spenta():
        traccia('spenta da patch_028 = 0')
        return False
    try:
        import threading
        import time

        if any(t.name == "ChiSono028" for t in threading.enumerate()):
            return True

        def lavora():
            # In un thread: l'avvio non deve aspettare la rete. Qualche
            # secondo perche' la licenza sia pronta, poi si parla.
            time.sleep(6)
            try:
                presentati()
            except Exception as e:
                traccia('%s: %s' % (type(e).__name__, e))

        threading.Thread(target=lavora, daemon=True, name="ChiSono028").start()
        return True
    except Exception:
        return False


def revert():
    return False


try:
    apply()
except Exception:
    pass
