# 017_ricerca_scaletta_da_tabella.py
#
# ANCHE LA RICERCA DELLA SCALETTA LA FA IL DATABASE.
#
# La 016 ha tolto il ciclo Python dalla tendina dei suggerimenti (quella che
# si apre mentre si scrive). Ma la stessa scansione su 400.000 brani era
# rimasta in ALTRI DUE punti, e questi due girano nel THREAD DELL'INTERFACCIA,
# non in un thread a parte: mentre cercano, il programma e' fermo e il MIDI
# perde i tempi.
#
#   riga aggiunta in scaletta, INVIO nel campo filtro
#     -> mostra_popup_suggerimenti()   ... 200 risultati
#   pulsante "cerca nel PC"
#     -> mostra_risultati_ricerca()    ... 100 risultati
#
# Tutte e due fanno la stessa identica cosa:
#     [b for b in self.brani_pc if query in b['nome_lower']][:N]
#
# QUI NON SI RISCRIVE LA FUNZIONE. La finestra che quelle due costruiscono e'
# lunga e piena di roba (tema, icone, doppio clic, tasto destro): ricopiarla
# in una patch vuol dire portarsi dietro venti nomi che nel compilato
# potrebbero non esserci — la lezione della 015, che moriva di NameError al
# primo tasto. Si fa invece il giro corto:
#
#     1. la tabella della 016 dice QUALI brani contengono la parola cercata
#        (SELECT ... WHERE nome LIKE '%parola%'), e mentre lavora molla il
#        turno, quindi il MIDI continua a suonare;
#     2. per il tempo di quella sola chiamata, self.brani_pc e' la lista
#        CORTA dei brani trovati;
#     3. si chiama la funzione ORIGINALE, che rifa' il suo ciclo — ma su
#        duecento brani invece che su quattrocentomila — e costruisce la
#        finestra esattamente come sempre;
#     4. si rimette la lista intera (in `finally`: anche se qualcosa esplode).
#
# Il risultato e' IDENTICO a prima, riga per riga: la ricerca nella tabella e'
# la stessa condizione ("il nome contiene questo pezzo"), l'ordine e' quello
# della lista, e il taglio a 100/200 lo fa sempre l'originale. Cambia solo
# CHI scorre i quattrocentomila nomi: SQLite invece di Python.
#
# ⚠️ SERVE LA 016: la tabella la costruisce quella. Se la 016 non c'e' o non
#    e' attiva, questa non fa niente e si resta come oggi (nessun rischio).
#    Di conseguenza vale anche qui il "solo oltre i 100.000 brani": sotto
#    quella soglia la tabella non viene nemmeno creata.
#
# ⚠️ Il % e l'_ digitati dall'utente vengono protetti (in SQL vogliono dire
#    "qualsiasi cosa" e "un carattere qualsiasi"): senza, chi cerca
#    "AC_DC" si vedrebbe arrivare anche "AC/DC" e "AC DC".
#
# SE NON VA BENE: `R17` la ritira, `patch_017 = 0` la spegne su una macchina
# sola, `revert()` rimette gli originali a caldo.


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_017', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def _cerca_nome_017(self, query, tetto):
    """Le posizioni dei brani il cui nome contiene `query`, in ordine di lista.

    None vuol dire "non si puo' rispondere dalla tabella" (non c'e', e'
    vecchia, o e' di un'altra cartella): chi chiama fa come sempre.
    """
    import os
    import sqlite3
    pronta = getattr(self, '_tabella016', None)
    brani = getattr(self, 'brani_pc', None) or ()
    # la tabella deve essere di QUESTA lista, non di quella di prima
    if not pronta or pronta[0] is not brani or pronta[1] != len(brani):
        return None
    f = pronta[2]
    if not os.path.exists(f):
        return None

    # in LIKE il % e l'_ sono jolly: quelli scritti dall'utente vanno protetti
    q = (query or '').replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
    try:
        con = sqlite3.connect('file:%s?mode=ro' % f, uri=True, timeout=3)
        cur = con.execute("SELECT pos FROM basi WHERE nome LIKE ? ESCAPE '\\' "
                          "ORDER BY pos LIMIT ?", ('%' + q + '%', tetto))
        fuori = [r[0] for r in cur.fetchall()]
        con.close()
    except Exception as e:
        print("patch 017: ricerca nella tabella fallita (%s)" % e)
        return None
    return [p for p in fuori if 0 <= p < len(brani)]


def _lista_corta_017(self, query, tetto):
    """La lista dei soli brani che contengono `query`. None = fai come sempre."""
    if not query or len(query) < 2:
        return None
    righe = _cerca_nome_017(self, query, tetto)
    if righe is None:
        return None
    brani = self.brani_pc
    return [brani[i] for i in righe]


def _con_lista_corta(self, corta, chiamata):
    """Esegue `chiamata` facendo vedere alla funzione originale la lista corta.

    ⚠️ La lista si rimette SEMPRE, anche se la funzione dentro solleva: e'
    per questo che c'e' il `finally`. Se restasse quella corta, il programma
    da li' in poi vedrebbe duecento basi invece di quattrocentomila.
    """
    pieni = self.brani_pc
    self.brani_pc = corta
    try:
        return chiamata()
    finally:
        self.brani_pc = pieni


def apply():
    if _spenta():
        print("patch 017: spenta dalla configurazione (patch_017 = 0)")
        return False
    try:
        import moduli.libreria_search_mixin as S
        C = getattr(S, "LibreriaSearchMixin", None)
        if C is None:
            print("patch 017: LibreriaSearchMixin non trovato, salto")
            return False
        if not hasattr(C, "_cerca_in_tabella_016"):
            print("patch 017: serve la 016 (la tabella la costruisce quella), salto")
            return False

        C._cerca_nome_017 = _cerca_nome_017

        # --- INVIO nel campo filtro: la finestra dei risultati ---
        if hasattr(C, "mostra_popup_suggerimenti") and not hasattr(C, "_orig_017_popup"):
            C._orig_017_popup = C.mostra_popup_suggerimenti

            def mostra_popup_suggerimenti(self, query, _orig=C._orig_017_popup):
                corta = None
                try:
                    corta = _lista_corta_017(self, query, 200)
                except Exception as e:
                    print("patch 017: %s" % e)
                if corta is None:
                    return _orig(self, query)
                return _con_lista_corta(self, corta, lambda: _orig(self, query))

            C.mostra_popup_suggerimenti = mostra_popup_suggerimenti

        # --- il pulsante "cerca nel PC" ---
        if hasattr(C, "mostra_risultati_ricerca") and not hasattr(C, "_orig_017_ricerca"):
            C._orig_017_ricerca = C.mostra_risultati_ricerca

            def mostra_risultati_ricerca(self, _orig=C._orig_017_ricerca):
                corta = None
                try:
                    # l'originale legge il campo cosi': .get().lower(), senza
                    # togliere gli spazi. Qui si fa uguale, o si cercherebbe
                    # una cosa diversa da quella che poi lui filtra.
                    corta = _lista_corta_017(self, self.entry_filtro.get().lower(), 100)
                except Exception as e:
                    print("patch 017: %s" % e)
                if corta is None:
                    return _orig(self)
                return _con_lista_corta(self, corta, lambda: _orig(self))

            C.mostra_risultati_ricerca = mostra_risultati_ricerca

        print("patch 017: anche la ricerca della scaletta passa dal database")
        return True
    except Exception as e:
        print("patch 017: %s" % e)
        return False


def revert():
    try:
        import moduli.libreria_search_mixin as S
        C = S.LibreriaSearchMixin
        rimessi = []
        if hasattr(C, "_orig_017_popup"):
            C.mostra_popup_suggerimenti = C._orig_017_popup
            del C._orig_017_popup
            rimessi.append('popup suggerimenti')
        if hasattr(C, "_orig_017_ricerca"):
            C.mostra_risultati_ricerca = C._orig_017_ricerca
            del C._orig_017_ricerca
            rimessi.append('cerca nel PC')
        if rimessi:
            print("patch 017: rimessi gli originali (%s)" % ', '.join(rimessi))
            return True
    except Exception as e:
        print("revert 017: %s" % e)
    return False


try:
    apply()
except Exception as _e:
    print("patch 017: %s" % _e)
