# 229 - tooltip dentro la finestra e rotella sulla lista suggerimenti

_VER = 1


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_229', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def _dentro_finestra(tip_window, anchor_widget):
    try:
        tip_window.update_idletasks()
        top = anchor_widget.winfo_toplevel()
        sx, sy = top.winfo_rootx(), top.winfo_rooty()
        dx, by = sx + top.winfo_width(), sy + top.winfo_height()
        pos = tip_window.wm_geometry().partition('+')[2]
        x, y = (int(v) for v in pos.replace('+-', '+').split('+')[:2]) if pos else (0, 0)
        w, h = tip_window.winfo_reqwidth(), tip_window.winfo_reqheight()
        nx = min(max(x, sx), max(sx, dx - w))
        ny = min(max(y, sy), max(sy, by - h))
        if (nx, ny) != (x, y):
            tip_window.wm_geometry('+%d+%d' % (nx, ny))
            tip_window.update_idletasks()
    except Exception:
        pass


def _tooltip():
    import moduli.libreria_widgets as LW
    if getattr(LW, '_ver229', None) == _VER:
        return
    orig = getattr(LW, '_o229_clamp', None) or LW.clamp_tooltip_to_monitor
    LW._o229_clamp = orig
    gia = hasattr(LW, 'tooltip_dentro_finestra')        # compilato nuovo: lo fa gia' da se'

    def clamp_tooltip_to_monitor(tip_window, anchor_widget):
        if not gia:
            _dentro_finestra(tip_window, anchor_widget)
        return orig(tip_window, anchor_widget)
    LW.clamp_tooltip_to_monitor = clamp_tooltip_to_monitor
    LW._ver229 = _VER


def _rotella(self):
    if getattr(self, '_rotella_suggerimenti_ok', False):
        return

    def rotella(event):
        try:
            lb, cont = self.listbox_suggerimenti, self.container_suggerimenti
            if not cont.winfo_ismapped() or event.widget is lb:
                return None
            if getattr(event, 'num', None) in (4, 5):
                passi = -1 if event.num == 4 else 1
            else:
                passi = -1 * int(event.delta / 120) or (-1 if event.delta > 0 else 1)
            lb.yview_scroll(passi, 'units')
            return 'break'
        except Exception:
            return None
    for ev in ('<MouseWheel>', '<Button-4>', '<Button-5>'):
        self.parent.winfo_toplevel().bind(ev, rotella, add='+')
    self._rotella_suggerimenti_ok = True


def apply():
    if _spenta():
        return False
    ok = False
    try:
        _tooltip()
        ok = True
    except Exception as e:
        print('[229] tooltip: %s' % e)
    try:
        from moduli.libreria import LibreriaSlider as C
        if getattr(C, '_ver229', None) != _VER:
            prima = getattr(C, '_o229_create_slider', None) or C.create_slider
            C._o229_create_slider = prima

            def create_slider(self, *a, **k):
                esito = prima(self, *a, **k)
                try:
                    _rotella(self)
                except Exception as e:
                    print('[229] rotella: %s' % e)
                return esito
            C.create_slider = create_slider
            C._ver229 = _VER
        ok = True
    except Exception as e:
        print('[229] libreria: %s' % e)
    return ok


def revert():
    try:
        import moduli.libreria_widgets as LW
        if getattr(LW, '_o229_clamp', None):
            LW.clamp_tooltip_to_monitor = LW._o229_clamp
            LW._ver229 = None
    except Exception:
        pass
    try:
        from moduli.libreria import LibreriaSlider as C
        if getattr(C, '_o229_create_slider', None):
            C.create_slider = C._o229_create_slider
            C._ver229 = None
    except Exception:
        pass
    return True
