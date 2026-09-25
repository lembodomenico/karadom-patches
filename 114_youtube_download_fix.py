import threading
import time as _t


def _install():
    import os
    import inspect
    import moduli.yt2mp3 as Y
    P = getattr(Y, 'YoutubePanel', None)
    if P is None:
        return None  # pannello non ancora caricato: riprova dopo
    cur = getattr(P, '_download_thread', None)
    if not callable(cur):
        return None
    if getattr(P, '_dl_fix_114', False):
        return True

    # gia' con firma giusta (accetta 'formato' o *args)? niente da fare
    try:
        params = list(inspect.signature(cur).parameters.values())
        if any(p.name == 'formato' for p in params) or \
           any(p.kind == p.VAR_POSITIONAL for p in params):
            P._dl_fix_114 = True
            return True
    except Exception:
        pass

    # cur = wrapper a 3 argomenti (patch 003 `_download_ricorda`): recupero il
    # downloader VERO dalla sua closure (scarica_orig, che accetta formato).
    src = None
    for cell in (getattr(cur, '__closure__', None) or ()):
        try:
            v = cell.cell_contents
        except Exception:
            continue
        if callable(v) and v is not cur:
            src = v
            break
    if src is None:
        src = Y.__dict__.get('_kd_download_thread')
    if not callable(src):
        return None

    def _dl(self, url, cartella, formato='mp4', *a, **k):
        prima = set(os.listdir(cartella)) if os.path.isdir(cartella) else set()
        try:
            esito = src(self, url, cartella, formato)
        except TypeError:
            esito = src(self, url, cartella)   # se src fosse a sua volta a 3 arg
        try:
            est = ('.mp4', '.mp3', '.m4a', '.webm', '.mkv', '.opus')
            nuovi = [os.path.join(cartella, f) for f in os.listdir(cartella)
                     if f not in prima and f.lower().endswith(est)]
            if nuovi:
                if not hasattr(self, '_scaricati'):
                    self._scaricati = {}
                self._scaricati[url] = max(nuovi, key=os.path.getmtime)
        except Exception:
            pass
        return esito

    P._download_thread = _dl
    P._dl_fix_114 = True
    print('[DL114] _download_thread corretto (firma con formato) installato')
    return True


def _retry_loop():
    for _ in range(40):          # fino a ~80s: aspetta che il pannello esista
        try:
            r = _install()
        except Exception as e:
            print('[DL114] retry:', e)
            r = None
        if r:
            return
        _t.sleep(2.0)


def apply():
    try:
        r = _install()
    except Exception as e:
        print('[DL114]', e)
        r = None
    if not r:
        threading.Thread(target=_retry_loop, daemon=True, name='dl-fix-114').start()
    return True


try:
    apply()
except Exception as _e:
    print('patch 114: %s' % _e)
