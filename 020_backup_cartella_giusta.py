# 020 - il backup torna a trovare la cartella dei dati.


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_020', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


# I file della licenza. La cache hardware si puo' salvare: dentro ha
# un'impronta del PC e si invalida da sola su una macchina diversa.
# Il .revoked NON si salva: una licenza revocata resta revocata.
FILE_LICENZA = ('_cx9k2m.pyc', '_hw8r3p.cache', '_v7xp4q.pyc')


def cartella_dati():
    import os
    try:
        from moduli.database import Database
        return os.path.dirname(os.path.abspath(Database.DB_PATH))
    except Exception:
        return os.path.abspath('data')


def cartella_sbagliata():
    """Dove finivano le cose prima: accanto a _internal, in %LOCALAPPDATA%."""
    import os
    try:
        from moduli.licensing import _get_base_internal_path
        return os.path.join(str(_get_base_internal_path().parent), 'data')
    except Exception:
        return ''


def esegui_backup(silent=True):
    import os
    import zipfile
    import hashlib
    from datetime import datetime
    from moduli.opzioni import OpzioniWindow
    from moduli.licensing import _get_base_internal_path

    backup_dir = OpzioniWindow.get_backup_dir()
    data_dir = cartella_dati()
    _int = _get_base_internal_path()
    file_licenza = [str(_int / n) for n in FILE_LICENZA if os.path.isfile(str(_int / n))]

    if not os.path.isdir(data_dir):
        if not silent:
            print("[Backup] cartella dati non trovata: %s" % data_dir)
        return False

    hasher = hashlib.md5()
    for root_dir, dirs, files in os.walk(data_dir):
        dirs[:] = [d for d in dirs if d.lower() != 'temp']
        dirs.sort()
        for f in sorted(files):
            fp = os.path.join(root_dir, f)
            try:
                hasher.update(f.encode())
                st = os.stat(fp)
                hasher.update(str(st.st_size).encode())
                hasher.update(str(int(st.st_mtime)).encode())
            except Exception:
                pass
    for _f in file_licenza:
        try:
            st = os.stat(_f)
            hasher.update(os.path.basename(_f).encode())
            hasher.update(str(st.st_size).encode())
            hasher.update(str(int(st.st_mtime)).encode())
        except Exception:
            pass
    current_hash = hasher.hexdigest()

    hash_file = os.path.join(backup_dir, '.last_hash')
    if os.path.isfile(hash_file):
        try:
            with open(hash_file, 'r') as f:
                if f.read().strip() == current_hash:
                    if not silent:
                        print("[Backup] Nessuna modifica rilevata")
                    return False
        except Exception:
            pass

    zip_name = "karadom_backup_%s.zip" % datetime.now().strftime('%Y%m%d_%H%M%S')
    zip_path = os.path.join(backup_dir, zip_name)
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root_dir, dirs, files in os.walk(data_dir):
                dirs[:] = [d for d in dirs if d.lower() != 'temp']
                for f in files:
                    fp = os.path.join(root_dir, f)
                    zf.write(fp, os.path.join('data', os.path.relpath(fp, data_dir)))
            for _f in file_licenza:
                zf.write(_f, os.path.join('_internal', os.path.basename(_f)))

        with open(hash_file, 'w') as f:
            f.write(current_hash)

        backups = sorted([f for f in os.listdir(backup_dir)
                          if f.startswith('karadom_backup_') and f.endswith('.zip')])
        while len(backups) > 14:
            try:
                os.remove(os.path.join(backup_dir, backups.pop(0)))
            except Exception:
                pass

        if not silent:
            print("[Backup] creato: %s" % zip_name)
        return True
    except Exception as e:
        if not silent:
            print("[Backup] errore: %s" % e)
        try:
            if os.path.exists(zip_path):
                os.remove(zip_path)
        except Exception:
            pass
        return False


def _porta_a_casa_il_ripristino():
    """Sposta nella cartella giusta quello che il ripristino ha scritto in quella
    sbagliata. Senza questo il ripristino sembrerebbe riuscito senza esserlo."""
    import os
    import shutil
    male = cartella_sbagliata()
    bene = cartella_dati()
    if not male or not bene or os.path.normcase(male) == os.path.normcase(bene):
        return 0
    if not os.path.isdir(male):
        return 0
    spostati = 0
    for radice, _dirs, files in os.walk(male):
        for f in files:
            sorgente = os.path.join(radice, f)
            destinazione = os.path.join(bene, os.path.relpath(sorgente, male))
            try:
                os.makedirs(os.path.dirname(destinazione), exist_ok=True)
                shutil.move(sorgente, destinazione)
                spostati += 1
            except Exception:
                pass
    try:
        shutil.rmtree(male, ignore_errors=True)
    except Exception:
        pass
    return spostati


def _rimetti_licenza_dal_zip(zip_path):
    """Rimette i file della licenza presi da un backup. Serve perche' il
    ripristino vecchio conosceva solo _cx9k2m.pyc."""
    import os
    import zipfile
    from moduli.licensing import _get_base_internal_path
    dove = str(_get_base_internal_path())
    messi = 0
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for m in zf.namelist():
                nome = os.path.basename(m)
                if m.startswith('_internal/') and nome in FILE_LICENZA:
                    with zf.open(m) as src, open(os.path.join(dove, nome), 'wb') as dst:
                        dst.write(src.read())
                    messi += 1
    except Exception:
        pass
    return messi


def apply():
    if _spenta():
        return False
    try:
        import os
        from moduli.opzioni import OpzioniWindow as C

        if not hasattr(C, 'get_data_dir'):
            C.get_data_dir = staticmethod(cartella_dati)

        if not hasattr(C, '_orig_020_backup'):
            C._orig_020_backup = C.esegui_backup
            C.esegui_backup = staticmethod(esegui_backup)

        if hasattr(C, '_mostra_restore_dialog') and not hasattr(C, '_orig_020_restore'):
            C._orig_020_restore = C._mostra_restore_dialog

            def _mostra_restore_dialog(self, _orig=C._orig_020_restore):
                esito = _orig(self)
                try:
                    quanti = _porta_a_casa_il_ripristino()
                    if quanti:
                        print("[Ripristino] %d file rimessi nella cartella giusta" % quanti)
                except Exception:
                    pass
                return esito

            C._mostra_restore_dialog = _mostra_restore_dialog

        return hasattr(C, '_orig_020_backup')
    except Exception:
        return False


def revert():
    try:
        from moduli.opzioni import OpzioniWindow as C
        fatto = False
        if hasattr(C, '_orig_020_backup'):
            C.esegui_backup = C._orig_020_backup
            del C._orig_020_backup
            fatto = True
        if hasattr(C, '_orig_020_restore'):
            C._mostra_restore_dialog = C._orig_020_restore
            del C._orig_020_restore
            fatto = True
        return fatto
    except Exception:
        return False


try:
    apply()
except Exception:
    pass
