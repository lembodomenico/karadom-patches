# 017 - la ricerca della scaletta cerca come quella in alto.

import re


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_017', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def _pezzi(testo):
    """La query spezzata ESATTAMENTE come la spezza il campo in alto:
    '*' oppure spazi, e un pezzo che comincia con '.' e' un'estensione."""
    t = (testo or '').lower().strip()
    if '*' in t:
        grezzi = [p.strip() for p in t.split('*') if p.strip()]
    else:
        grezzi = [p for p in re.split(r'\s+', t) if p]
    parti, ext = [], []
    for p in grezzi:
        if p.startswith('.'):
            parti.append(p[1:])
            ext.append(True)
        else:
            parti.append(p)
            ext.append(False)
    return parti, ext


def _parole_di(b):
    import os
    parole = b.get('parole')
    if parole is not None:
        return parole, b.get('ext', '')
    nome_lower = b.get('nome_lower') or b['nome'].lower()
    senza, est = os.path.splitext(nome_lower)
    ext = est[1:] if est else ''
    if ' - ' in senza:
        a, _s, d = senza.partition(' - ')
        parole = a.split() + d.split()
    else:
        parole = senza.split()
    if ext:
        parole.append(ext)
    return parole, ext


def _combacia(b, parti, ext_flag):
    """Lo stesso criterio del campo in alto: prefisso di parola OPPURE
    sottostringa nel nome intero; le parti si sommano in AND."""
    parole, ext = _parole_di(b)
    nome_full = b.get('nome_lower') or b['nome'].lower()
    for i, parte in enumerate(parti):
        if ext_flag[i]:
            if ext != parte:
                return False
        else:
            if not any(p.startswith(parte) for p in parole) and parte not in nome_full:
                return False
    return True


def _lista_corta_017(self, query, tetto):
    """I brani da mostrare, cercati come li cerca il campo in alto.

    Due strade, stesso risultato:
      - la tabella della 016, se c'e' (una SELECT, e il MIDI non si accorge);
      - altrimenti lo stesso ciclo, qui, sulla lista - e intanto si CHIEDE la
        tabella, come fa il campo in alto quando non ce l'ha ancora.
    """
    parti, ext_flag = _pezzi(query)
    if not parti or len(''.join(parti)) < 2:
        return None
    brani = getattr(self, 'brani_pc', None) or ()
    if not brani:
        return None

    righe = None
    try:
        righe = self._cerca_in_tabella_016(parti, ext_flag, brani, tetto)
    except Exception:
        righe = None

    if righe is None:
        # ⚠️ Niente tabella = archivio sotto i 100.000 brani, oppure tabella non
        #    ancora pronta. In tutti e due i casi qui NON si tocca niente e si
        #    lascia lavorare la funzione originale, esattamente come prima
        #    della patch: sotto la soglia non deve cambiare nulla.
        #    Intanto la si chiede, come fa il campo in alto quando non ce l'ha.
        try:
            self._prepara_tabella_016()
        except Exception:
            pass
        return None

    scelti = [brani[i] for i in righe]

    # ⚠️ La funzione originale RIFILTRA con `query in nome_lower`: cercando per
    #    piu' parole ("vasco albachiara") quel filtro butterebbe via tutto e la
    #    finestra direbbe "nessun brano trovato". Si passano quindi delle COPIE
    #    con la query dentro `nome_lower`, cosi' il filtro lascia passare quello
    #    che si e' gia' scelto qui. `nome` e `path` restano quelli veri - dentro
    #    quella funzione `nome_lower` non serve a nient'altro - quindi la
    #    finestra mostra e apre il brano giusto.
    q = (query or '').lower()
    fuori = []
    for b in scelti:
        c = dict(b)
        c['nome_lower'] = q + ' ' + (b.get('nome_lower') or b['nome'].lower())
        fuori.append(c)
    return fuori


def _con_lista_corta(self, corta, chiamata):
    pieni = self.brani_pc
    self.brani_pc = corta
    try:
        return chiamata()
    finally:
        self.brani_pc = pieni


def apply():
    if _spenta():
        return False
    try:
        import moduli.libreria_search_mixin as S
        C = getattr(S, "LibreriaSearchMixin", None)
        if C is None:
            return False
        if not hasattr(C, "_cerca_in_tabella_016"):
            return False

        if hasattr(C, "mostra_popup_suggerimenti") and not hasattr(C, "_orig_017_popup"):
            C._orig_017_popup = C.mostra_popup_suggerimenti

            def mostra_popup_suggerimenti(self, query, _orig=C._orig_017_popup):
                corta = None
                try:
                    corta = _lista_corta_017(self, query, 200)
                except Exception:
                    corta = None
                if corta is None:
                    return _orig(self, query)
                return _con_lista_corta(self, corta, lambda: _orig(self, query))

            C.mostra_popup_suggerimenti = mostra_popup_suggerimenti

        if hasattr(C, "mostra_risultati_ricerca") and not hasattr(C, "_orig_017_ricerca"):
            C._orig_017_ricerca = C.mostra_risultati_ricerca

            def mostra_risultati_ricerca(self, _orig=C._orig_017_ricerca):
                corta = None
                try:
                    corta = _lista_corta_017(self, self.entry_filtro.get().lower(), 100)
                except Exception:
                    corta = None
                if corta is None:
                    return _orig(self)
                return _con_lista_corta(self, corta, lambda: _orig(self))

            C.mostra_risultati_ricerca = mostra_risultati_ricerca

        return True
    except Exception:
        return False


def revert():
    try:
        import moduli.libreria_search_mixin as S
        C = S.LibreriaSearchMixin
        fatto = False
        if hasattr(C, "_orig_017_popup"):
            C.mostra_popup_suggerimenti = C._orig_017_popup
            del C._orig_017_popup
            fatto = True
        if hasattr(C, "_orig_017_ricerca"):
            C.mostra_risultati_ricerca = C._orig_017_ricerca
            del C._orig_017_ricerca
            fatto = True
        return fatto
    except Exception:
        return False


try:
    apply()
except Exception:
    pass
