# 219 - avviso quando KaraDom e' stato aggiornato

import hashlib
import os
import threading
import time

_VER = 1
CONTROLLO_MIN = 20          # ogni quanto si cercano patch nuove con KaraDom aperto
FERMO_SEC = 180             # da quanto non deve suonare niente prima di mostrare l'avviso
AVVIO_SEC = 240             # nei primi minuti (prima di suonare) l'avviso esce subito

_stato = {'sistema': None, 'ultimo_suono': time.time(), 'avviato': time.time(),
          'suonato': False, 'caricate': None, 'rimanda': 0.0, 'in_corso': False}


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_219', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def _dir():
    try:
        from moduli.hotfix import patches_dir
        return patches_dir()
    except Exception:
        base = os.environ.get('LOCALAPPDATA') or os.path.expanduser('~')
        return os.path.join(base, 'KaraDom', 'patches')


def _impronte():
    d, fuori = _dir(), {}
    try:
        for n in os.listdir(d):
            if n.endswith('.py'):
                try:
                    dati = open(os.path.join(d, n), 'rb').read().replace(b'\r\n', b'\n')
                    fuori[n] = hashlib.sha1(dati).hexdigest()
                except Exception:
                    pass
    except Exception:
        pass
    return fuori


def _in_attesa():
    """Patch scaricate ma NON ancora in funzione in questo KaraDom: cambiate dopo l'avvio,
    nuove non partite, o ritirate (tolte dal disco ma ancora attive in memoria)."""
    caricate = _stato['caricate'] or {}
    ora = _impronte()
    try:
        from moduli.hotfix import APPLICATE
    except Exception:
        APPLICATE = set()
    fuori = []
    for n, h in ora.items():
        if n in caricate:
            if caricate[n] != h:
                fuori.append(n)
        elif n not in APPLICATE:
            fuori.append(n)
    fuori += [n for n in caricate if n not in ora]
    return sorted(fuori)


def _suona():
    s = _stato['sistema']
    try:
        return bool(s is not None and getattr(s, 'is_playing', False))
    except Exception:
        return False


def _root():
    try:
        import tkinter
        r = getattr(tkinter, '_default_root', None)
        if r is not None and r.winfo_exists():
            return r
    except Exception:
        pass
    return None


def _riavvia():
    """Solo quando l'utente preme "Riavvia ora": niente riavvii automatici."""
    import sys
    print('[219] riavvio scelto dall\'utente per attivare gli aggiornamenti')
    if os.path.exists('/opt/karadom-os/sessione.sh'):
        os._exit(0)                     # KaraDom OS: sessione.sh lo rilancia da sola in 2 s
    r = _root()
    try:
        if r is not None:
            r.destroy()
    except Exception:
        pass
    exe = os.path.abspath(sys.argv[0]) if sys.argv and sys.argv[0] else ''
    try:
        if exe.lower().endswith('.exe') and os.path.exists(exe):
            os.execv(exe, [exe] + sys.argv[1:])
        elif sys.executable and not sys.executable.lower().endswith('python.exe'):
            os.execv(sys.executable, [sys.executable] + sys.argv[1:])
        else:
            os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception as e:
        print('[219] riavvio non riuscito: %s' % e)
        os._exit(0)


def _avviso(quante):
    """Riquadro in alto: 'KaraDom e' stato aggiornato' con Riavvia ora / Piu' tardi.
    Il riavvio lo decide SEMPRE l'utente. Gira nel thread di Tk."""
    import tkinter as tk
    r = _root()
    if r is None:
        _stato['in_corso'] = False
        return
    try:
        from moduli.i18n import _
    except Exception:
        def _(s):
            return s
    w = tk.Toplevel(r)
    w.overrideredirect(True)
    w.attributes('-topmost', True)
    w.configure(bg='#1e5bd8')
    tk.Label(w, text=_("KaraDom è stato aggiornato: riavvia per attivare gli aggiornamenti"),
             bg='#1e5bd8', fg='white', font=('Segoe UI', 14, 'bold'), padx=22, pady=12).pack(side='left')

    def ora():
        w.destroy()
        _riavvia()

    def tardi():
        _stato['rimanda'] = time.time() + 30 * 60
        _stato['in_corso'] = False
        w.destroy()
    tk.Button(w, text=_("Riavvia ora"), command=ora, bg='#28a745', fg='white', relief='flat',
              font=('Segoe UI', 12, 'bold'), padx=14, cursor='hand2').pack(side='left', padx=(0, 8), pady=8)
    tk.Button(w, text=_("Più tardi"), command=tardi, bg='#2a3560', fg='white', relief='flat',
              font=('Segoe UI', 12, 'bold'), padx=14, cursor='hand2').pack(side='left', padx=(0, 12), pady=8)

    def guarda():
        # se parte un brano l'avviso si toglie (mai sopra la musica) e torna a brano finito
        if not w.winfo_exists():
            return
        if _suona():
            _stato['in_corso'] = False
            w.destroy()
            return
        w.after(1000, guarda)
    guarda()
    w.update_idletasks()
    w.geometry('+%d+%d' % ((w.winfo_screenwidth() - w.winfo_reqwidth()) // 2, 60))


def _guardia():
    ultimo_controllo = time.time()
    while True:
        time.sleep(15)
        try:
            ora = time.time()
            if _suona():
                _stato['ultimo_suono'] = ora
                _stato['suonato'] = True
                continue
            if _stato['in_corso'] or ora < _stato['rimanda']:
                continue
            # con KaraDom aperto a lungo: ogni tanto si cercano patch nuove
            if ora - ultimo_controllo > CONTROLLO_MIN * 60:
                ultimo_controllo = ora
                try:
                    from moduli import updater
                    updater.scarica_patch_adesso()
                except Exception as e:
                    print('[219] controllo patch: %s' % e)
            attesa = _in_attesa()
            if not attesa:
                continue
            all_avvio = not _stato['suonato'] and ora - _stato['avviato'] < AVVIO_SEC
            fermo = ora - _stato['ultimo_suono'] > FERMO_SEC
            if not (all_avvio or fermo):
                continue
            print('[219] patch da attivare: %s' % ', '.join(attesa[:12]))
            r = _root()
            if r is not None:
                _stato['in_corso'] = True
                r.after(0, lambda n=len(attesa): _avviso(n))
        except Exception as e:
            print('[219] guardia: %s' % e)


def apply():
    if _spenta():
        return False
    try:
        import moduli.system as S
        C = getattr(S, 'KaraokeMonitorSystem', None)
        if C is not None and getattr(C, '_ver219', None) != _VER:
            orig = getattr(C, '_o219_init', None) or C.__init__
            C._o219_init = orig

            def __init__(self, *a, **k):
                orig(self, *a, **k)
                _stato['sistema'] = self
            C.__init__ = __init__
            C._ver219 = _VER
    except Exception as e:
        print('[219] aggancio sistema: %s' % e)
    import sys
    if getattr(sys, '_kd_guardia219', None) == _VER:
        return True
    # fotografia delle patch che questo KaraDom ha appena caricato
    _stato['caricate'] = _impronte()
    sys._kd_guardia219 = _VER
    threading.Thread(target=_guardia, daemon=True, name='Patch219').start()
    print('[219] guardia aggiornamenti accesa (%d patch caricate)' % len(_stato['caricate']))
    return True
