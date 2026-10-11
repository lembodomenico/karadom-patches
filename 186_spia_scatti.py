# 186 - spia scatti
_VER = 2
def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_186', '1')) == '0'
    except Exception:
        return False


SOGLIA = 0.12
PASSO_MS = 20


def _tempi_thread():
    import ctypes
    from ctypes import wintypes
    k32 = ctypes.WinDLL('kernel32', use_last_error=True)

    class FT(ctypes.Structure):
        _fields_ = [('lo', wintypes.DWORD), ('hi', wintypes.DWORD)]

    import threading
    k32.OpenThread.restype = wintypes.HANDLE
    k32.GetCurrentProcess.restype = wintypes.HANDLE
    fuori = {}
    for t in threading.enumerate():
        tid = getattr(t, 'native_id', None)
        if not tid:
            continue
        h = k32.OpenThread(0x0800, False, tid)
        if h:
            c, e, kk, u = FT(), FT(), FT(), FT()
            if k32.GetThreadTimes(wintypes.HANDLE(h), ctypes.byref(c), ctypes.byref(e), ctypes.byref(kk), ctypes.byref(u)):
                fuori[tid] = ((kk.hi << 32 | kk.lo) + (u.hi << 32 | u.lo)) / 1e7
            k32.CloseHandle(wintypes.HANDLE(h))
    c, e, kk, u = FT(), FT(), FT(), FT()
    if k32.GetProcessTimes(wintypes.HANDLE(k32.GetCurrentProcess()), ctypes.byref(c), ctypes.byref(e), ctypes.byref(kk), ctypes.byref(u)):
        fuori['PROCESSO'] = ((kk.hi << 32 | kk.lo) + (u.hi << 32 | u.lo)) / 1e7
    return fuori


_NOMI_VISTI = {}


def _nomi():
    import threading
    for t in threading.enumerate():
        nid = getattr(t, 'native_id', None)
        if nid:
            _NOMI_VISTI[nid] = t.name
    return _NOMI_VISTI


def _classifica(prima, dopo, secondi, quanti=5):
    nomi = _nomi()
    uso = []
    py = 0.0
    for tid, v in dopo.items():
        if tid == 'PROCESSO':
            continue
        d = max(0.0, v - prima.get(tid, 0.0 if tid not in prima else v))
        py += d
        uso.append((d, nomi.get(tid, 'thread %s' % tid)))
    tot = max(0.0, dopo.get('PROCESSO', 0.0) - prima.get('PROCESSO', dopo.get('PROCESSO', 0.0)))
    nativi = max(0.0, tot - py)
    uso.sort(reverse=True)
    pezzi = ['%s %.0f%%' % (n, 100 * d / secondi) for d, n in uso[:quanti] if d > 0.005]
    pezzi.append('VLC/BASS/altro nativo %.0f%%' % (100 * nativi / secondi))
    return ', '.join(pezzi)


def _suona():
    import json, os, time, tempfile
    try:
        base = os.environ.get('LOCALAPPDATA') or tempfile.gettempdir()
        with open(os.path.join(base, 'KaraDom', 'studio_bridge.json'), 'r', encoding='utf-8') as f:
            d = json.load(f)
        return bool(d.get('playing')) and time.time() - float(d.get('ts', 0)) < 3
    except Exception:
        return False


def apply():
    if _spenta():
        return False
    import threading
    if getattr(threading, '_spia_scatti_186', False):
        return True
    import os, sys, time, traceback, tkinter

    stato = {'battito': time.time(), 'root': None}

    def _batti(root):
        stato['battito'] = time.time()
        try:
            root.after(PASSO_MS, _batti, root)
        except Exception:
            pass

    vera = tkinter.Tk.mainloop

    def mainloop(self, n=0, _v=vera):
        if stato['root'] is None:
            stato['root'] = self
            try:
                self.after(PASSO_MS, _batti, self)
            except Exception:
                pass
        return _v(self, n)

    tkinter.Tk.mainloop = mainloop

    def _guardia():
        try:
            main_tid = threading.main_thread().ident
        except Exception:
            return
        import collections
        storia = collections.deque(maxlen=40)
        t_storia = 0.0
        ultimo_rapporto = 0.0
        in_scatto = False
        inizio = 0.0
        pila = ''
        conta = 0
        peggiore = 0.0
        t_finestra = time.time()
        try:
            base_finestra = _tempi_thread()
        except Exception:
            base_finestra = {}
        while True:
            time.sleep(0.02)
            try:
                ora = time.time()
                if stato['root'] is None:
                    continue
                if ora - t_storia >= 0.25:
                    t_storia = ora
                    try:
                        storia.append((ora, _tempi_thread()))
                        _nomi()
                    except Exception:
                        pass
                ritardo = ora - stato['battito'] - PASSO_MS / 1000.0
                if ritardo > SOGLIA and not in_scatto:
                    in_scatto = True
                    inizio = stato['battito']
                    fr = sys._current_frames().get(main_tid)
                    st = traceback.extract_stack(fr) if fr is not None else []
                    pila = ' > '.join('%s:%d %s' % (os.path.basename(x.filename), x.lineno, x.name)
                                      for x in st if not x.filename.endswith(('threading.py', 'selectors.py')))
                elif in_scatto and ritardo <= SOGLIA:
                    in_scatto = False
                    durata = ora - inizio
                    conta += 1
                    peggiore = max(peggiore, durata)
                    if ora - ultimo_rapporto > 3 and _suona():
                        ultimo_rapporto = ora
                        try:
                            prima = [s for s in storia if s[0] <= inizio]
                            t0, cpu0 = prima[-1] if prima else (storia[0] if storia else (ora, {}))
                            chi = _classifica(cpu0, _tempi_thread(), max(0.05, ora - t0))
                        except Exception as e:
                            chi = 'cpu ? (%s)' % e
                        print('[SPIA-SCATTI] video/testo fermi %.2fs | thread: %s | stava facendo: %s'
                              % (durata, chi, pila[-1500:]))
                if ora - t_finestra >= 30:
                    if _suona() and conta:          # riepilogo solo se ci sono stati scatti (11-10-2026: ora su tutti i PC)
                        try:
                            ora_cpu = _tempi_thread()
                            print('[SPIA-SCATTI] ultimi 30s: %d scatti (peggiore %.2fs) | CPU KaraDom: %s'
                                  % (conta, peggiore, _classifica(base_finestra, ora_cpu, ora - t_finestra, 6)))
                            base_finestra = ora_cpu
                        except Exception as e:
                            print('[SPIA-SCATTI] riepilogo non riuscito: %s' % e)
                    else:
                        try:
                            base_finestra = _tempi_thread()
                        except Exception:
                            pass
                    t_finestra = ora
                    conta = 0
                    peggiore = 0.0
            except Exception:
                pass

    threading.Thread(target=_guardia, name='spia_scatti_186', daemon=True).start()
    threading._spia_scatti_186 = True
    print('[SPIA-SCATTI] guardiano avviato (scatti oltre %.2fs mentre suona)' % SOGLIA)
    return True


def revert():
    pass


try:
    apply()
except Exception as _e:
    print('patch 186: %s' % _e)
