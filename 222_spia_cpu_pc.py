# 222 - spia CPU del PC

import os
import sys
import threading
import time

_VER = 1
SOLO_SERIALI = ('3DCB-B3E0-C35B-FAED', '605C-14CE-1283-C667')
OGNI = 10.0


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_222', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def _serial_giusto():
    try:
        from moduli.licensing import get_hardware_id, generate_serial
        return generate_serial(*get_hardware_id()) in SOLO_SERIALI
    except Exception:
        return False


def _guarda():
    try:
        import ctypes
        k = ctypes.windll.kernel32
        k.SetThreadPriority(k.GetCurrentThread(), -2)
    except Exception:
        pass
    try:
        import psutil
    except Exception as e:
        print('[CPU-PC] psutil non disponibile: %s' % e)
        return
    n = psutil.cpu_count() or 1
    noti = {}
    psutil.cpu_percent(None)
    while True:
        time.sleep(OGNI)
        try:
            tot = psutil.cpu_percent(None)
            righe = []
            vivi = set()
            for p in psutil.process_iter(['name']):
                if p.pid == 0:
                    continue
                vivi.add(p.pid)
                q = noti.get(p.pid)
                if q is None:
                    noti[p.pid] = p
                    try:
                        p.cpu_percent(None)
                    except Exception:
                        pass
                    continue
                try:
                    c = q.cpu_percent(None) / n
                except Exception:
                    continue
                if c >= 1.0:
                    righe.append((c, q.info.get('name') or str(q.pid)))
            for pid in list(noti):
                if pid not in vivi:
                    noti.pop(pid, None)
            righe.sort(reverse=True)
            print('[CPU-PC] totale %d%% | %s' % (tot, ', '.join('%s %d%%' % (nm, c) for c, nm in righe[:5]) or '-'))
        except Exception as e:
            print('[CPU-PC] errore: %s' % e)


def apply():
    if _spenta() or os.name != 'nt':
        return False
    if getattr(sys, '_kd222', None) == _VER:
        return True
    if not _serial_giusto():
        return False
    sys._kd222 = _VER
    threading.Thread(target=_guarda, daemon=True, name='spia_cpu_222').start()
    print('[CPU-PC] spia accesa (ogni %ds)' % OGNI)
    return True


def revert():
    return False


try:
    apply()
except Exception:
    pass
