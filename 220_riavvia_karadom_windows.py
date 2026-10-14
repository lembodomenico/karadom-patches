# 220 - "Riavvia KaraDom" funziona sul programma installato

import os
import sys

_VER = 1


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_220', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def _exe_vero():
    """Il vero KaraDom.exe. Nel programma compilato sys.executable e' un python.exe che sul
    disco NON esiste: rilanciare quello dava '[WinError 2] Impossibile trovare il file'."""
    for c in (sys.argv[0] if sys.argv else '', os.path.join(os.path.dirname(sys.executable), 'KaraDom.exe')):
        try:
            p = os.path.abspath(c)
            if p.lower().endswith('.exe') and os.path.exists(p) and 'python' not in os.path.basename(p).lower():
                return p
        except Exception:
            pass
    return None


def apply():
    if _spenta() or os.name != 'nt':
        return False
    import subprocess
    if getattr(subprocess.Popen, '_kd220', None) == _VER:
        return True
    Vero = getattr(subprocess.Popen, '_kd220_orig', None) or subprocess.Popen

    class Popen(Vero):
        def __init__(self, args, *a, **k):
            try:
                if isinstance(args, (list, tuple)) and args and str(args[0]) == sys.executable \
                        and not os.path.exists(sys.executable):
                    exe = _exe_vero()
                    if exe:
                        resto = [str(x) for x in args[1:]]
                        if resto and os.path.abspath(resto[0]) == exe:
                            resto = resto[1:]
                        riga = ' '.join('"%s"' % x for x in [exe] + resto)
                        # si riapre DOPO un paio di secondi, quando questo KaraDom e' chiuso:
                        # altrimenti il nuovo trova il vecchio ancora aperto e si ferma
                        args = ['cmd', '/c', 'ping -n 3 127.0.0.1 >nul & start "" ' + riga]
                        k.setdefault('creationflags', 0x08000000)       # senza finestra nera
                        k['close_fds'] = True
                        print('[220] riavvio: %s' % exe)
            except Exception as e:
                print('[220] %s' % e)
            super().__init__(args, *a, **k)

    Popen._kd220 = _VER
    Popen._kd220_orig = Vero
    subprocess.Popen = Popen
    return True


try:
    apply()
except Exception:
    pass
