# 247 - ridisegna avvio

import threading
import time

_VER = 2
_QUANDO = (0.05, 0.3, 1.5, 4.0)  # secondi dopo che la finestra e' pronta (mainloop)
_MOSTRA = 0.35                 # v2: quando la finestra torna visibile (gia' dipinta)

# [25-10-2026] Utente: "e' un po' di tempo che quando parte si vede cosi'" (finestra principale vuota, blu scuro,
# senza "Strumenti / Extra / About" in alto a sinistra). Spia 246: a +12 s la finestra e' costruita TUTTA e per Tk e'
# visibile, il programma e' fermo in attesa (CPU 2-10%), ma a schermo si vedono solo due pezzi della barra in basso.
# La finestra nasce piccola come splash (420x280) e poi diventa a tutto schermo: Windows non ridipinge la parte nuova.
# Rimedio: appena il programma e' pronto si chiede a Windows di ridisegnare TUTTA la finestra con i figli, piu' volte.
# v2 (utente: "vuota per qualche secondo"): la finestra compare trasparente e diventa visibile gia' dipinta.


def _titolare():
    try:
        from moduli.licensing import load_license
        d = load_license() or {}
        return (str(d.get('nome', '')).strip().lower(),
                str(d.get('cognome', '')).strip().lower()) == ('domenico', 'lembo')
    except Exception:
        return False


def _log(msg):
    try:
        print('[247] %s' % msg)
    except Exception:
        pass


def _ridisegna(root, n):
    """Nel thread della finestra: Tk ricalcola e Windows ridipinge tutto (cornice e figli compresi)."""
    try:
        root.update_idletasks()
        import ctypes
        hwnd = int(root.wm_frame(), 16)
        RDW_INVALIDATE, RDW_ERASE, RDW_ALLCHILDREN, RDW_UPDATENOW, RDW_FRAME = 0x1, 0x4, 0x80, 0x100, 0x400
        ok = ctypes.windll.user32.RedrawWindow(hwnd, None, None,
                                               RDW_INVALIDATE | RDW_ERASE | RDW_ALLCHILDREN | RDW_UPDATENOW | RDW_FRAME)
        _log('finestra ridisegnata (%d) %s' % (n, 'ok' if ok else 'non riuscito'))
    except Exception as e:
        _log('ridisegno non riuscito: %s' % e)


_stato = {'nascosta': False}


def _mostra(root):
    """v2: la finestra torna visibile, gia' dipinta. Chiamata dal thread della finestra."""
    if _stato.get('nascosta'):
        _stato['nascosta'] = False
        try:
            root.attributes('-alpha', 1.0)
            _log('finestra mostrata, gia dipinta')
        except Exception as e:
            _log('alpha non rimesso: %s' % e)


def _aggancia_deiconify():
    """v2, utente: 'vuota per qualche secondo'. La finestra principale diventa a tutto schermo (deiconify dopo
    lo splash) prima che Windows la dipinga: la si fa comparire TRASPARENTE e la si rende visibile solo dopo il
    primo ridisegno. Sicurezza: dopo 3 s torna visibile comunque."""
    import tkinter as tk
    orig = tk.Wm.wm_deiconify

    def wm_deiconify(self):
        try:
            if isinstance(self, tk.Tk) and not getattr(self, '_v247', False) and str(self.state()) in ('zoomed', 'withdrawn'):
                self._v247 = True
                self.attributes('-alpha', 0.0)
                _stato['nascosta'] = True
                self.after(3000, lambda: _mostra(self))
        except Exception:
            pass
        return orig(self)
    tk.Wm.wm_deiconify = wm_deiconify
    tk.Wm.deiconify = wm_deiconify


def _aspetta_e_chiedi():
    """Aspetta che il thread della finestra sia nel mainloop, poi mette in fila i ridisegni (after: dentro Tk)."""
    import sys
    import tkinter
    main = threading.main_thread().ident
    fine = time.time() + 120
    while time.time() < fine:
        time.sleep(0.25)
        try:
            fr = sys._current_frames().get(main)
            dentro = False
            while fr is not None:
                if fr.f_code.co_name == 'mainloop':
                    dentro = True
                    break
                fr = fr.f_back
            r = tkinter._default_root
            if dentro and r is not None:
                for i, s in enumerate(_QUANDO, 1):
                    r.after(int(s * 1000), lambda n=i: _ridisegna(r, n))
                r.after(int(_MOSTRA * 1000), lambda: _mostra(r))
                return
        except Exception:
            continue


def apply():
    if not _titolare():
        return False
    try:
        from moduli.database import Database
        if str(Database.get_config('patch_247', '1')).strip() in ('0', 'no', 'off'):
            return False
    except Exception:
        pass
    import sys
    if getattr(sys, '_ridisegna247', False):
        return True
    sys._ridisegna247 = True
    try:
        _aggancia_deiconify()
    except Exception as e:
        _log('aggancio deiconify non riuscito: %s' % e)
    threading.Thread(target=_aspetta_e_chiedi, daemon=True, name='ridisegna_247').start()
    return True


def revert():
    return False
