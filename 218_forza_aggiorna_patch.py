# 218 - menu Extra: "Forza aggiornamento patch"

_VER = 2

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


def forza_patch():
    """Riscarica TUTTE le patch pubblicate, senza fidarsi di impronte o cache.
    Ritorna (aggiornate, nuove, errori)."""
    import os
    import json
    import urllib.request
    from moduli import updater
    from moduli.hotfix import patches_dir, _verify
    updater._patch_base_fatta[0] = None
    d = patches_dir()
    base = updater._base_patches()
    req = urllib.request.Request(base + "/manifest.json",
                                 headers={'User-Agent': 'KaraDom Pro Updater',
                                          'Cache-Control': 'no-cache', 'Pragma': 'no-cache'})
    with urllib.request.urlopen(req, timeout=20) as resp:
        manifest = json.loads(resp.read().decode('utf-8'))
    elenco = [str(n) for n in (manifest.get("patches") or []) if str(n).endswith(".py")]
    aggiornate, nuove, errori = [], [], []
    for nome in elenco:
        try:
            py = updater._scarica(base + "/" + nome)
            sig = updater._scarica(base + "/" + nome + ".sig")
            if py is None or sig is None:
                errori.append(nome)
                continue
            if not _verify(py, sig):
                errori.append(nome + " (firma)")
                continue
            dest = os.path.join(d, nome)
            if os.path.exists(dest[:-3] + ".py.prova") or os.path.exists(dest + ".prova"):
                continue        # prova locale / patch bloccata di KaraDom OS: non si tocca
            c_era = os.path.exists(dest)
            if c_era and open(dest, "rb").read() == py and os.path.exists(dest + ".sig"):
                continue
            open(dest, "wb").write(py)
            open(dest + ".sig", "wb").write(sig)
            (aggiornate if c_era else nuove).append(nome)
        except Exception as e:
            errori.append("%s (%s)" % (nome, e))
    print("🩹 forza patch: %d aggiornate, %d nuove, %d errori su %d"
          % (len(aggiornate), len(nuove), len(errori), len(elenco)))
    return aggiornate, nuove, errori


def _riavvia_karadom(root):
    import os
    import sys
    import subprocess
    if os.name == 'nt':
        exe = sys.executable
        if getattr(sys, 'frozen', False) or '__compiled__' in globals() or 'python' not in os.path.basename(exe).lower():
            subprocess.Popen([exe] + sys.argv[1:], close_fds=True)
        else:
            subprocess.Popen([exe] + sys.argv, close_fds=True)
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
            return True         # KaraDom ricompilato: la voce c'e' gia' nel menu
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
