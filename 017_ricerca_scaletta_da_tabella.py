# 017 - ricerca della scaletta dalla tabella della 016.


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_017', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def _cerca_nome_017(self, query, tetto):
    import os
    import sqlite3
    pronta = getattr(self, '_tabella016', None)
    brani = getattr(self, 'brani_pc', None) or ()
    if not pronta or pronta[0] is not brani or pronta[1] != len(brani):
        return None
    f = pronta[2]
    if not os.path.exists(f):
        return None

    q = (query or '').replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
    try:
        con = sqlite3.connect('file:%s?mode=ro' % f, uri=True, timeout=3)
        cur = con.execute("SELECT pos FROM basi WHERE nome LIKE ? ESCAPE '\\' "
                          "ORDER BY pos LIMIT ?", ('%' + q + '%', tetto))
        fuori = [r[0] for r in cur.fetchall()]
        con.close()
    except Exception:
        return None
    return [p for p in fuori if 0 <= p < len(brani)]


def _lista_corta_017(self, query, tetto):
    if not query or len(query) < 2:
        return None
    righe = _cerca_nome_017(self, query, tetto)
    if righe is None:
        return None
    brani = self.brani_pc
    return [brani[i] for i in righe]


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

        C._cerca_nome_017 = _cerca_nome_017

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
