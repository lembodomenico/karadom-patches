# 014_ricerca_per_tipo_e_barra_linux.py
#
# Due cose, tutte e due provate sul notebook Linux:
#
#   1) I SUGGERIMENTI DELLA RICERCA ESCONO PER TIPO: prima gli mp3, sotto i
#      video (mp4), poi i midi.
#   2) SU LINUX SPARISCE LA BARRA TITOLO DISEGNATA DENTRO L'APPLICAZIONE
#      (logo + edizione + versione), diventata un doppione.
#
# --------------------------------------------------------------------------
# 1. ORDINE DEI SUGGERIMENTI
# --------------------------------------------------------------------------
# Prima i risultati dei tre archivi si INTERLACCIAVANO: uno per archivio a
# giro. Una ricerca dava quindi mp3, video e midi mescolati, mentre chi cerca
# una base da cantare vuole per prima cosa gli mp3.
#
# Attenzione pero': con il solo ordine, gli mp3 (oltre 14.000 in archivio)
# riempiono da soli tutto il limite e video e midi NON si vedrebbero MAI.
# Misurato prima di scrivere questa patch: cercando "amore", 200 risultati su
# 200 erano mp3. Per questo a ogni tipo che ha qualcosa da mostrare si tiene
# da parte una fetta piccola, e tutto il resto va agli mp3. Sul notebook, con
# il limite del suggeritore (60):
#
#     amore    mp3 x46   poi  video x7   poi  midi x7
#     vasco    mp3 x46   poi  video x7   poi  midi x7
#     volare   mp3 x28   poi  midi x16          <- niente video: lo spazio
#                                                  avanzato va agli altri
#
# La funzione originale non viene riscritta: la si chiama con un limite piu'
# largo (serve pescare abbastanza mp3) e se ne riordina il risultato.
#
# --------------------------------------------------------------------------
# 2. BARRA TITOLO SU LINUX
# --------------------------------------------------------------------------
# Su Linux la finestra non ha la decorazione del sistema, quindi ui.py
# disegnava una propria barra con logo ed edizione/versione. Adesso quelle tre
# cose stanno nella barra di sistema in cima allo schermo (tint2), e la barra
# Tk faceva un doppione una riga sotto l'altra, rubando anche sc(26) pixel di
# altezza all'applicazione.
#
# Non si puo' "togliere" codice da una funzione gia' scritta: si intercetta la
# nascita della Label con quel testo e si toglie dal layout il Frame che la
# contiene (pack_forget). Il Frame resta vivo, semplicemente non occupa piu'
# spazio: niente da riscrivere in create_ui.
#
# Su WINDOWS non cambia nulla: li' quella barra non viene proprio creata (il
# blocco e' dentro un "if sys.platform.startswith('linux')") ed e' il sistema
# a disegnare la titlebar.

import sys

# ==========================================================================
# 1. ORDINE DEI SUGGERIMENTI: mp3, poi video (mp4), poi midi
# ==========================================================================

ORDINE_FONTI = ('mp3', 'video', 'midi')


def _riordina_per_tipo(risultati, limite):
    """Rimette i risultati in ordine di tipo, lasciando a ciascuno la sua
    fetta perche' nessuno resti fuori."""
    per_fonte = {}
    for v in risultati:
        per_fonte.setdefault(v.get('_fonte', ''), []).append(v)
    if len(per_fonte) <= 1:
        return risultati[:limite]

    chiavi = [c for c in ORDINE_FONTI if c in per_fonte]
    chiavi += [c for c in per_fonte if c not in ORDINE_FONTI]

    quota_minima = max(1, limite // 8)
    riservati = quota_minima * max(0, len(chiavi) - 1)

    finali = []
    for posto, chiave in enumerate(chiavi):
        spazio = max(quota_minima, limite - riservati) if posto == 0 else quota_minima
        finali.extend(per_fonte[chiave][:spazio])

    # lo spazio avanzato da chi aveva pochi risultati non si butta
    if len(finali) < limite:
        gia = set(id(v) for v in finali)
        for chiave in chiavi:
            for v in per_fonte[chiave]:
                if id(v) not in gia:
                    finali.append(v)
                    if len(finali) >= limite:
                        break
            if len(finali) >= limite:
                break
    return finali[:limite]


try:
    from moduli import carica_basi

    if not getattr(carica_basi, '_ordine_per_tipo_attivo', False):
        _cerca_originale = carica_basi.cerca_nei_db

        def _cerca_ordinata(query, limite=200):
            # si chiede piu' del necessario: la funzione originale interlaccia
            # e taglia, quindi con il solo 'limite' non arriverebbero abbastanza
            # mp3 per riempire la loro fetta
            largo = min(400, max(limite * 4, limite))
            try:
                grezzi = _cerca_originale(query, limite=largo)
            except TypeError:          # firma diversa in versioni piu' vecchie
                grezzi = _cerca_originale(query)
            return _riordina_per_tipo(grezzi, limite)

        _cerca_ordinata.__doc__ = _cerca_originale.__doc__
        carica_basi.cerca_nei_db = _cerca_ordinata
        carica_basi.ORDINE_FONTI = ORDINE_FONTI
        carica_basi._ordine_per_tipo_attivo = True

        # il suggeritore importa la funzione DENTRO la funzione che la usa
        # ("from .carica_basi import cerca_nei_db"), quindi rimpiazzare il
        # nome nel modulo basta: non ne resta una copia da un'altra parte
        print("🔎 Ricerca: prima gli mp3, poi i video, poi i midi")
except Exception as _e:
    print("⚠️ patch 014, ordine ricerca non applicato: %s" % _e)


# ==========================================================================
# 2. VIA LA BARRA TITOLO DUPLICATA (solo Linux)
# ==========================================================================

if sys.platform.startswith('linux'):
    try:
        import tkinter as tk

        if not getattr(tk.Label, '_barra_titolo_tolta', False):
            _label_init = tk.Label.__init__

            def _label_init_senza_titlebar(self, master=None, **kw):
                _label_init(self, master, **kw)
                try:
                    testo = str(kw.get('text', ''))
                    # la riga e' esattamente "KaraDom <edizione> <versione>",
                    # con la versione che comincia per cifra: cosi' non si
                    # rischia di cancellare un'altra scritta che nomina KaraDom
                    if testo.startswith('KaraDom '):
                        pezzi = testo.split()
                        if len(pezzi) == 3 and pezzi[2][:1].isdigit():
                            if master is not None:
                                master.pack_forget()
                except Exception:
                    pass

            tk.Label.__init__ = _label_init_senza_titlebar
            tk.Label._barra_titolo_tolta = True
            print("🪧 Barra titolo: la disegna la barra di sistema, non l'app")
    except Exception as _e:
        print("⚠️ patch 014, barra titolo non tolta: %s" % _e)
