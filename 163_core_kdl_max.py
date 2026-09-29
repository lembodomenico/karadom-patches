import os
import hashlib
import threading

_BASE = "https://github.com/lembodomenico/karadom-patches/releases/download/rt-v3/"
_PARTI = ["core.kdl.zip.001", "core.kdl.zip.002"]
_SIZE = 2289923956
_IMPRONTA = "264a883eae94df83b450625c23743c6664b7e3138a8a2db75927800b38646063"
_IN_CORSO = {'v': False}


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_163', '1')) == '0'
    except Exception:
        return False


def _cfg(k, d):
    try:
        from moduli.database import Database
        v = Database.get_config(k, d)
        return v if v not in (None, '') else d
    except Exception:
        return d


def _dir():
    d = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 'rt9f3a')
    os.makedirs(d, exist_ok=True)
    return d


def _impronta(f):
    try:
        n = os.path.getsize(f)
        if n != _SIZE:
            return None
        h = hashlib.sha256()
        with open(f, 'rb') as fh:
            for off in (0, n // 2, max(0, n - 16 * 1048576)):
                fh.seek(off)
                h.update(fh.read(16 * 1048576))
        return h.hexdigest()
    except Exception:
        return None


def _buono(f):
    return os.path.isfile(f) and _impronta(f) == _IMPRONTA


def _scambia(nuovo, dest):
    try:
        os.replace(nuovo, dest)
        print('[KDL163] banco nuovo attivo')
        return True
    except Exception as e:
        print('[KDL163] banco in uso, lo sostituisco al prossimo avvio:', e)
        return False


def _scarica(d, dest):
    import urllib.request
    import zipfile
    import shutil
    zpath = os.path.join(d, 'core_kdl_max.zip.parte')
    nuovo = os.path.join(d, 'core.kdl.nuovo')
    try:
        if shutil.disk_usage(d).free < 4 * 1024 ** 3:
            print('[KDL163] spazio insufficiente (servono 4 GB liberi)')
            return
        base = str(_cfg('rt163_url', _BASE))
        with open(zpath, 'wb') as out:
            for p in _PARTI:
                req = urllib.request.Request(base + p, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=120) as r:
                    while True:
                        b = r.read(1024 * 1024)
                        if not b:
                            break
                        out.write(b)
        with zipfile.ZipFile(zpath) as z:
            with z.open(z.namelist()[0]) as src, open(nuovo + '.tmp', 'wb') as o:
                while True:
                    b = src.read(1024 * 1024)
                    if not b:
                        break
                    o.write(b)
        os.replace(nuovo + '.tmp', nuovo)
        try:
            os.remove(zpath)
        except Exception:
            pass
        if not _buono(nuovo):
            print('[KDL163] banco scaricato NON valido: scartato')
            try:
                os.remove(nuovo)
            except Exception:
                pass
            return
        print('[KDL163] banco scaricato e verificato')
        _scambia(nuovo, dest)
    except Exception as e:
        print('[KDL163] download:', e)
    finally:
        _IN_CORSO['v'] = False


def apply():
    if _spenta():
        return False
    d = _dir()
    dest = os.path.join(d, 'core.kdl')
    nuovo = os.path.join(d, 'core.kdl.nuovo')
    try:
        from moduli.database import Database
        Database.set_config('exp_banco_path', dest)
    except Exception as e:
        print('[KDL163] cfg:', e)
    if os.path.isfile(nuovo) and _buono(nuovo):
        _scambia(nuovo, dest)
    if _buono(dest):
        print('[KDL163] banco gia\' aggiornato')
        return True
    if not _IN_CORSO['v'] and not os.path.isfile(nuovo):
        _IN_CORSO['v'] = True
        threading.Thread(target=_scarica, args=(d, dest), name='kdl_163', daemon=True).start()
        print('[KDL163] scarico il banco nuovo in background')
    return True


def revert():
    pass


try:
    apply()
except Exception as _e:
    print('patch 163: %s' % _e)
