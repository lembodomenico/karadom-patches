import os


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_138', '1')) == '0'
    except Exception:
        return False


def _ritrova_file_nei_preferiti(self, vecchio):
    """Cerca un FILE per NOME nelle cartelle registrate nei preferiti (istantaneo, dagli
    elenchi gia' salvati). Torna il percorso attuale se lo trova ed esiste."""
    try:
        nome = os.path.basename(vecchio).lower()
        if not nome:
            return None
        from moduli.database import Database
        cache = getattr(self, "_cache_brani", None) or {}
        for pref in Database.get_preferiti():
            q = pref.get('path', '')
            if not q:
                continue
            elenco = None
            chiave = os.path.normpath(q).lower()
            if chiave in cache:
                try:
                    elenco = cache[chiave][0]
                except Exception:
                    elenco = None
            if elenco is None:
                try:
                    elenco = self._leggi_cache_disco(q)
                except Exception:
                    elenco = None
            if not elenco:
                continue
            for p in elenco:
                if os.path.basename(p).lower() == nome and os.path.exists(p):
                    return p
        return None
    except Exception:
        return None


def _memorizza_nuovo_percorso(self, vecchio, nuovo):
    """MEMORIZZA la nuova posizione: aggiorna le righe della scaletta che puntavano al
    vecchio percorso (e le salva)."""
    try:
        vn = os.path.normpath(vecchio).lower()
        cambiato = False
        for iid, data in list(getattr(self, '_sc_row_data', {}).items()):
            if os.path.normpath(str(data.get('path', ''))).lower() == vn:
                data['path'] = nuovo
                cambiato = True
        if cambiato:
            try:
                self.salva_righe()
            except Exception:
                pass
        print("[RITROVA138] %s -> %s (memorizzato=%s)" % (os.path.basename(vecchio), nuovo, cambiato))
    except Exception as e:
        print("[RITROVA138] memorizza:", e)


def apply():
    if _spenta():
        return False
    try:
        import moduli.libreria as lib
        C = getattr(lib, 'LibreriaSlider', None)
        if C is None or getattr(C, '_ritrova138', False):
            return True
        C._ritrova_file_nei_preferiti = _ritrova_file_nei_preferiti
        C._memorizza_nuovo_percorso = _memorizza_nuovo_percorso
        _op = C.play_brano

        def _wrap(self, path, entry_ton=None, cantante="", brano="", tonalita=None, *a, **k):
            try:
                _p = str(path or '')
                if _p and '://' not in _p and 'youtu' not in _p.lower() and not os.path.exists(_p):
                    nuovo = self._ritrova_file_nei_preferiti(_p)
                    if nuovo:
                        self._memorizza_nuovo_percorso(_p, nuovo)
                        path = nuovo
            except Exception as e:
                print('[RITROVA138]', e)
            return _op(self, path, entry_ton, cantante, brano, tonalita, *a, **k)

        C.play_brano = _wrap
        C._ritrova138 = True
        print('[RITROVA138] file mancante -> cercato per nome nelle cartelle dei preferiti (e memorizzato)')
    except Exception as e:
        print('[RITROVA138] hook:', e)
    return True


def revert():
    pass


try:
    apply()
except Exception as _e:
    print('patch 138: %s' % _e)
