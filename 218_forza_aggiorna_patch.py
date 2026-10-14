# 218 - menu Extra: "Forza aggiornamento patch"

_VER = 3

# [14-10-2026] su tutti i PC (prima solo sul portatile KaraDom OS)
SOLO_SERIALI = ('4D8E-F63F-45E1-8F06', '1E49-898D-7E7D-E899')   # disco interno, chiavetta 64 GB


def _pc_giusto():
    try:
        from moduli.licensing import get_hardware_id, generate_serial
        c, m = get_hardware_id()
        return generate_serial(c, m) in SOLO_SERIALI
    except Exception:
        return False


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_218', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def _leggi(url, timeout=20):
    import urllib.request
    req = urllib.request.Request(url, headers={'User-Agent': 'KaraDom Pro Updater',
                                               'Cache-Control': 'no-cache', 'Pragma': 'no-cache'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def forza_patch():
    """Riscarica TUTTE le patch pubblicate, senza fidarsi di impronte o cache.
    ⛔ Non usa pezzi interni di moduli.updater: sui KaraDom installati non sempre ci sono
    ("module 'moduli.updater' has no attribute '_patch_base_fatta'").
    Ritorna (aggiornate, nuove, errori)."""
    import os
    import json
    try:
        from moduli.hotfix import patches_dir, _verify
    except Exception:
        from hotfix import patches_dir, _verify
    raw = "https://raw.githubusercontent.com/lembodomenico/karadom-patches"
    try:                        # l'ultimo commit esatto: niente copie vecchie dalla cache di GitHub
        sha = json.loads(_leggi("https://api.github.com/repos/lembodomenico/karadom-patches/commits/main"
                                ).decode('utf-8'))['sha']
        base = raw + "/" + sha
    except Exception:
        base = raw + "/main"
    d = patches_dir()
    manifest = json.loads(_leggi(base + "/manifest.json").decode('utf-8'))
    elenco = [str(n) for n in (manifest.get("patches") or []) if str(n).endswith(".py")]
    aggiornate, nuove, errori = [], [], []
    for nome in elenco:
        try:
            dest = os.path.join(d, nome)
            if os.path.exists(dest + ".prova") or os.path.exists(os.path.join('/opt/karadom-os/patches_os', nome)):
                continue        # prova locale / patch bloccata di KaraDom OS: non si tocca
            py = _leggi(base + "/" + nome)
            sig = _leggi(base + "/" + nome + ".sig")
            if not _verify(py, sig):
                errori.append(nome + " (firma)")
                continue
            c_era = os.path.exists(dest)
            if c_era and open(dest, "rb").read() == py and open(dest + ".sig", "rb").read() == sig:
                continue
            for f, dati in ((dest + ".sig", sig), (dest, py)):
                with open(f + ".tmp218", "wb") as fh:
                    fh.write(dati)
                os.replace(f + ".tmp218", f)
            (aggiornate if c_era else nuove).append(nome)
        except Exception as e:
            errori.append("%s (%s)" % (nome, e))
    try:
        os.remove(os.path.join(d, '.ultimo_commit'))   # la 000 ricontrolla tutto al prossimo avvio
    except Exception:
        pass
    print("🩹 forza patch: %d aggiornate, %d nuove, %d errori su %d"
          % (len(aggiornate), len(nuove), len(errori), len(elenco)))
    return aggiornate, nuove, errori


def _riavvia_karadom(root):
    import os
    import sys
    import subprocess
    if os.name == 'nt':
        exe = os.path.abspath(sys.argv[0]) if sys.argv and sys.argv[0] else ''
        if exe.lower().endswith('.exe') and os.path.exists(exe) and 'python' not in os.path.basename(exe).lower():
            riga = ' '.join('"%s"' % x for x in [exe] + sys.argv[1:])
        else:
            riga = ' '.join('"%s"' % x for x in [sys.executable] + sys.argv)
        # fra ~2 s, a KaraDom chiuso; ⛔ STRINGA, non lista (virgolette rovinate -> "Impossibile trovare '\'")
        subprocess.Popen('cmd /c ping -n 3 127.0.0.1 >nul & start "" ' + riga,
                         creationflags=0x08000000, close_fds=True)
    else:
        avvio = '/root/avvia_karadom.sh'
        if os.path.exists(avvio):
            subprocess.Popen(['setsid', '--fork', 'bash', '-c',
                              'sleep 2; exec </dev/tty1 >/dev/tty1 2>&1; %s' % avvio],
                             close_fds=True, start_new_session=True)
        else:
            subprocess.Popen(['setsid', sys.executable] + sys.argv,
                             close_fds=True, start_new_session=True)
    root.after(300, root.destroy)


def apri(root):
    import threading
    from tkinter import messagebox
    try:
        from moduli.i18n import _
    except Exception:
        def _(s):
            return s

    def fine(ris):
        if isinstance(ris, Exception):
            messagebox.showerror(_("Forza aggiornamento patch"),
                                 _("Server delle patch non raggiungibile:\n{e}").format(e=ris), parent=root)
            return
        aggiornate, nuove, errori = ris
        testo = _("Patch aggiornate: {a}\nPatch nuove: {n}").format(a=len(aggiornate), n=len(nuove))
        if errori:
            testo += "\n" + _("Non scaricate: {e}").format(e=", ".join(errori[:8]))
        if aggiornate or nuove:
            if messagebox.askyesno(_("Forza aggiornamento patch"),
                                   testo + "\n\n" + _("Riavviare KaraDom adesso per attivarle?"), parent=root):
                try:
                    _riavvia_karadom(root)
                except Exception as e:
                    messagebox.showerror(_("Riavvia KaraDom"), str(e), parent=root)
        else:
            messagebox.showinfo(_("Forza aggiornamento patch"),
                                testo + "\n\n" + _("Le patch sono già tutte aggiornate."), parent=root)

    def lavora():
        try:
            ris = forza_patch()
        except Exception as e:
            ris = e
        try:
            root.after(0, lambda: fine(ris))
        except Exception:
            pass

    threading.Thread(target=lavora, daemon=True, name="ForzaPatch").start()


def apply():
    if _spenta():
        return False
    try:
        from moduli import updater
        if hasattr(updater, 'apri_forza_patch'):
            updater.apri_forza_patch = apri     # KaraDom ricompilato: voce nel menu, lavoro fatto qui
            return True
    except Exception:
        pass
    import tkinter as tk
    if getattr(tk.Menu, '_forza_218', False):
        return True
    try:
        from moduli.i18n import _
    except Exception:
        def _(s):
            return s
    _orig = tk.Menu.add_command

    def add_command(self, cnf={}, **kw):
        r = _orig(self, cnf, **kw)
        try:
            etichetta = str(kw.get('label') or (cnf or {}).get('label') or '')
            if etichetta in ("Controlla aggiornamenti...", _("Controlla aggiornamenti...")) \
                    and not getattr(self, '_forza_218_messa', False):
                self._forza_218_messa = True
                root = self.winfo_toplevel()
                _orig(self, label=_("Forza aggiornamento patch"), command=lambda: apri(root))
        except Exception as e:
            print("⚠️ 218: voce menu non aggiunta (%s)" % e)
        return r

    tk.Menu.add_command = add_command
    tk.Menu._forza_218 = True
    return True
