# 103 - scarica l'expander software (exe + banco) dal server
URL_ZIP = 'https://iocanto.karadom.it/dl/Expander.zip'
URL_VER = 'https://iocanto.karadom.it/dl/Expander.ver'
EXE = 'KaraDom Expander.exe'


def _abilitato():
    # Scarica su TUTTI i client (l'expander software deve arrivare ai clienti).
    # Unico interruttore: patch_103=0 lo spegne su un PC specifico.
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_103', '1')) != '0'
    except Exception:
        return True


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
    import os
    for r, _d, files in os.walk(top):
        if EXE.lower() in [f.lower() for f in files]:
            return r
    return top


def _copia_dentro(src, dest):
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


def _loopmidi_installato():
    import os
    pf = os.environ.get('PROGRAMFILES', r'C:\Program Files')
    return (os.path.isfile(os.path.join(pf, 'Tobias Erichsen', 'teVirtualMIDI', 'teVirtualMIDI64.sys'))
            or os.path.isfile(os.path.join(pf, 'Tobias Erichsen', 'loopMIDI', 'loopMIDI.exe')))


def _installa_loopmidi(dest):
    # loopMIDI installa un driver: l'auto-lancio da thread in background non e'
    # affidabile. Mostro un BOTTONE sulla UI; al CLIC dell'utente il setup parte
    # in primo piano (l'UAC compare normale) e installa.
    import os, sys
    if os.name != 'nt' or _loopmidi_installato():
        return
    setup = os.path.join(dest, 'loopMIDISetup.exe')
    if not os.path.isfile(setup):
        return
    if getattr(_installa_loopmidi, '_mostrata', False):
        return
    try:
        main = sys.modules.get('__main__')
        root = getattr(main, '_app_root', None)
        if root is None:
            return
        _installa_loopmidi._mostrata = True

        def _mostra():
            try:
                import tkinter as tk
                w = tk.Toplevel(root)
                w.title('KaraDom Expander')
                try:
                    w.attributes('-topmost', True)
                except Exception:
                    pass
                tk.Label(w, justify='left', padx=20, pady=14,
                         text="Per usare l'Expander serve il MIDI virtuale loopMIDI.\n"
                              "Installalo ora: un 'Si' all'avviso di Windows, poi Avanti/Installa.").pack()

                def _go():
                    try:
                        os.startfile(setup)
                        print('[EXP] loopMIDI: setup avviato dal bottone')
                    except Exception as e:
                        print('[EXP] installo loopMIDI:', e)
                    try:
                        w.destroy()
                    except Exception:
                        pass

                tk.Button(w, text='Installa loopMIDI', command=_go, bg='#0d6efd',
                          fg='white', relief='flat', padx=16, pady=6,
                          cursor='hand2').pack(pady=(0, 14))
            except Exception as e:
                print('[EXP] dialog loopMIDI:', e)

        root.after(0, _mostra)
    except Exception as e:
        print('[EXP] installo loopMIDI:', e)


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
        return
    if exe_ok and _leggi_ver(verfile) == remoto:
        _installa_loopmidi(dest)   # gia' aggiornato: assicura comunque loopMIDI
        return
    # NB: se l'exe expander e' in uso NON blocco l'aggiornamento. La copia del solo
    # exe (bloccato) fallira' e verra' saltata, ma setup+banchi si aggiornano e
    # loopMIDI puo' installarsi lo stesso.

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
        _installa_loopmidi(dest)
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