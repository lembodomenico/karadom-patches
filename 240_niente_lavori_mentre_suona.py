# 240 - niente lavori mentre suona

import json
import os
import tempfile
import time

_VER = 2


def _titolare():
    """Solo sui PC del titolare: licenza FIRMATA intestata a Domenico Lembo (come la 233)."""
    try:
        from moduli.licensing import load_license
        d = load_license() or {}
        return (str(d.get('nome', '')).strip().lower(),
                str(d.get('cognome', '')).strip().lower()) == ('domenico', 'lembo')
    except Exception:
        return False


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_240', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def _log(msg):
    try:
        print('[240] %s' % msg)
    except Exception:
        pass


def _suona():
    """Stesso segnale della spia 186: studio_bridge.json aggiornato da meno di 3 s con playing=true."""
    try:
        base = os.environ.get('LOCALAPPDATA') or tempfile.gettempdir()
        with open(os.path.join(base, 'KaraDom', 'studio_bridge.json'), 'r', encoding='utf-8') as f:
            d = json.load(f)
        return bool(d.get('playing')) and time.time() - float(d.get('ts', 0)) < 3
    except Exception:
        return False


def _in_memoria(self, cartella):
    cache = getattr(self, '_cache_brani', None) or {}
    chiave = os.path.normpath(str(cartella)).lower()
    return chiave in cache


def apply():
    if not _titolare():
        return False
    if _spenta():
        _log('spenta (patch_240=0)')
        return False
    try:
        import moduli.libreria as lib
    except Exception as e:
        _log('libreria non trovata: %s' % e)
        return False
    C = getattr(lib, 'LibreriaSlider', None)
    if C is None or not hasattr(C, 'carica_brani'):
        return False
    if getattr(C, '_ver240', None) == _VER:
        return True
    originale = getattr(C, '_o240_carica_brani', None) or C.carica_brani
    C._o240_carica_brani = originale

    def carica_brani(self, cartella, forza=False, *a, **k):
        # gia' in memoria, richiesta esplicita (tasto destro) o niente musica: come sempre
        if forza or _in_memoria(self, cartella) or not _suona():
            self._attesa240 = None
            return originale(self, cartella, forza, *a, **k)
        # mentre suona la ricostruzione di centinaia di migliaia di voci ferma il testo:
        # si rimanda a fine brano (vale l'ULTIMA cartella chiesta)
        primo = getattr(self, '_attesa240', None) is None
        self._attesa240 = (cartella, a, k)
        _log('suona: carico %s a fine brano' % cartella)
        if primo:
            def controlla():
                att = getattr(self, '_attesa240', None)
                if att is None:
                    return
                if _suona():
                    try:
                        self.parent.after(1000, controlla)
                    except Exception:
                        pass
                    return
                self._attesa240 = None
                c, aa, kk = att
                _log('brano finito: carico %s' % c)
                try:
                    originale(self, c, False, *aa, **kk)
                except Exception as e:
                    _log('carico rimandato: %s' % e)
            try:
                self.parent.after(1000, controlla)
            except Exception:
                return originale(self, cartella, forza, *a, **k)
        return None

    C.carica_brani = carica_brani
    C._ver240 = _VER
    _log('mentre suona gli elenchi da ricostruire aspettano la fine del brano')
    return True


def revert():
    try:
        import moduli.libreria as lib
        C = lib.LibreriaSlider
        if getattr(C, '_o240_carica_brani', None):
            C.carica_brani = C._o240_carica_brani
            C._ver240 = None
            return True
    except Exception:
        pass
    return False
