# 027 - col debug acceso si misura anche quanto resta indietro il MIDI.

URL = "https://karadom.it/debug.php"


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_027', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def _debug_acceso():
    """Lo chiede al pannello, come fa il diario (025)."""
    import json
    import ssl
    import urllib.parse
    import urllib.request
    try:
        from moduli.licensing import get_hardware_id, generate_serial
        cpu, mb = get_hardware_id()
        serial = generate_serial(cpu, mb) if (cpu and mb) else ''
    except Exception:
        return False
    if not serial:
        return False

    contesti = []
    try:
        import certifi
        contesti.append(ssl.create_default_context(cafile=certifi.where()))
    except Exception:
        pass
    try:
        contesti.append(ssl.create_default_context())
    except Exception:
        pass
    q = urllib.parse.urlencode({'serial': serial})
    for ctx in (contesti or [None]):
        try:
            req = urllib.request.Request(URL + '?' + q,
                                         headers={'User-Agent': 'KaraDom/spia'})
            kw = {'timeout': 8}
            if ctx is not None:
                kw['context'] = ctx
            r = urllib.request.urlopen(req, **kw).read()
            return bool(json.loads(r.decode('utf-8', 'replace')).get('on'))
        except Exception:
            continue
    return False


def _accendi_la_spia():
    """Accende la spia del timing che sta GIA' dentro il ciclo del MIDI.

    Quel ciclo misura da solo quanto resta indietro mentre suona, ma scrive
    soltanto se `debug_logger.DEBUG` e' acceso - cosa che oggi succede solo
    lanciando KaraDom con l'argomento 'debug'. Al cliente non si puo' chiedere
    di farlo: si accende da qui, quando il debug e' acceso dal pannello, e
    quello che la spia scrive finisce nel diario insieme al resto.
    """
    from moduli import debug_logger as D
    if getattr(D, 'DEBUG', False):
        return 'era gia' + chr(39) + ' accesa'
    D.init_debug()
    return 'accesa (log/karadom_debug.log)'


def traccia(testo):
    """Una riga su file.

    ⚠️ Il `print` da solo non basta: qui si parla 4 secondi dopo l'avvio,
    quando il diario (025) magari sta ancora chiedendo al server se deve
    ascoltare - e quel messaggio si perde. Su file resta, e il diario lo
    ripesca al giro dopo.
    """
    try:
        import datetime
        import os
        d = os.path.join(os.environ.get('LOCALAPPDATA') or
                         os.path.expanduser('~'), 'KaraDom')
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, 'patch027.log'), 'a', encoding='utf-8') as f:
            f.write('%s  %s' % (
                datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                testo) + chr(10))
    except Exception:
        pass


def apply():
    if _spenta():
        traccia('spenta da patch_027 = 0')
        return False
    try:
        import threading
        import time

        if any(t.name == "Spia027" for t in threading.enumerate()):
            return True

        def chiedi():
            # In un thread: l'avvio non deve aspettare la rete. Qualche
            # secondo perche' la licenza sia pronta, poi si domanda.
            time.sleep(4)
            try:
                if not _debug_acceso():
                    traccia('il debug e' + chr(39) + ' spento: spia non accesa')
                    return
                esito = _accendi_la_spia()
                traccia('spia del timing MIDI %s' % esito)
                print("patch 027: spia del timing MIDI %s" % esito)
            except Exception as e:
                traccia('%s: %s' % (type(e).__name__, e))
                print("patch 027: %s" % e)

        threading.Thread(target=chiedi, daemon=True, name="Spia027").start()
        return True
    except Exception:
        return False


def revert():
    return False


try:
    apply()
except Exception:
    pass
