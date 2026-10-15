# 223 - preferiti grandi: niente rilettura a ogni clic

import os

_VER = 4


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


def _segno():
    return os.path.join(os.environ.get('LOCALAPPDATA') or os.path.expanduser('~'),
                        'KaraDom', 'elenchi', 'libreria_grande_223')


def _libreria_grande(self):
    if getattr(self, '_grande223', False):
        return True
    if os.path.exists(_segno()):
        self._grande223 = True
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
        try:
            os.makedirs(os.path.dirname(_segno()), exist_ok=True)
            open(_segno(), 'w').write(str(n))
        except Exception:
            pass
    return getattr(self, '_grande223', False)


def _una_volta(delta):
    def _delta_preferito(self, cartella, *a, **k):
        if _libreria_grande(self):
            return None
        return delta(self, cartella, *a, **k)
    _delta_preferito._da223 = True
    return _delta_preferito


def _mtime(self, chiave):
    try:
        f = self._file_cache_brani(chiave)
        return os.path.getmtime(f) if f and os.path.exists(f) else 0.0
    except Exception:
        return 0.0


def _dal_padre(self, cartella):
    """Sottocartella di un elenco gia' in memoria: si ricava da quello, senza disco."""
    cache = getattr(self, '_cache_brani', None)
    if not cache:
        return False
    chiave = os.path.normpath(str(cartella)).lower()
    if chiave in cache:
        return False
    padre = None
    for k in list(cache):
        if chiave.startswith(k.rstrip('\\/') + os.sep) and (padre is None or len(k) > len(padre)):
            padre = k
    if padre is None:
        return False
    if _mtime(self, chiave) > _mtime(self, padre):
        return False          # elenco della sottocartella piu' nuovo (aggiornato a mano): vale quello
    try:
        _completi, voci, indice = cache[padre]
    except Exception:
        return False
    import threading
    pref = chiave + os.sep

    def lavora():
        import time as _t
        sub, sub_idx = [], {}
        for n, v in enumerate(voci):
            if n % 5000 == 0 and n:
                _t.sleep(0.002)
            try:
                p = v['path']
            except Exception:
                continue
            if os.path.normpath(p).lower().startswith(pref):
                sub.append(v)
                if p in indice:
                    sub_idx[p] = indice[p]
        if not sub:
            def _normale():
                carica_vera(self, cartella)
            self.parent.after(0, _normale)
            return
        completi = [v['path'] for v in sub]

        def _assegna():
            cache[chiave] = (completi, sub, sub_idx)
            if os.path.normpath(str(getattr(self, 'percorso_attivo', '') or '')).lower() != chiave:
                return
            self.brani_completi, self.brani_pc, self.indice_preferiti = completi, sub, sub_idx
            self._caricato223 = (_chiave(cartella), sub)
            print("✅ %d brani (dalla memoria del preferito)" % len(sub))
        self.parent.after(0, _assegna)

    self.percorso_attivo = cartella
    try:
        self._aggancia_caricamento_016()
    except Exception:
        pass
    threading.Thread(target=lavora, daemon=True, name='padre223').start()
    return True


carica_vera = None


def apply():
    global carica_vera
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
        if not forza and _libreria_grande(self):
            try:
                if _dal_padre(self, cartella):
                    return None
            except Exception as e:
                print('[223] dal preferito: %s' % e)
        r = carica(self, cartella, forza, *a, **k)
        try:
            lista = getattr(self, 'brani_pc', None)
            self._caricato223 = (ch, lista) if lista else None
        except Exception:
            pass
        return r

    C.carica_brani = carica_brani
    carica_vera = carica

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
