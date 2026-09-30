import sys


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_164', '1')) == '0'
    except Exception:
        return False


def apply():
    if _spenta():
        return False
    try:
        import moduli.libreria as L
    except Exception:
        return False
    C = getattr(L, 'LibreriaSlider', None)
    if C is None or getattr(C, '_wheel_sugg_righe_patched', False):
        return True
    orig = getattr(C, '_sc_edit_brano', None)
    if orig is None:
        return True

    def _sc_edit_brano(self, iid, text_item_id):
        r = orig(self, iid, text_item_id)
        try:
            lb = getattr(self, '_sc_brano_sugg_lb', None)
            en = getattr(self, '_sc_edit_entry', None)
            fr = getattr(self, '_sc_brano_sugg', None)
            if lb is not None:
                def _wheel(e):
                    try:
                        d = -1 * int(e.delta / 120) if getattr(e, 'delta', 0) else 0
                        if d == 0:
                            n = getattr(e, 'num', 0)
                            d = -1 if n == 4 else (1 if n == 5 else 0)
                        lb.yview_scroll(d, 'units')
                    except Exception:
                        pass
                    return 'break'
                for w in (lb, en, fr):
                    if w is not None:
                        w.bind('<MouseWheel>', _wheel)
                        w.bind('<Button-4>', _wheel)
                        w.bind('<Button-5>', _wheel)
        except Exception:
            pass
        return r

    C._sc_edit_brano = _sc_edit_brano
    C._wheel_sugg_righe_patched = True
    return True


try:
    apply()
except Exception as _e:
    print('patch 164: %s' % _e)
