# 076 - scarica assistenza
URL_ZIP = 'https://iocanto.karadom.it/dl/AssistenzaKD.zip'
URL_VER = 'https://iocanto.karadom.it/dl/AssistenzaKD.ver'


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_076', '1')) == '0'
    except Exception:
        return False


def _destdir():
    import os
    base = os.environ.get('LOCALAPPDATA') or os.path.expanduser('~')
    return os.path.join(base, 'KaraDom', 'AssistenzaKD')


def _leggi_ver(path):
    import os
    try:
        if os.path.isfile(path):
            return open(path, encoding='utf-8').read().strip()
    except Exception:
        pass
    return ''


def _remota(url):
    import urllib.request
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            return (r.read(64) or b'').decode('utf-8', 'ignore').strip()
    except Exception:
        return ''


def _in_uso():
    # se AssistenzaKD e' aperto i file sono bloccati: si rimanda al prossimo avvio
    import os
    import subprocess
    if os.name != 'nt':
        return False
    nowin = 0x08000000
    for nome in ('AssistenzaKD_qs.exe', 'AssistenzaKD.exe'):
        try:
            out = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq ' + nome,
                                  '/FO', 'CSV', '/NH'], capture_output=True,
                                 text=True, timeout=5, creationflags=nowin).stdout or ''
            if nome.lower() in out.lower():
                return True
        except Exception:
            pass
    return False


def _trova_root(top):
    # cartella (dentro l'estratto) che contiene davvero l'exe
    import os
    for r, _d, files in os.walk(top):
        low = [f.lower() for f in files]
        if 'assistenzakd_qs.exe' in low or 'assistenzakd.exe' in low:
            return r
    return top


def _pulisci_vecchi():
    # il single-file vecchio in dipendenze/ (best effort: su Program Files puo' fallire)
    import os
    import sys
    try:
        try:
            from moduli.constants import get_base_path
            bp = get_base_path()
        except Exception:
            bp = os.path.dirname(os.path.abspath(sys.argv[0]))
        for rel in ('AssistenzaKD.exe', 'AssistenzaKD_qs.exe', 'rustdesk.exe'):
            p = os.path.join(bp, 'dipendenze', rel)
            try:
                if os.path.isfile(p):
                    os.remove(p)
            except Exception:
                pass
    except Exception:
        pass


def _aggiorna():
    import os
    import shutil
    import tempfile
    import zipfile
    import urllib.request

    dest = _destdir()
    verfile = os.path.join(dest, '.ver')
    exe_ok = (os.path.isfile(os.path.join(dest, 'AssistenzaKD_qs.exe')) or
              os.path.isfile(os.path.join(dest, 'AssistenzaKD.exe')))

    remoto = _remota(URL_VER)
    if not remoto:
        return  # server non raggiungibile: non blocco nulla
    if exe_ok and _leggi_ver(verfile) == remoto:
        return  # gia' aggiornato

    if _in_uso():
        return  # riprovo al prossimo avvio (file bloccati)

    tmpzip = os.path.join(tempfile.gettempdir(), 'AssistenzaKD_dl.zip')
    tmpdir = os.path.join(tempfile.gettempdir(), 'AssistenzaKD_dl')
    try:
        with urllib.request.urlopen(URL_ZIP, timeout=180) as r, open(tmpzip, 'wb') as f:
            shutil.copyfileobj(r, f)
        shutil.rmtree(tmpdir, ignore_errors=True)
        with zipfile.ZipFile(tmpzip) as z:
            z.extractall(tmpdir)
    except Exception:
        try:
            os.remove(tmpzip)
        except Exception:
            pass
        return

    src = _trova_root(tmpdir)
    try:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        nuovo = dest + '.new'
        shutil.rmtree(nuovo, ignore_errors=True)
        shutil.copytree(src, nuovo)
        shutil.rmtree(dest, ignore_errors=True)   # elimina quella attuale
        os.replace(nuovo, dest)
        open(verfile, 'w', encoding='utf-8').write(remoto)
    except Exception:
        return
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
        try:
            os.remove(tmpzip)
        except Exception:
            pass

    _pulisci_vecchi()


def apply():
    if _spenta():
        return False
    import threading
    threading.Thread(target=_aggiorna, daemon=True).start()
    return True


def revert():
    return False


try:
    apply()
except Exception:
    pass
