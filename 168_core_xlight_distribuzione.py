import os
import hashlib
import threading

_URL = ("https://github.com/lembodomenico/karadom-patches/releases/download/"
        "rt-v4/core.kdl.zip")
_SIZE = 280219422
_SHA = "990af177029baefeb849215ad09ac527e37e5657ef4654edbc24f5192625b242"
_IN_CORSO = {'v': False}


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_168', '1')) == '0'
    except Exception:
        return False


def _set(k, v):
    try:
        from moduli.database import Database
        Database.set_config(k, v)
    except Exception:
        pass


def _dir():
    d = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 'rt9f3a')
    os.makedirs(d, exist_ok=True)
    return d


def _integro(dest):
    try:
        if not os.path.isfile(dest) or os.path.getsize(dest) != _SIZE:
            return False
        h = hashlib.sha256()
        with open(dest, 'rb') as f:
            for b in iter(lambda: f.read(1024 * 1024), b''):
                h.update(b)
        return h.hexdigest() == _SHA
    except Exception:
        return False


def _scarica(url, dest):
    import urllib.request
    tmp = dest + '.parte'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=180) as r, open(tmp, 'wb') as f:
        while True:
            blocco = r.read(1024 * 512)
            if not blocco:
                break
            f.write(blocco)
    os.replace(tmp, dest)


def _installa_bg(dest):
    import zipfile
    zpath = dest + '.zip'
    try:
        print('[RT168] scarico core.kdl.zip...')
        _scarica(_URL, zpath)
        print('[RT168] scompatto...')
        with zipfile.ZipFile(zpath) as z:
            nome = z.namelist()[0]
            with z.open(nome) as src, open(dest + '.parte', 'wb') as out:
                while True:
                    b = src.read(1024 * 512)
                    if not b:
                        break
                    out.write(b)
        os.replace(dest + '.parte', dest)
        try:
            os.remove(zpath)
        except Exception:
            pass
        if _integro(dest):
            print('[RT168] core.kdl pronto (%d MB) in rt9f3a' % (os.path.getsize(dest) // (1024 * 1024)))
        else:
            print('[RT168] core.kdl scaricato ma NON integro (size/hash) -> rimuovo')
            try:
                os.remove(dest)
            except Exception:
                pass
    except Exception as e:
        print('[RT168] errore download:', e)
    finally:
        _IN_CORSO['v'] = False


def apply():
    if _spenta():
        return False
    dest = os.path.join(_dir(), 'core.kdl')
    # ferma la vecchia distribuzione HD MAX (2,29 GB) e punta al nuovo banco
    _set('patch_163', '0')
    _set('exp_banco_default', dest)
    _set('exp_banco_path', dest)
    if _integro(dest):
        print('[RT168] core.kdl gia\' presente e integro')
        return True
    if _IN_CORSO['v']:
        return True
    _IN_CORSO['v'] = True
    threading.Thread(target=_installa_bg, args=(dest,), daemon=True).start()
    return True


try:
    apply()
except Exception as _e:
    print('patch 168: %s' % _e)
