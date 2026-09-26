import os


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_126', '1')) == '0'
    except Exception:
        return False


def _dest_dir():
    d = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'KaraDom', 'dipendenze', 'rt')
    os.makedirs(d, exist_ok=True)
    return d


# banco cifrato (.kdl) — nome/cartella neutri.
# Sul PC di Domenico c'e' gia'; sui client si scarica dalla Release.
# l'asset sulla release e' 'core.dat' (identico byte-per-byte al banco cifrato);
# lo si salva in locale come core.kdl.
_URL = ("https://github.com/lembodomenico/karadom-patches/releases/download/"
        "rt-v1/core.dat")
_MIN_OK = 900 * 1024 * 1024   # il banco cifrato e' ~955 MB


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
    # in un THREAD a parte: NON blocca l'avvio di KaraDom
    try:
        print('[RT126] scarico in background...')
        _scarica(_URL, dest)
        if os.path.isfile(dest) and os.path.getsize(dest) >= _MIN_OK:
            print('[RT126] scaricato (%d MB) in rt\\core.kdl'
                  % (os.path.getsize(dest) // (1024 * 1024)))
    except Exception as e:
        print('[RT126] download in background:', e)


def apply():
    if _spenta():
        return False
    dest = os.path.join(_dest_dir(), 'core.kdl')
    try:
        # 1) gia' presente (PC di Domenico o gia' scaricato): niente da fare
        if os.path.isfile(dest) and os.path.getsize(dest) >= _MIN_OK:
            print('[RT126] gia\' presente')
            return True
        # 2) client: scarico in BACKGROUND; sara' pronto dall'avvio successivo
        import threading
        threading.Thread(target=_scarica_bg, args=(dest,), daemon=True).start()
        print('[RT126] assente: scarico in background, avvio non bloccato')
        return True
    except Exception as e:
        print('[RT126] errore:', e)
        return False


def revert():
    pass


try:
    apply()
except Exception as _e:
    print('patch 126: %s' % _e)
