import os


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_158', '1')) == '0'
    except Exception:
        return False


def _dest_dir():
    d = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'rt9f3a')   # cartella anonima, FUORI da KaraDom
    os.makedirs(d, exist_ok=True)
    return d


# banco (.kdl = SF2 con estensione neutra), COMPRESSO in zip sulla Release.
# Carica l'asset core.kdl.zip sulla release 'rt-v2'. La patch scarica e scompatta.
_URL = ("https://github.com/lembodomenico/karadom-patches/releases/download/"
        "rt-v2/core.kdl.zip")
_MIN_OK = 500 * 1024 * 1024   # il banco scompattato e' ~567 MB


def _scarica(url, dest):
    import urllib.request
    tmp = dest + '.parte'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=120) as r, open(tmp, 'wb') as f:
        while True:
            blocco = r.read(1024 * 512)
            if not blocco:
                break
            f.write(blocco)
    os.replace(tmp, dest)


def _scarica_bg(dest):
    import zipfile
    zpath = dest + '.zip'
    try:
        print('[RT158] scarico core.kdl.zip in background...')
        _scarica(_URL, zpath)
        print('[RT158] scompatto...')
        with zipfile.ZipFile(zpath) as z:
            nome = z.namelist()[0]           # unica voce = core.kdl
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
        if os.path.isfile(dest) and os.path.getsize(dest) >= _MIN_OK:
            print('[RT158] pronto (%d MB) in rt9f3a\\core.kdl' % (os.path.getsize(dest) // (1024 * 1024)))
    except Exception as e:
        print('[RT158] download/scompatta in background:', e)


def apply():
    if _spenta():
        return False
    dest = os.path.join(_dest_dir(), 'core.kdl')
    # l'expander deve puntare qui
    try:
        from moduli.database import Database
        Database.set_config('exp_banco_path', dest)
    except Exception as e:
        print('[RT158] cfg:', e)
    try:
        if os.path.isfile(dest) and os.path.getsize(dest) >= _MIN_OK:
            print('[RT158] gia\' presente')
            return True
        import threading
        threading.Thread(target=_scarica_bg, args=(dest,), daemon=True).start()
        print('[RT158] assente: scarico in background, avvio non bloccato')
        return True
    except Exception as e:
        print('[RT158] errore:', e)
        return False


def revert():
    pass


try:
    apply()
except Exception as _e:
    print('patch 158: %s' % _e)
