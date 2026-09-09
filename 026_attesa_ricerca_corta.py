# 026 - il filtro in alto risponde subito, come i campi delle righe.

ATTESA_CON_TABELLA = 200      # gli stessi millisecondi dei campi nelle righe


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_026', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def _attesa_scelta(self):
    """Quanto si aspetta dopo l'ultimo tasto, prima di cercare.

    ⚠️ Sopra i 100.000 brani si aspettavano 900 ms. Li aveva messi la 014
    quando a cercare era un ciclo su 400.000 nomi: farlo partire tardi era
    l'unico modo per non far calare i BPM. Da quando cerca la TABELLA (016)
    quel ritardo non protegge piu' niente, si sente e basta: il campo in alto
    sembrava lento mentre i campi delle righe, che aspettano 200 ms,
    rispondevano subito.

    Se la tabella non c'e' - archivio piccolo, o non ancora pronta - si
    lasciano i valori di prima: li' il ciclo c'e' ancora e il ritardo serve.
    """
    valori = getattr(self, '_attese_ricerca', None)
    if valori is None:
        return None                      # non ancora deciso: non si tocca
    lunga, corta, soglia = valori
    if getattr(self, '_tabella016', None) is None:
        return None                      # niente tabella: si resta com'era
    if lunga <= ATTESA_CON_TABELLA:
        return None                      # gia' corta (l'ha messa l'utente)
    return (ATTESA_CON_TABELLA, corta, soglia)


def apply():
    if _spenta():
        return False
    try:
        import moduli.libreria_search_mixin as S
        C = getattr(S, "LibreriaSearchMixin", None)
        if C is None or not hasattr(C, "_debounce_suggerimenti"):
            return False
        if hasattr(C, "_orig_026"):
            return True
        C._orig_026 = C._debounce_suggerimenti

        def _debounce_suggerimenti(self, event=None, _orig=C._orig_026):
            # Si cambia solo il numero che l'originale legge, e poi si lascia
            # fare tutto a lui: niente della sua logica viene riscritto.
            try:
                nuovo = _attesa_scelta(self)
                if nuovo is not None:
                    self._attese_ricerca = nuovo
                    print("patch 026: attesa della ricerca %d ms "
                          "(la tabella c'e', i 900 ms non servono piu')"
                          % nuovo[0])
            except Exception:
                pass
            return _orig(self, event)

        C._debounce_suggerimenti = _debounce_suggerimenti
        return True
    except Exception:
        return False


def revert():
    try:
        import moduli.libreria_search_mixin as S
        C = S.LibreriaSearchMixin
        if hasattr(C, "_orig_026"):
            C._debounce_suggerimenti = C._orig_026
            del C._orig_026
            return True
    except Exception:
        pass
    return False


try:
    apply()
except Exception:
    pass
