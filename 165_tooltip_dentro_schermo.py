import sys


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_165', '1')) == '0'
    except Exception:
        return False


def _clamp(tip, anchor):
    """Tiene il tooltip DENTRO il monitor del widget (no sforo sullo schermo pubblico).
    Pixel fisici Win32 -> ok anche con DPI/scaling diversi. Silenzioso su errore."""
    try:
        tip.update_idletasks()
        import ctypes
        from ctypes import wintypes
        u = ctypes.windll.user32

        class R(ctypes.Structure):
            _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                        ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

        class MI(ctypes.Structure):
            _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", R),
                        ("rcWork", R), ("dwFlags", wintypes.DWORD)]

        for fn, rt, at in (
            ("MonitorFromWindow", ctypes.c_void_p, [ctypes.c_void_p, ctypes.c_uint]),
            ("GetMonitorInfoW", ctypes.c_int, [ctypes.c_void_p, ctypes.c_void_p]),
            ("GetAncestor", ctypes.c_void_p, [ctypes.c_void_p, ctypes.c_uint]),
            ("GetWindowRect", ctypes.c_int, [ctypes.c_void_p, ctypes.c_void_p]),
            ("SetWindowPos", ctypes.c_int, [ctypes.c_void_p, ctypes.c_void_p,
                                            ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                            ctypes.c_int, ctypes.c_uint]),
        ):
            f = getattr(u, fn); f.restype = rt; f.argtypes = at

        GA_ROOT = 2
        NEAREST = 2
        try:
            hw = anchor.winfo_toplevel().winfo_id()
        except Exception:
            hw = anchor.winfo_id()
        hw = u.GetAncestor(hw, GA_ROOT) or hw
        hmon = u.MonitorFromWindow(hw, NEAREST)
        mi = MI(); mi.cbSize = ctypes.sizeof(MI)
        if not u.GetMonitorInfoW(hmon, ctypes.byref(mi)):
            return
        m = mi.rcMonitor
        ht = u.GetAncestor(tip.winfo_id(), GA_ROOT) or tip.winfo_id()
        r = R(); u.GetWindowRect(ht, ctypes.byref(r))
        w = r.right - r.left; h = r.bottom - r.top
        x = r.left; y = r.top
        if x + w > m.right:  x = m.right - w
        if x < m.left:       x = m.left
        if y + h > m.bottom: y = m.bottom - h
        if y < m.top:        y = m.top
        if x != r.left or y != r.top:
            u.SetWindowPos(ht, 0, int(x), int(y), 0, 0, 0x0001 | 0x0004 | 0x0010)
    except Exception:
        pass


def _wrap(cls, method, getwin):
    o = getattr(cls, method, None)
    if o is None or getattr(o, '_clamp165', False):
        return
    def w(self, *a, **k):
        r = o(self, *a, **k)
        try:
            win, anc = getwin(self, a)
            if win is not None and anc is not None:
                _clamp(win, anc)
        except Exception:
            pass
        return r
    w._clamp165 = True
    setattr(cls, method, w)


def apply():
    if _spenta():
        return False
    ok = False
    # 1) sostituisci l'helper condiviso: ogni tooltip che gia' lo chiama (import a
    #    runtime) usa da ora questo -> un colpo solo ripara tutti.
    try:
        import moduli.libreria_widgets as LW
        LW.clamp_tooltip_to_monitor = _clamp
        ok = True
    except Exception:
        pass
    # 2) avvolgi anche le classi tooltip, per gli exe VECCHI che il clamp non lo
    #    chiamano affatto (doppio clamp = innocuo).
    try:
        import moduli.ui as U
        _wrap(U.ToolTip, 'show_tip',
              lambda self, a: (getattr(self, 'tip_window', None), getattr(self, 'widget', None)))
    except Exception:
        pass
    try:
        import moduli.libreria_widgets as LW2
        _wrap(LW2.ToolTip, 'show_tip',
              lambda self, a: (getattr(self, 'tip_window', None), getattr(self, 'widget', None)))
    except Exception:
        pass
    try:
        import moduli.sampler as SA
        _wrap(SA._SamplerTooltip, '_show',
              lambda self, a: (getattr(self, 'tip', None),
                               (a[0] if a else (self.widgets[0] if getattr(self, 'widgets', None) else None))))
    except Exception:
        pass
    return ok


try:
    apply()
except Exception as _e:
    print('patch 165: %s' % _e)
