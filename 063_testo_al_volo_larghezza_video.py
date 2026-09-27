# 063 - Testo al volo: le righe si adattano alla larghezza del video (il testo non esce piu' dallo schermo)
def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_063', '1')) == '0'
    except Exception:
        return False


def apply():
    if _spenta():
        return False
    import types
    try:
        from moduli.system import KaraokeMonitorSystem as C
    except Exception as _e:
        print('patch 063: no system %s' % _e)
        return False
    f = getattr(C, '_testo_ass', None)
    if f is None:
        return False
    if getattr(f, '_larghezza_063', False):
        return True
    code = getattr(f, '__code__', None)
    if code is None:
        return False
    OLD, NEW = 0.58, 0.66
    if not any(isinstance(c, float) and abs(c - OLD) < 1e-9 for c in code.co_consts):
        # costante non presente (build gia' corretta): niente da fare
        try:
            f._larghezza_063 = True
        except Exception:
            pass
        return True
    consts = tuple(NEW if (isinstance(c, float) and abs(c - OLD) < 1e-9) else c
                   for c in code.co_consts)
    try:
        newcode = code.replace(co_consts=consts)
    except Exception as _e:
        print('patch 063: code.replace non disponibile (%s)' % _e)
        return False
    nf = types.FunctionType(newcode, f.__globals__, f.__name__,
                            f.__defaults__, f.__closure__)
    nf.__dict__.update(getattr(f, '__dict__', {}))
    nf._orig_063 = f
    nf._larghezza_063 = True
    C._testo_ass = nf
    print('[TESTO] patch 063: parole per riga adattate alla larghezza del video (0.58 -> 0.66)')
    return True


def revert():
    try:
        from moduli.system import KaraokeMonitorSystem as C
        o = getattr(getattr(C, '_testo_ass', None), '_orig_063', None)
        if o is not None:
            C._testo_ass = o
    except Exception:
        pass


try:
    apply()
except Exception as _e:
    print('patch 063: %s' % _e)
