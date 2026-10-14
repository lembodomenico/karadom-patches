# 191 - KaraDom DJ al posto del DJ-set
import base64
import os
import sys
import types
import zlib

_VER191 = 5

_CODICE = (
    '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'
)


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_191', '1')) == '0'
    except Exception:
        return False


def _modulo():
    nome = 'moduli.karadom_dj'
    m = sys.modules.get(nome)
    if m is not None and getattr(m, '_v191', 0) >= _VER191:
        return m
    import moduli
    m = types.ModuleType(nome)
    m.__package__ = 'moduli'
    m.__file__ = nome.replace('.', '/') + '.py'
    sys.modules[nome] = m
    exec(compile(zlib.decompress(base64.b64decode(_CODICE)).decode('utf-8'), 'karadom_dj.py', 'exec'), m.__dict__)
    m._v191 = _VER191
    moduli.karadom_dj = m
    return m


def apply():
    if _spenta() or os.name != 'nt':      # KaraDom OS (Linux): KaraDom DJ non c'e', resta il DJ-set
        return False
    try:
        import moduli.djset as D
        if getattr(D, '_p191', None) == _VER191:
            return True
        if getattr(D, '_p191_o', None) is None:
            D._p191_o = D.apri_djset

        def apri_djset(parent, system):
            return _modulo().apri_karadom_dj(parent, system)
        D.apri_djset = apri_djset
        D._p191 = _VER191
        return True
    except Exception as e:
        print('[patch191] %s' % e)
        return False


def revert():
    try:
        import moduli.djset as D
        if getattr(D, '_p191_o', None) is not None:
            D.apri_djset = D._p191_o
            D._p191 = None
        return True
    except Exception:
        return False


try:
    apply()
except Exception:
    pass
