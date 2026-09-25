import threading
import time
import os
import json
import urllib.request

DEBUG_URL = 'https://karadom.it/debug.php'


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_118', '1')) == '0'
    except Exception:
        return False


def _serial():
    try:
        from moduli.licensing import get_hardware_id, generate_serial
        cpu, mb = get_hardware_id()
        return generate_serial(cpu, mb)
    except Exception:
        return ''


def _patches_dir():
    try:
        from moduli.hotfix import patches_dir
        return patches_dir()
    except Exception:
        base = os.environ.get('LOCALAPPDATA') or os.path.expanduser('~')
        return os.path.join(base, 'KaraDom', 'patches')


def _ordine(serial):
    try:
        req = urllib.request.Request(DEBUG_URL + '?serial=' + serial,
                                     headers={'Cache-Control': 'no-cache'})
        with urllib.request.urlopen(req, timeout=8) as r:
            d = json.loads(r.read().decode('utf-8', 'replace'))
        return str(d.get('patch_reset', '') or '').strip()
    except Exception:
        return ''


def _ack(serial):
    try:
        data = json.dumps({'patch_ack': 1}).encode('utf-8')
        req = urllib.request.Request(DEBUG_URL + '?serial=' + serial, data=data,
                                     headers={'Content-Type': 'application/json'})
        urllib.request.urlopen(req, timeout=8).read()
    except Exception:
        pass


def _elimina(d, quali):
    numeri = None
    if quali != '*':
        numeri = set(t for t in quali.replace(',', ' ').split() if t.isdigit())
        if not numeri:
            return []
    tolti = []
    try:
        files = os.listdir(d)
    except Exception:
        return tolti
    for f in files:
        if f.endswith('.py.sig'):
            stem = f[:-7]
        elif f.endswith('.py'):
            stem = f[:-3]
        else:
            continue
        num = stem.split('_', 1)[0]
        if num == '002':
            continue                      # la 002 riscarica le altre: mai toglierla
        if numeri is not None and num not in numeri:
            continue
        if os.path.exists(os.path.join(d, stem + '.prova')):
            continue                      # patch di PROVA locale: non toccare
        try:
            os.remove(os.path.join(d, f))
            tolti.append(f)
        except Exception:
            pass
    return tolti


def _lavoro():
    if _spenta():
        return
    time.sleep(12)                        # dopo l'avvio, a programma su
    s = _serial()
    if not s:
        return
    quali = _ordine(s)
    if not quali:
        return
    print('[RISCARICA118] ordine dal pannello: patch da riscaricare =', quali)
    d = _patches_dir()
    tolti = _elimina(d, quali)
    print('[RISCARICA118] rimosse %d patch locali: %s' % (len(tolti), tolti[:12]))
    # le riscarico SUBITO (fresche): essendo ora assenti, la 002 le riprende e riapplica
    try:
        from moduli.updater import check_and_update_patches
        check_and_update_patches()
        print('[RISCARICA118] riscarico avviato')
    except Exception as e:
        print('[RISCARICA118] riscarico (partira\' alla riapertura):', e)
    _ack(s)
    print('[RISCARICA118] ordine azzerato.')


def apply():
    try:
        threading.Thread(target=_lavoro, daemon=True, name='riscarica-118').start()
    except Exception as e:
        print('[RISCARICA118]', e)
    return True


try:
    apply()
except Exception as _e:
    print('patch 118: %s' % _e)
