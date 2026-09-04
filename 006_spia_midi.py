# 006_spia_midi.py
#
# SOLO UNA SPIA: misura se il MIDI resta indietro. NON tocca la riproduzione.
#
# A cosa serve. Con l'expander la musica rallenta, ma "rallenta" a orecchio non
# si puo' discutere: serve un numero. Questa patch non corregge niente - guarda
# da fuori quanto avanza il brano e lo scrive nel log:
#
#     [MIDI-TIMING] la musica sta andando al 85% del dovuto
#                   (in 2.0 s reali ne ha suonati 1.7) - expander=si, thread vivi=9
#     [MIDI-TIMING] RIEPILOGO brano: il peggio e' stato 52%, persi 5.248 ms
#
# Perche' sta da sola. Prima viveva dentro la 004 insieme a correzioni vere, e
# per provare KaraDom "senza le mie modifiche" bisognava togliere anche il
# riavvio in debug e le dipendenze di YouTube, che non c'entrano niente. Cosi'
# invece si accende e si spegne da sola, e un test "con o senza" resta pulito.
#
# Cosa fa esattamente:
#   - avvolge play() per far partire un thread di sola lettura;
#   - quel thread, ogni due secondi, chiede al player la posizione del brano e
#     la confronta col tempo reale trascorso;
#   - scrive una riga SOLO quando si perde tempo (sotto il 97%): se la musica
#     va liscia il log resta pulito.
#
# Scrive in log/karadom_debug.log, quindi SOLO in modalita' debug
# (Extra > Riavvia con debug). Ad avvio normale non parte nemmeno e non costa
# niente: `_log()` torna None e il thread non viene creato.
#
# ⚠️ Il costo della spia stessa: un thread che dorme due secondi e legge un
# numero. `get_position_ms` fa una somma sulla tempo map, niente lock sul
# motore. Non e' lei a far rallentare la musica - ma se un giorno il dubbio
# venisse, basta togliere questa patch e riprovare, che e' esattamente il
# motivo per cui adesso sta da sola.

import threading
import time
import os

def _log():
    """La funzione di log di KaraDom, se il programma gira in modalita' debug."""
    try:
        from moduli.debug_logger import DEBUG, dbg
        return dbg if DEBUG else None
    except Exception:
        return None


def _sorveglia(player, dbg):
    """Confronta l'avanzamento della MUSICA con quello dell'OROLOGIO.

    Non entra nel motore: legge la posizione del brano da fuori, ogni due
    secondi. Se in due secondi reali la musica ne fa 1,8 vuol dire che il brano
    sta andando al 90% - cioe' 120 BPM che diventano 108. E' la misura del
    sintomo, non di una causa ipotizzata."""
    try:
        leggi = player.get_position_ms
    except Exception:
        return
    peggio = 1.0
    persi = 0.0
    righe = []      # si scrive tutto DOPO, non mentre suona
    try:
        pos0, t0 = leggi(), time.perf_counter()
        inizio = t0
        while getattr(player, "is_playing", False):
            time.sleep(2.0)
            if not getattr(player, "is_playing", False):
                break          # brano finito o fermato: l'ultima finestra e' monca
                               # e darebbe un falso allarme (misurato: 48%)
            pos1, t1 = leggi(), time.perf_counter()
            reale = (t1 - t0) * 1000.0
            musica = pos1 - pos0
            pos0, t0 = pos1, t1
            if reale < 100 or musica < 0:      # cambio brano o salto: si riparte
                continue
            velocita = float(getattr(player, "_speed", 1.0) or 1.0)
            rapporto = musica / (reale * velocita)
            if rapporto < 0.97:                 # sotto il 97% si sente
                persi += reale * velocita - musica
                if rapporto < peggio:
                    peggio = rapporto
                # ⚠️ NON si scrive nel log adesso: scrivere su file mentre la
                #    musica suona significa fare I/O proprio nei momenti in cui
                #    il thread sta gia' faticando, e la misura disturberebbe
                #    cio' che deve misurare. Si tiene tutto in memoria (una
                #    tupla per finestra, poche decine per brano) e si scrive
                #    quando il brano e' finito.
                righe.append((rapporto, reale, musica,
                              getattr(player, "is_expander", False),
                              threading.active_count()))
        for _r, _re, _mu, _exp, _th in righe:
            dbg("MIDI-TIMING",
                "la musica e' andata al %.0f%% del dovuto "
                "(in %.1f s reali ne ha suonati %.1f) - expander=%s, "
                "thread vivi=%d" % (_r * 100, _re / 1000.0, _mu / 1000.0,
                                    "si" if _exp else "no", _th))
        if peggio < 1.0:
            dbg("MIDI-TIMING",
                "RIEPILOGO brano: durata %.0f s, il peggio e' stato %.0f%%, "
                "musica persa in tutto %.0f ms" % (
                    time.perf_counter() - inizio, peggio * 100, persi))
    except Exception:
        pass


def _accendi():
    """Fa partire la spia a ogni riproduzione. Il motore NON si tocca."""
    import moduli.fluidsynth_player as fp

    P = getattr(fp, "FluidSynthPlayer", None)
    if P is None or not hasattr(P, "play"):
        print("patch 006: motore MIDI diverso, salto la spia")
        return False
    if getattr(P, "_ha_spia", False):
        return True

    play_originale = P.play

    def play(self, *a, **k):
        esito = play_originale(self, *a, **k)      # nessuna modifica al motore
        dbg = _log()
        if dbg is not None:
            threading.Thread(target=_sorveglia, args=(self, dbg), daemon=True).start()
        return esito

    P.play = play
    P._ha_spia = True
    print("patch 006: spia del timing MIDI attiva (solo in modalita' debug)")
    return True


try:
    _accendi()
except Exception as _e:
    print("patch 006 (spia): %s" % _e)
