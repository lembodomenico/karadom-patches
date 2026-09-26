def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_133', '1')) == '0'
    except Exception:
        return False


def _clamp_inline(tip_window, anchor_widget):
    # tiene il tooltip DENTRO il monitor del widget (mai sullo schermo ospiti, mai
    # fuori dai bordi). Pixel fisici Win32 -> ok anche con scaling/DPI diversi.
    try:
        tip_window.update_idletasks()
        import ctypes
        from ctypes import wintypes
        u = ctypes.windll.user32

        class _RECT(ctypes.Structure):
            _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                        ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

        class _MI(ctypes.Structure):
            _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", _RECT),
                        ("rcWork", _RECT), ("dwFlags", wintypes.DWORD)]

        u.MonitorFromWindow.restype = ctypes.c_void_p
        u.MonitorFromWindow.argtypes = [ctypes.c_void_p, ctypes.c_uint]
        u.GetMonitorInfoW.restype = ctypes.c_int
        u.GetMonitorInfoW.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        u.GetAncestor.restype = ctypes.c_void_p
        u.GetAncestor.argtypes = [ctypes.c_void_p, ctypes.c_uint]
        u.GetWindowRect.restype = ctypes.c_int
        u.GetWindowRect.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        u.SetWindowPos.restype = ctypes.c_int
        u.SetWindowPos.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int,
                                   ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint]
        NEAREST = 2; GA_ROOT = 2
        try:
            _hw = anchor_widget.winfo_toplevel().winfo_id()
        except Exception:
            _hw = anchor_widget.winfo_id()
        _hw = u.GetAncestor(_hw, GA_ROOT) or _hw
        hmon = u.MonitorFromWindow(_hw, NEAREST)
        mi = _MI(); mi.cbSize = ctypes.sizeof(_MI)
        if not u.GetMonitorInfoW(hmon, ctypes.byref(mi)):
            return
        m = mi.rcMonitor
        htip = u.GetAncestor(tip_window.winfo_id(), GA_ROOT) or tip_window.winfo_id()
        r = _RECT(); u.GetWindowRect(htip, ctypes.byref(r))
        w = r.right - r.left; h = r.bottom - r.top
        x, y = r.left, r.top
        if x + w > m.right:  x = m.right - w
        if x < m.left:       x = m.left
        if y + h > m.bottom: y = m.bottom - h
        if y < m.top:        y = m.top
        if x != r.left or y != r.top:
            u.SetWindowPos(htip, 0, int(x), int(y), 0, 0, 0x0001 | 0x0004 | 0x0010)
    except Exception:
        pass


def _clamp(tw, widget):
    # USO SEMPRE il mio clamp (quello della build "dovrebbe ma non lo fa")
    _clamp_inline(tw, widget)


def _aggancia(modname):
    try:
        import importlib
        mod = importlib.import_module(modname)
    except Exception:
        return False
    TT = getattr(mod, 'ToolTip', None)
    if TT is None or getattr(TT, '_clamp133', False):
        return False
    _orig = TT.show_tip

    def _show(self, event=None):
        r = _orig(self, event)
        try:
            tw = getattr(self, 'tip_window', None)
            if tw is not None:
                _clamp(tw, self.widget)
                # riapplica dopo un attimo: a volte Tk riposiziona la finestra
                # DOPO show_tip e il primo clamp verrebbe annullato
                def _ri():
                    tw2 = getattr(self, 'tip_window', None)
                    if tw2 is not None:
                        _clamp(tw2, self.widget)
                try: self.widget.after(40, _ri)
                except Exception: pass
        except Exception:
            pass
        return r

    TT.show_tip = _show
    TT._clamp133 = True
    return True


def apply():
    if _spenta():
        return False
    fatti = []
    for m in ('moduli.ui', 'moduli.libreria_widgets'):
        if _aggancia(m):
            fatti.append(m)
    print('[TIP133] clamp tooltip attivo su:', ', '.join(fatti) if fatti else '(gia attivo/nessuno)')
    return True


def revert():
    pass


try:
    apply()
except Exception as _e:
    print('patch 133: %s' % _e)
