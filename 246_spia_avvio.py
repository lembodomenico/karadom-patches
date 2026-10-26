# 246 - spia avvio

import os
import sys
import threading
import time
import traceback

_VER = 2
_DURATA = 90          # secondi di osservazione dall'avvio
_PASSO = 0.25         # ogni quanto si guarda cosa fa il thread della finestra
_FERMO = 0.5          # si annota un punto quando il thread ci resta almeno tanto

# [25-10-2026] Utente: "e' un po' di tempo che quando parte si vede cosi' (finestra vuota) e di solito appare una
# scritta in alto a sx, cerca di capire perche'" + "fai prima a mettere una spia".
# Per il primo minuto e mezzo guarda il thread della finestra e annota DOVE resta fermo (file:riga > funzione),
# con i secondi dall'avvio del programma. Scrive in %LOCALAPPDATA%\KaraDom\spia_avvio.log (in fondo, non si
# cancella a ogni avvio: il registro karadom_debug.log invece riparte da zero) e lo stampa anche (diario).


def _titolare():
    try:
        from moduli.licensing import load_license
        d = load_license() or {}
        return (str(d.get('nome', '')).strip().lower(),
                str(d.get('cognome', '')).strip().lower()) == ('domenico', 'lembo')
    except Exception:
        return False


def _avvio_processo():
    """Quando e' partito il programma (non la patch): GetProcessTimes su Windows, se no adesso."""
    try:
        import ctypes
        from ctypes import wintypes
        k = ctypes.windll.kernel32
        c, e, kk, u = wintypes.FILETIME(), wintypes.FILETIME(), wintypes.FILETIME(), wintypes.FILETIME()
        if k.GetProcessTimes(k.GetCurrentProcess(), ctypes.byref(c), ctypes.byref(e), ctypes.byref(kk), ctypes.byref(u)):
            ft = (c.dwHighDateTime << 32) | c.dwLowDateTime
            return ft / 1e7 - 11644473600.0
    except Exception:
        pass
    return time.time()


_T0 = _avvio_processo()
_FILE = os.path.join(os.environ.get('LOCALAPPDATA') or os.path.expanduser('~'), 'KaraDom', 'spia_avvio.log')


def _scrivi(msg):
    riga = '%s +%5.1fs %s' % (time.strftime('%d-%m %H:%M:%S'), time.time() - _T0, msg)
    try:
        print('[SPIA-AVVIO] ' + riga)
    except Exception:
        pass
    try:
        with open(_FILE, 'a', encoding='utf-8') as f:
            f.write(riga + '\n')
    except Exception:
        pass


def _dove(frame):
    """Gli ultimi 4 punti della pila del thread della finestra, il piu' interno per ultimo."""
    pila = traceback.extract_stack(frame)[-4:]
    return ' > '.join('%s:%d %s' % (os.path.basename(p.filename), p.lineno, p.name) for p in pila)


def _finestre():
    """Le finestre visibili di QUESTO programma, lette da Windows (mai Tk da un altro thread: bloccherebbe)."""
    try:
        import ctypes
        from ctypes import wintypes
        u = ctypes.windll.user32
        pid = os.getpid()
        out = []

        @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        def cb(h, _l):
            p = wintypes.DWORD()
            u.GetWindowThreadProcessId(h, ctypes.byref(p))
            if p.value == pid and u.IsWindowVisible(h):
                n = u.GetWindowTextLengthW(h)
                b = ctypes.create_unicode_buffer(n + 1)
                u.GetWindowTextW(h, b, n + 1)
                r = wintypes.RECT()
                u.GetWindowRect(h, ctypes.byref(r))
                out.append('"%s" %dx%d' % (b.value[:30], r.right - r.left, r.bottom - r.top))
            return True
        u.EnumWindows(cb, 0)
        return ', '.join(out) or 'nessuna'
    except Exception as e:
        return '?(%s)' % e


def _albero(w, liv=0, out=None, max_liv=3):
    """Pannelli della finestra: classe, come e' messo (pack/grid/place), visibile, grandezza. Nel thread della finestra."""
    if out is None:
        out = []
    try:
        figli = w.winfo_children()
        testo = ''
        try:
            testo = str(w.cget('text'))[:40]
        except Exception:
            pass
        out.append('%s%s %s vis=%d %dx%d @%d,%d figli=%d %s' % ('  ' * liv, w.winfo_class(), w.winfo_manager() or '-',
                                                     w.winfo_ismapped(), w.winfo_width(), w.winfo_height(),
                                                     w.winfo_x(), w.winfo_y(), len(figli), repr(testo) if testo else ''))
        if liv < max_liv:
            for f in figli[:25]:
                _albero(f, liv + 1, out, max_liv)
    except Exception as e:
        out.append('  ' * liv + '?(%s)' % e)
    return out


def _fotografa(quando):
    """Chiesta dal thread della spia, eseguita DAL thread della finestra (after): Tk non si tocca da fuori."""
    try:
        import tkinter
        r = tkinter._default_root
        if r is None:
            return

        def scatta():
            _scrivi('--- struttura della finestra a +%ds ---' % quando)
            for riga in _albero(r):
                _scrivi('   ' + riga)
        r.after(0, scatta)
    except Exception as e:
        _scrivi('foto finestra non riuscita: %s' % e)


def _guarda():
    main = threading.main_thread().ident
    _scrivi('===== avvio: spia accesa (%.1f s dopo la partenza del programma), pid %d' % (time.time() - _T0, os.getpid()))
    ultimo, da, annotato = None, time.time(), False
    fine = time.time() + _DURATA
    prossime_finestre = 0
    fatte = set()
    while time.time() < fine:
        time.sleep(_PASSO)
        try:
            fr = sys._current_frames().get(main)
            if fr is None:
                continue
            qui = _dove(fr)
        except Exception:
            continue
        ora = time.time()
        if qui != ultimo:
            ultimo, da, annotato = qui, ora, False
        elif not annotato and ora - da >= _FERMO:
            annotato = True
            _scrivi('finestra ferma qui da %.1f s: %s' % (ora - da, qui))
        elif annotato and int(ora - da) and int(ora - da) % 3 == 0 and (ora - da) % 3 < _PASSO:
            _scrivi('   ... ancora ferma (%.0f s)' % (ora - da))
        if 'mainloop' in qui:
            for s in (12, 15, 20, 30, 45):
                if ora - _T0 >= s and s not in fatte:
                    fatte.add(s)
                    _fotografa(s)
        if ora >= prossime_finestre:
            prossime_finestre = ora + 2
            _scrivi('finestre visibili: %s' % _finestre())
    _scrivi('===== fine osservazione (%d s)' % _DURATA)


def apply():
    if not _titolare():
        return False
    try:
        from moduli.database import Database
        if str(Database.get_config('patch_246', '1')).strip() in ('0', 'no', 'off'):
            return False
    except Exception:
        pass
    if getattr(sys, '_spia246', False):
        return True
    sys._spia246 = True
    threading.Thread(target=_guarda, daemon=True, name='spia_avvio_246').start()
    return True


def revert():
    return False
