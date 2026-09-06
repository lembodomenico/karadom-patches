# 013_contrasto_bottoni_player.py
#
# CONTRASTO SUI BOTTONI DEL PLAYER (play/pausa/stop/skip/loop/pitch/velocita').
#
# Va insieme alla 012 (barre blu notte): con lo sfondo della barra bassa
# diventato blu notte scurissimo (#060c1c), i bottoni neri (#000000) ci si
# mimetizzavano quasi del tutto - nessun contrasto visibile.
#
# --------------------------------------------------------------------------
# COSA NON FUNZIONA, e perche' questa patch e' stata riscritta
# --------------------------------------------------------------------------
# Primo tentativo: colorare lo sfondo dei bottoni di un blu piu' chiaro.
# Scartato: i bottoni mostrano icone PNG con margini trasparenti diversi fra
# loro, quindi il colore "traspariva" in modo incoerente - si vedeva bene sui
# primi tre bottoni e quasi per niente sugli altri.
#
# Secondo tentativo: bordo via highlightthickness + highlightbackground.
# Funziona su Linux, ma su WINDOWS Tk NON disegna affatto quelle opzioni sui
# Button: provato a 1, 2 e 3 pixel, sullo schermo non cambiava niente. Questa
# patch, nella sua prima stesura, faceva esattamente questo: sarebbe arrivata
# ai clienti senza produrre alcun effetto visibile.
#
# --------------------------------------------------------------------------
# COME FUNZIONA ORA
# --------------------------------------------------------------------------
# Il bordo e' un Frame colorato messo DIETRO al bottone, che sporge di 1 pixel
# su ogni lato: puro layout, quindi si vede identico su Windows e su Linux e
# non dipende da come Tk disegna i bordi.
#
# Il Frame va creato PRIMA del bottone, perche' in Tk un widget non si puo'
# spostare sotto un altro genitore dopo essere stato creato. Per questo si
# interviene su tk.Button.__init__: quando nasce un bottone con bg='#000000'
# (e' il colore ESATTO, e solo quello, usato dai bottoni del player in ui.py:
# play/pausa/stop/skip/loop/pitch-/pitch+/velocita-/velocita+) gli si crea
# attorno il Frame e lo si mette dentro. pack/grid/place/pack_forget del
# bottone vengono dirottati sul Frame, cosi' tutto il resto di create_ui()
# continua a posizionare il bottone come prima, senza saperne niente.

import tkinter as tk

_BORDO = '#5b78c4'      # blu, la variante scelta
_SPESSORE = 1           # pixel di bordo su ogni lato

_ORIG_INIT = tk.Button.__init__
_ORIG_PACK = tk.Button.pack


def _button_init_bordo(self, master=None, **kw):
    metti_bordo = False
    try:
        if str(kw.get('bg', '')).lower() == '#000000':
            metti_bordo = True
            # Se il genitore E' GIA' un Frame del colore del bordo, vuol dire
            # che il bordo c'e' gia' (versione del sorgente che lo fa da se',
            # oppure patch applicata due volte): un secondo Frame darebbe un
            # bordo doppio e piu' spesso.
            try:
                if isinstance(master, tk.Frame) and str(master.cget('bg')).lower() == _BORDO:
                    metti_bordo = False
            except Exception:
                pass
    except Exception:
        metti_bordo = False

    if not metti_bordo:
        _ORIG_INIT(self, master, **kw)
        return

    try:
        holder = tk.Frame(master, bg=_BORDO)
        _ORIG_INIT(self, holder, **kw)
        _ORIG_PACK(self, padx=_SPESSORE, pady=_SPESSORE)
        # chi posiziona il bottone in realta' posiziona il Frame che lo contiene
        self.pack = holder.pack
        self.pack_forget = holder.pack_forget
        self.grid = holder.grid
        self.grid_forget = holder.grid_forget
        self.place = holder.place
        self.place_forget = holder.place_forget
        self._bordo_holder = holder
    except Exception:
        # qualunque imprevisto: bottone normale, senza bordo. Meglio un bottone
        # senza contrasto che una schermata che non si apre.
        try:
            _ORIG_INIT(self, master, **kw)
        except Exception:
            pass


tk.Button.__init__ = _button_init_bordo

print("patch 013: bordo di contrasto sui bottoni del player (Frame, visibile anche su Windows)")
