# 103 - scarica l'expander software (exe + banco) dal server, dove abilitato
URL_ZIP = 'https://iocanto.karadom.it/dl/Expander.zip'
URL_VER = 'https://iocanto.karadom.it/dl/Expander.ver'
EXE = 'KaraDom Expander.exe'


def _abilitato():
    # NON scarica 80 MB su tutti: solo dove il gestore ha acceso l'expander software.
    # Si accende con: Database.set_config('expander_software', '1') sul PC voluto.
    try:
        from moduli.database import Database
        if str(Database.get_config('patch_103', '1')) == '0':
            return False
        return str(Database.get_config('expander_software', '0')) == '1'
    except Exception:
        return False


def _destdir():
    import os
    base = os.environ.get('LOCALAPPDATA') or os.path.expanduser('~')
    return os.path.join(base, 'KaraDom', 'dipendenze', 'Expander')


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
    # se l'expander e' aperto l'exe e' bloccato: si rimanda al prossimo avvio
    import os
    import subprocess
    if os.name != 'nt':
        return False
    nowin = 0x08000000
    try:
        out = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq ' + EXE,
                              '/FO', 'CSV', '/NH'], capture_output=True,
                             text=True, timeout=5, creationflags=nowin).stdout or ''
        return EXE.lower() in out.lower()
    except Exception:
        return False


def _trova_root(top):
    # cartella (dentro l'estratto) che contiene davvero l'exe
    import os
    for r, _d, files in os.walk(top):
        if EXE.lower() in [f.lower() for f in files]:
            return r
    return top


def _copia_dentro(src, dest):
    # copia i file dell'estratto DENTRO la cartella Expander SENZA cancellarla:
    # cosi' NON tocca overlay.sf2 / expander.cfg / 099_spia.txt gia' presenti.
    import os
    import shutil
    os.makedirs(dest, exist_ok=True)
    for r, dirs, files in os.walk(src):
        rel = os.path.relpath(r, src)
        outdir = dest if rel == '.' else os.path.join(dest, rel)
        os.makedirs(outdir, exist_ok=True)
        for f in files:
            try:
                shutil.copy2(os.path.join(r, f), os.path.join(outdir, f))
            except Exception:
                pass


def _driver_ok():
    # il driver teVirtualMIDI (dentro il setup di loopMIDI) e' installato?
    import os
    pf = os.environ.get('PROGRAMFILES', r'C:\Program Files')
    return (os.path.isfile(os.path.join(pf, 'Tobias Erichsen', 'teVirtualMIDI', 'teVirtualMIDI64.sys'))
            or os.path.isfile(os.path.join(pf, 'Tobias Erichsen', 'loopMIDI', 'loopMIDI.exe')))


def _proponi_driver(dest):
    # Senza il driver kernel loopMIDI non crea la porta MIDI. Il setup ufficiale
    # (firmato) e' nel pacchetto: lo apro in modo VISIBILE (l'utente vede la
    # finestra e conferma l'UAC), una volta sola (marcatore .driver_lanciato).
    # NIENTE installazione silenziosa/elevata di nascosto.
    import os
    if os.name != 'nt' or _driver_ok():
        return
    setup = os.path.join(dest, 'loopMIDISetup.exe')
    if not os.path.isfile(setup):
        return
    marker = os.path.join(dest, '.driver_lanciato')
    if os.path.isfile(marker):
        return  # gia' proposto: non riaprirlo a ogni avvio
    try:
        os.startfile(setup)   # apre il wizard ufficiale; l'UAC lo gestisce Windows
        open(marker, 'w').write('1')
        print('[EXP] aperto il setup del driver loopMIDI (serve per la porta MIDI)')
    except Exception as e:
        print('[EXP] apertura setup driver:', e)


def _aggiorna():
    import os
    import shutil
    import tempfile
    import zipfile
    import urllib.request

    dest = _destdir()
    verfile = os.path.join(dest, '.ver')
    exe_ok = os.path.isfile(os.path.join(dest, EXE))

    remoto = _remota(URL_VER)
    if not remoto:
        return  # server non raggiungibile: non blocco nulla
    if exe_ok and _leggi_ver(verfile) == remoto:
        return  # gia' aggiornato

    if exe_ok and _in_uso():
        return  # aggiornamento rimandato: file in uso (riprovo al prossimo avvio)

    tmpzip = os.path.join(tempfile.gettempdir(), 'Expander_dl.zip')
    tmpdir = os.path.join(tempfile.gettempdir(), 'Expander_dl')
    try:
        with urllib.request.urlopen(URL_ZIP, timeout=600) as r, open(tmpzip, 'wb') as f:
            shutil.copyfileobj(r, f)
        shutil.rmtree(tmpdir, ignore_errors=True)
        with zipfile.ZipFile(tmpzip) as z:
            z.extractall(tmpdir)
    except Exception as e:
        print('[EXP] scarico expander:', e)
        try:
            os.remove(tmpzip)
        except Exception:
            pass
        return

    src = _trova_root(tmpdir)
    try:
        _copia_dentro(src, dest)
        open(verfile, 'w', encoding='utf-8').write(remoto)
        print('[EXP] expander software installato/aggiornato (v%s)' % remoto)
        _proponi_driver(dest)   # se manca il driver MIDI, apre il setup ufficiale
    except Exception as e:
        print('[EXP] installo expander:', e)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
        try:
            os.remove(tmpzip)
        except Exception:
            pass


def apply():
    if not _abilitato():
        return False
    import threading
    threading.Thread(target=_aggiorna, daemon=True, name='exp_scarica_103').start()
    return True


def revert():
    return False


try:
    apply()
except Exception:
    pass
