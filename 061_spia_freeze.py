# 061 - Spia "Non risponde": se il programma si blocca, scrive nel diario dove si e' bloccato
def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_061', '1')) == '0'
    except Exception:
        return False


def apply():
    if _spenta():
        return False
    import threading
    if getattr(threading, '_spia_freeze_061', False):
        return True
    import sys, time, traceback

    def _watch():
        try:
            main_tid = threading.main_thread().ident
        except Exception:
            return
        prev_key = None
        stuck_s = 0
        step = 2
        while True:
            time.sleep(step)
            try:
                frames = sys._current_frames()
                fr = frames.get(main_tid)
                if fr is None:
                    continue
                stack = traceback.format_stack(fr)
                inner = stack[-1] if stack else ""
                # UI INATTIVA = ferma nel mainloop di Tk (normale): NON e' un blocco.
                if ('mainloop' in inner) or ('dooneevent' in inner) or ('tkinter' in inner and 'mainloop' in "".join(stack[-2:])):
                    stuck_s = 0
                    prev_key = None
                    continue
                # chiave = ultime 3 righe (dove sta davvero)
                key = "".join(stack[-3:])
                if key and key == prev_key:
                    stuck_s += step
                    if stuck_s in (6, 12, 30, 60):
                        _flat = " | ".join(s.strip().replace("\n", " ") for s in stack[-8:])
                        print("[SPIA-FREEZE] UI ferma da %ds -> %s" % (stuck_s, _flat[:1400]))
                else:
                    if stuck_s >= 6:
                        print("[SPIA-FREEZE] UI ripartita dopo %ds" % stuck_s)
                    stuck_s = 0
                    prev_key = key
            except Exception:
                pass

    t = threading.Thread(target=_watch, name="spia_freeze_061", daemon=True)
    t.start()
    threading._spia_freeze_061 = True
    print("[SPIA-FREEZE] guardiano avviato (rileva blocchi UI)")
    return True


def revert():
    # il thread e' daemon: si ferma alla chiusura. Nulla da annullare a caldo.
    pass


try:
    apply()
except Exception as _e:
    print('patch 061: %s' % _e)
