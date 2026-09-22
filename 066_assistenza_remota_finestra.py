# 066 - assistenza remota
def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_066', '1')) == '0'
    except Exception:
        return False


def apply():
    if _spenta():
        return False
    import os
    import sys
    import subprocess
    import tkinter as tk
    from tkinter import messagebox

    NOWIN = 0x08000000 if os.name == 'nt' else 0

    try:
        from moduli.i18n import _
    except Exception:
        def _(s):
            return s

    def base_path():
        try:
            from moduli.constants import get_base_path
            return get_base_path()
        except Exception:
            if getattr(sys, 'frozen', False) or ('__compiled__' in globals()):
                return os.path.dirname(os.path.abspath(sys.argv[0]))
            return os.getcwd()

    def trova_exe():
        dep = os.path.join(base_path(), 'dipendenze')
        la = os.path.join(os.environ.get('LOCALAPPDATA') or os.path.expanduser('~'),
                          'KaraDom', 'AssistenzaKD')
        for p in (os.path.join(la, 'AssistenzaKD_qs.exe'),
                  os.path.join(la, 'AssistenzaKD.exe'),
                  os.path.join(dep, 'AssistenzaKD', 'AssistenzaKD_qs.exe'),
                  os.path.join(dep, 'AssistenzaKD', 'AssistenzaKD.exe'),
                  os.path.join(dep, 'AssistenzaKD_qs.exe'),
                  os.path.join(dep, 'AssistenzaKD.exe'),
                  os.path.join(dep, 'AssistenzaKD', 'rustdesk.exe'),
                  os.path.join(dep, 'rustdesk.exe')):
            if os.path.exists(p):
                return p
        return os.path.join(la, 'AssistenzaKD_qs.exe')

    def imposta_opzione(f, key, val):
        try:
            import re
            s = open(f, encoding='utf-8').read() if os.path.isfile(f) else ''
            riga = "%s = '%s'" % (key, val)
            if re.search(r"(?m)^\s*%s\s*=" % re.escape(key), s):
                s2 = re.sub(r"(?m)^\s*%s\s*=.*$" % re.escape(key), riga, s)
            elif '[options]' in s:
                s2 = s.replace('[options]', '[options]\n' + riga, 1)
            else:
                s2 = (s + ('\n' if s and not s.endswith('\n') else '') +
                      '[options]\n' + riga + '\n')
            if s2 != s:
                os.makedirs(os.path.dirname(f), exist_ok=True)
                open(f, 'w', encoding='utf-8').write(s2)
        except Exception:
            pass

    def servizio_on():
        # server interno ACCESO (password visibile, niente install/UAC) + tema scuro
        base = os.environ.get('APPDATA') or os.path.expanduser('~')
        cfg = os.path.join(base, 'AssistenzaKD', 'config')
        imposta_opzione(os.path.join(cfg, 'AssistenzaKD2.toml'), 'stop-service', '')
        imposta_opzione(os.path.join(cfg, 'AssistenzaKD_local.toml'), 'theme', 'dark')

    def pids_di(nome):
        if os.name != 'nt':
            return set()
        try:
            out = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq ' + nome,
                                  '/FO', 'CSV', '/NH'], capture_output=True,
                                 text=True, timeout=5, creationflags=NOWIN).stdout or ''
            pids = set()
            for riga in out.splitlines():
                parti = [p.strip('" ') for p in riga.split('","')]
                if len(parti) >= 2 and parti[0].lower() == nome.lower():
                    try:
                        pids.add(int(parti[1]))
                    except Exception:
                        pass
            return pids
        except Exception:
            return set()

    def porta_su(pids):
        if os.name != 'nt' or not pids:
            return
        try:
            import ctypes
            from ctypes import wintypes
            u = ctypes.windll.user32
            EnumProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

            def cb(hwnd, _l):
                pid = wintypes.DWORD()
                u.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                if pid.value in pids and u.GetWindowTextLengthW(hwnd) > 0:
                    try:
                        u.AllowSetForegroundWindow(pid.value)
                    except Exception:
                        pass
                    u.ShowWindow(hwnd, 5)   # SW_SHOW
                    u.ShowWindow(hwnd, 9)   # SW_RESTORE
                    u.BringWindowToTop(hwnd)
                    u.SetForegroundWindow(hwnd)
                return True
            u.EnumWindows(EnumProc(cb), 0)
        except Exception:
            pass

    def apri(parent):
        exe = trova_exe()
        if not os.path.exists(exe):
            messagebox.showerror(_("Assistenza remota"),
                                 _("Manca il file:\n%s\n\nMettilo nella cartella "
                                   "dipendenze.") % exe, parent=parent)
            return
        # gia' in esecuzione? riporta su QUELLA (niente seconda finestra).
        pids = pids_di(os.path.basename(exe))
        if pids:
            porta_su(pids)
            return
        servizio_on()  # server acceso -> password visibile, niente install/UAC
        try:
            subprocess.Popen([exe], cwd=os.path.dirname(exe), creationflags=NOWIN)
        except Exception as e:
            messagebox.showerror(_("Assistenza remota"),
                                 _("Impossibile avviare: %s") % e, parent=parent)

    if not getattr(tk.Menu, '_assist_066', False):
        _orig = tk.Menu.add_command

        def add_command(self, cnf={}, **kw):
            try:
                lbl = str(kw.get('label', '') or '').lower()
                if 'assistenza remota' in lbl or 'remote assist' in lbl:
                    kw = dict(kw)
                    kw['command'] = lambda: apri(getattr(tk, '_default_root', None))
            except Exception:
                pass
            return _orig(self, cnf, **kw)

        tk.Menu.add_command = add_command
        tk.Menu._assist_066 = True
    return True


def revert():
    return False


try:
    apply()
except Exception:
    pass
