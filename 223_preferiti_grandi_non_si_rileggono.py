# 223 - preferiti grandi: niente rilettura a ogni clic

import os

_VER = 1


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
    if delta is not None:
        def _delta_preferito(self, cartella, *a, **k):
            if _tanti(self):
                fatti = self.__dict__.setdefault('_delta223', set())
                ch = _chiave(cartella)
                if ch in fatti:
                    return None
                fatti.add(ch)
            return delta(self, cartella, *a, **k)
        C._delta_preferito = _delta_preferito

    C._ver223 = _VER
    print('[223] preferiti oltre %d brani: niente rilettura a ogni clic' % _soglia())
    return True


def revert():
    return False


try:
    apply()
except Exception:
    pass
