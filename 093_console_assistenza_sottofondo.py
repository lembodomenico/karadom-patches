# 093 - console assistenza accanto a SOT
SERIAL_DOM = "1A55-2CD1-3303-20EB"


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_093', '1')) == '0'
    except Exception:
        return False


def _serial():
    try:
        from moduli.licensing import get_hardware_id, generate_serial
        return generate_serial(*get_hardware_id())
    except Exception as e:
        print("[console093] serial err: %s" % e)
        return ""


def _apri_console():
    import os
    import sys
    import subprocess
    try:
        from moduli.constants import get_base_path
        base = get_base_path()
    except Exception:
        if getattr(sys, 'frozen', False) or ('__compiled__' in globals()):
            base = os.path.dirname(os.path.abspath(sys.argv[0]))
        else:
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dep = os.path.join(base, 'dipendenze', 'AssistenzaKD Console')
    cand = [os.path.join(dep, 'AssistenzaKD Console.exe'),
            os.path.join(dep, 'rustdesk.exe'),
            os.path.join(os.path.expanduser('~'), 'Desktop',
                         'AssistenzaKD Console', 'AssistenzaKD Console.exe')]
    exe = next((p for p in cand if os.path.exists(p)), None)
    try:
        if exe:
            subprocess.Popen([exe], cwd=os.path.dirname(exe))
        else:
            print("[console093] exe non trovato in dipendenze")
    except Exception as e:
        print("[console093] apri: %s" % e)


def apply():
    if _spenta():
        return False
    try:
        import moduli.monitor as mon
        from moduli.glow_button import GlowButton
        from moduli.ui_scale import S, F
    except Exception as e:
        print("[console093] import: %s" % e)
        return False
    if getattr(mon.KaraokeMonitor, '_botcons093', False):
        return True

    _orig = mon.KaraokeMonitor.setup_toolbar_buttons

    def setup_toolbar_buttons(self, *a, **k):
        r = _orig(self, *a, **k)
        try:
            if _serial() != SERIAL_DOM:
                return r
            bf = getattr(self, 'buttons_frame', None)
            if bf is None or getattr(self, 'btn_console_ass', None) is not None:
                return r
            BTN_SIZE = S(45)
            BTN_W = round(BTN_SIZE * 1.5)
            CORNER = S(16)
            self.btn_console_ass = GlowButton(bf, text="\U0001f6e0",
                                              command=_apri_console,
                                              width=BTN_W, height=BTN_SIZE,
                                              corner_radius=CORNER,
                                              fg_color="#6366f1", hover_color="#4f46e5",
                                              text_color="white",
                                              font=F("Segoe UI", 12, "bold"))
            self.btn_console_ass.pack(side='left', padx=0)
            try:
                self._add_tooltip(self.btn_console_ass, "Console assistenza")
            except Exception:
                pass
            print("[console093] bottone aggiunto in barra")
        except Exception as e:
            print("[console093] init err: %s" % e)
        return r

    mon.KaraokeMonitor.setup_toolbar_buttons = setup_toolbar_buttons
    mon.KaraokeMonitor._botcons093 = True
    print("[console093] apply ok, serial=%s" % _serial())
    return True


def revert():
    return False


try:
    apply()
except Exception as _e:
    try:
        print("[console093] apply crash: %s" % _e)
    except Exception:
        pass
