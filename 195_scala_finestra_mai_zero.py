def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_195', '1')) == '0'
    except Exception:
        return False


_ULTIMA = {'v': 1.0}


def apply():
    if _spenta():
        return False
    try:
        from customtkinter.windows.widgets.scaling.scaling_tracker import ScalingTracker as ST
    except Exception as e:
        print('[SCALA195] customtkinter:', e)
        return False
    if getattr(ST, '_mai_zero195', False):
        return True
    _orig = ST.get_window_dpi_scaling.__func__

    def get_window_dpi_scaling(cls, window):
        try:
            v = _orig(cls, window)
        except Exception:
            v = 0
        try:
            v = float(v)
        except Exception:
            v = 0.0
        if v > 0.2:
            _ULTIMA['v'] = v
            return v
        print('[SCALA195] DPI della finestra non disponibile (%r): uso %.2f' % (v, _ULTIMA['v']))
        return _ULTIMA['v']
    ST.get_window_dpi_scaling = classmethod(get_window_dpi_scaling)

    try:
        from customtkinter.windows.widgets.scaling.scaling_base_class import CTkScalingBaseClass as B
        _rev = B._reverse_widget_scaling

        def _reverse_widget_scaling(self, value):
            try:
                return _rev(self, value)
            except ZeroDivisionError:
                return value
        B._reverse_widget_scaling = _reverse_widget_scaling
    except Exception as e:
        print('[SCALA195] base:', e)
    ST._mai_zero195 = True
    return True


def revert():
    return False
