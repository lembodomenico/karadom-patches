# 056 - Telefono USB (SKV) disattivato: adb non parte piu, niente errori a ripetizione
def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_056', '1')) == '0'
    except Exception:
        return False


def apply():
    if _spenta():
        return False
    import os as _os
    import io as _io
    import subprocess as _sp
    if getattr(_sp.Popen, '_adb_noop_056', False):
        return True

    class _FakeAdb(object):
        def __init__(self, args, *a, **k):
            self.args = args
            self.returncode = 0
            self.pid = -1
            _txt = bool(k.get('text') or k.get('universal_newlines') or k.get('encoding'))
            if _txt:
                self.stdout = _io.StringIO('')
                self.stderr = _io.StringIO('')
            else:
                self.stdout = _io.BytesIO(b'')
                self.stderr = _io.BytesIO(b'')
            self.stdin = None
            self._txt = _txt

        def communicate(self, *a, **k):
            return ('', '') if self._txt else (b'', b'')

        def wait(self, *a, **k):
            return 0

        def poll(self):
            return 0

        def kill(self):
            pass

        def terminate(self):
            pass

        def send_signal(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    _orig = _sp.Popen

    def _popen056(args, *a, **k):
        try:
            primo = args[0] if isinstance(args, (list, tuple)) and args else args
            if _os.path.basename(str(primo)).lower() in ('adb.exe', 'adb', 'fastboot.exe'):
                return _FakeAdb(args, *a, **k)
        except Exception:
            pass
        return _orig(args, *a, **k)

    _popen056._adb_noop_056 = True
    _popen056._orig_056 = _orig
    _sp.Popen = _popen056
    return True


def revert():
    try:
        import subprocess as _sp
        _o = getattr(_sp.Popen, '_orig_056', None)
        if _o is not None:
            _sp.Popen = _o
    except Exception:
        pass


try:
    apply()
except Exception as _e:
    print('patch 056: %s' % _e)
