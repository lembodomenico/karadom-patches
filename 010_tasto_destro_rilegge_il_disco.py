# 010_tasto_destro_rilegge_il_disco.py
#
# IL TASTO DESTRO SUL PREFERITO DEVE RILEGGERE IL DISCO, SUBITO.
#
# Va insieme alla 009, che fa indicizzare i preferiti UNA volta sola e poi
# riusare l'elenco salvato. Con quella da sola restava un buco: il comando per
# rileggere davvero - il tasto destro -> "Aggiorna preferito" - chiama
# `carica_brani(path)` SENZA `forza=True`, quindi riusava l'elenco come il clic
# normale e non c'era piu' modo di reindicizzare.
#
# Nel sorgente e' gia' sistemato, ma aspettare la prossima build non va bene:
# chi aggiunge basi oggi deve poterle vedere oggi.
#
# COME CI SI ARRIVA. Quella voce di menu nasce dentro una funzione locale
# (`_on_tree_right_click` in libreria_uibuilder_mixin) e la sua variabile non
# esiste da nessuna parte a cui una patch possa arrivare. Ma il comando della
# voce e' una CHIUSURA, e una chiusura si porta dentro le variabili che usa:
# `self` (la libreria) e `path` (la cartella). Si leggono da
# `funzione.__closure__`, accoppiandole ai nomi in `__code__.co_freevars`.
#
# Quindi: si intercetta `Menu.add_command`, e quando passa la voce "Aggiorna
# preferito" le si sostituisce il comando con uno che fa la stessa cosa ma con
# `forza=True`. Nient'altro cambia: stesso menu, stessa voce, stesso posto.
#
# ⚠️ L'intercettazione NON si spegne dopo il primo uso, a differenza della 007:
# quel menu viene ricostruito a ogni clic destro, quindi la sostituzione serve
# ogni volta. Costa un confronto di stringhe per voce di menu: nulla.
#
# ⚠️ Se un domani la voce venisse rinominata o il comando smettesse di essere
# una chiusura con quei nomi, la patch non trova niente e lascia tutto com'e':
# si torna al comportamento di prima, non si rompe niente.

import tkinter as tk


def _dentro(funzione):
    """Le variabili che una funzione si porta dietro, per nome."""
    try:
        nomi = funzione.__code__.co_freevars
        celle = funzione.__closure__ or ()
        return {n: c.cell_contents for n, c in zip(nomi, celle)}
    except Exception:
        return {}


def _e_la_voce_giusta(etichetta):
    t = str(etichetta or "").lower()
    return "aggiorna" in t and "preferit" in t


def _aggancia():
    originale = tk.Menu.add_command

    def add_command(self, cnf={}, **kw):
        try:
            etichetta = kw.get("label") or (cnf or {}).get("label") or ""
            comando = kw.get("command") or (cnf or {}).get("command")
            if _e_la_voce_giusta(etichetta) and callable(comando):
                dati = _dentro(comando)
                lib, path = dati.get("self"), dati.get("path")
                if lib is not None and path and hasattr(lib, "carica_brani"):
                    def rileggi(_lib=lib, _path=path):
                        try:
                            _lib.percorso_attivo = _path
                        except Exception:
                            pass
                        print("🔄 rileggo il disco per: %s" % _path)
                        _lib.carica_brani(_path, forza=True)

                    if "command" in kw:
                        kw["command"] = rileggi
                    else:
                        cnf = dict(cnf or {})
                        cnf["command"] = rileggi
                    # si dice anche nell'etichetta, cosi' e' chiaro cosa fa
                    testo = str(etichetta)
                    if "rilegge" not in testo.lower():
                        testo = testo + " (rilegge il disco)"
                        if "label" in kw:
                            kw["label"] = testo
                        else:
                            cnf["label"] = testo
        except Exception:
            pass                     # qualunque intoppo: la voce resta com'era
        return originale(self, cnf, **kw)

    tk.Menu.add_command = add_command


try:
    _aggancia()
    print("patch 010: col tasto destro sul preferito si rilegge il disco")
except Exception as _e:
    print("patch 010: %s" % _e)
