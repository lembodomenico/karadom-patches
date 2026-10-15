# 223 - preferiti grandi: niente rilettura a ogni clic

import os

_VER = 2


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_223', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def _soglia():
    try:
        from moduli.database import Database
        return int(Database.get_config('ricerca_soglia_brani', '100000') or 100000)
    except Exception:
        return 100000


def _chiave(cartella):
    try:
        return os.path.normcase(os.path.normpath(str(cartella)))
    except Exception:
        return str(cartella)


def _tanti(self):
    try:
        return len(getattr(self, 'brani_pc', None) or []) > _soglia()
    except Exception:
        return False


def _libreria_grande(self):
    if getattr(self, '_grande223', False):
        return True
    try:
        n = max(len(getattr(self, 'brani_pc', None) or []),
                len(getattr(self, 'brani_completi', None) or []))
        for v in (getattr(self, '_cache_brani', None) or {}).values():
            n = max(n, len(v[0] or []))
    except Exception:
        n = 0
    if n > _soglia():
        self._grande223 = True
    return getattr(self, '_grande223', False)


def _una_volta(delta):
    def _delta_preferito(self, cartella, *a, **k):
        if _libreria_grande(self):
            fatti = self.__dict__.setdefault('_delta223', set())
            ch = _chiave(cartella)
            if ch in fatti:
                return None
            fatti.add(ch)
        return delta(self, cartella, *a, **k)
    _delta_preferito._da223 = True
    return _delta_preferito


def apply():
    if _spenta():
        return False
    try:
        import moduli.libreria as lib
    except Exception:
        return False
    C = getattr(lib, 'LibreriaSlider', None)
    if C is None or not hasattr(C, 'carica_brani'):
        return False
    if getattr(C, '_ver223', None) == _VER:
        return True

    carica = C.carica_brani

    def carica_brani(self, cartella, forza=False, *a, **k):
        ch = _chiave(cartella)
        gia = getattr(self, '_caricato223', None)
        if not forza and gia and gia[0] == ch and gia[1] is getattr(self, 'brani_pc', None) and _tanti(self):
            return None
        r = carica(self, cartella, forza, *a, **k)
        try:
            lista = getattr(self, 'brani_pc', None)
            self._caricato223 = (ch, lista) if lista else None
        except Exception:
            pass
        return r

    C.carica_brani = carica_brani

    delta = getattr(C, '_delta_preferito', None)
    if delta is not None and not getattr(delta, '_da223', False):
        C._delta_preferito = _una_volta(delta)
        g = getattr(carica, '__globals__', None)
        if isinstance(g, dict) and g.get('_delta_preferito') is delta:
            g['_delta_preferito'] = C._delta_preferito

    C._ver223 = _VER
    print('[223] preferiti oltre %d brani: niente rilettura a ogni clic' % _soglia())
    return True


def revert():
    return False


try:
    apply()
except Exception:
    pass
