def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_145', '1')) == '0'
    except Exception:
        return False


def _riwrap(self):
    # ri-wrappa alla larghezza VERA del contenitore (ora misurabile) invece di
    # lasciare righe larghe -> rimpicciolite. Usa la macchina gia' presente.
    try:
        if getattr(self, '_do_rewrap', None):
            self._do_rewrap()
        elif getattr(self, '_deferred_rewrap', None):
            self._deferred_rewrap()
    except Exception:
        pass
    try:
        if getattr(self, '_apply_line_shrink', None):
            self._apply_line_shrink()
    except Exception:
        pass


def apply():
    if _spenta():
        return False
    try:
        import moduli.monitor as M
        C = getattr(M, 'KaraokeMonitor', None)
        if C is None or getattr(C, '_riwrap145', False):
            return True
        _orig = C.load_text

        def load_text(self, *a, **k):
            r = _orig(self, *a, **k)
            try:
                engine = k.get('engine')
                if engine is None and len(a) >= 3:
                    engine = a[2]
                if not (engine is not None and getattr(engine, 'is_video', False)):
                    _riwrap(self)
                    # se la finestra non era ancora mappata, il container misura
                    # male anche adesso: riprovo poco dopo, quando e' realizzata.
                    for _d in (250, 1000):
                        try:
                            self.text_widget.after(_d, lambda: _riwrap(self))
                        except Exception:
                            pass
            except Exception as e:
                print('[REWRAP145]', e)
            return r

        C.load_text = load_text
        C._riwrap145 = True
        print('[REWRAP145] righe ri-wrappate alla larghezza vera dopo load_text')
    except Exception as e:
        print('[REWRAP145] hook:', e)
    return True


def revert():
    pass


try:
    apply()
except Exception as _e:
    print('patch 145: %s' % _e)
