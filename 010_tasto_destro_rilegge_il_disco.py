# 010_tasto_destro_rilegge_il_disco.py
#
# IL TASTO DESTRO SUL PREFERITO DEVE RILEGGERE IL DISCO, SUBITO.
#
# Va insieme alla 009, che fa indicizzare i preferiti UNA volta sola e poi
# riusare l'elenco salvato. Senza questa resta un buco: il comando per rileggere
# davvero - tasto destro -> "Aggiorna preferito" - chiama `carica_brani(path)`
# SENZA `forza=True`, quindi riusa l'elenco come il clic normale e non c'e' piu'
# modo di reindicizzare. Nel sorgente e' sistemato, ma aspettare la prossima
# build non va bene: chi aggiunge basi oggi deve vederle oggi.
#
# ⛔ COME NON FARLO (primo tentativo, fallito).
# Quella voce nasce dentro una funzione locale, e il suo comando e' una
# chiusura: in Python normale si possono leggere le variabili che si porta
# dietro (`self` e `path`) da `__closure__`, e ricostruire il comando. Funziona
# in laboratorio, NON nel programma compilato: Nuitka non conserva le chiusure
# in una forma ispezionabile, quindi la patch non trovava niente e lasciava la
# voce com'era. Da qui il "non funziona aggiorna preferito".
#
# ✅ COME FUNZIONA ADESSO. Non si smonta piu' niente: il comando originale si
# ESEGUE, cosi' com'e', e gli si dice soltanto in che modo comportarsi.
#
#   1. si intercetta `carica_brani`: se e' stata chiamata mentre il segnale e'
#      alzato, allora `forza=True`;
#   2. si intercetta la voce di menu "Aggiorna preferito": il suo comando viene
#      avvolto - alza il segnale, chiama l'originale, riabbassa il segnale.
#
# L'originale fa il suo mestiere (imposta il percorso, chiama carica_brani) e la
# chiamata arriva con `forza=True` senza che noi dobbiamo sapere ne' quale sia
# la cartella ne' quale sia l'oggetto libreria. Niente chiusure, niente nomi
# indovinati: funziona compilato come non compilato.
#
# ⚠️ Il segnale e' per THREAD (threading.local): `carica_brani` lancia un thread
# di scansione, e un segnale globale avrebbe rischiato di restare alzato per
# chiamate che non c'entravano.

import threading

import tkinter as tk

_segnale = threading.local()


def _dal_tasto_destro():
    return getattr(_segnale, "acceso", False)


def _aggancia_carica_brani():
    """Se la chiamata arriva dal tasto destro, si rilegge il disco."""
    import moduli.libreria_scan_mixin as L
    C = getattr(L, "LibreriaScanMixin", None)
    if C is None or not hasattr(C, "carica_brani"):
        return False
    if getattr(C, "_ha_forza_dal_menu", False):
        return True

    originale = C.carica_brani

    def carica_brani(self, cartella, *a, **kw):
        if _dal_tasto_destro():
            kw["forza"] = True
        try:
            return originale(self, cartella, *a, **kw)
        except TypeError:
            # versione senza `forza` (patch 009 non applicata): si chiama com'e'
            kw.pop("forza", None)
            return originale(self, cartella, *a, **kw)

    C.carica_brani = carica_brani
    C._ha_forza_dal_menu = True
    return True


def _e_la_voce_giusta(etichetta):
    t = str(etichetta or "").lower()
    return "aggiorna" in t and "preferit" in t


def _aggancia_menu():
    originale = tk.Menu.add_command

    def add_command(self, cnf={}, **kw):
        try:
            etichetta = kw.get("label") or (cnf or {}).get("label") or ""
            comando = kw.get("command") or (cnf or {}).get("command")
            if _e_la_voce_giusta(etichetta) and callable(comando):

                def rileggi(_orig=comando):
                    _segnale.acceso = True
                    try:
                        print("🔄 tasto destro: rileggo il disco")
                        return _orig()
                    finally:
                        _segnale.acceso = False

                if "command" in kw:
                    kw["command"] = rileggi
                else:
                    cnf = dict(cnf or {})
                    cnf["command"] = rileggi

                testo = str(etichetta)
                if "rilegge" not in testo.lower():
                    testo += " (rilegge il disco)"
                    if "label" in kw:
                        kw["label"] = testo
                    else:
                        cnf["label"] = testo
        except Exception:
            pass                 # a qualunque intoppo la voce resta com'era
        return originale(self, cnf, **kw)

    tk.Menu.add_command = add_command


try:
    _aggancia_carica_brani()
    _aggancia_menu()
    print("patch 010: col tasto destro sul preferito si rilegge il disco")
except Exception as _e:
    print("patch 010: %s" % _e)
