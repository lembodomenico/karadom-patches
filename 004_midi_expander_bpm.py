# 004_midi_expander_bpm.py
#
# IL MIDI CON L'EXPANDER RALLENTAVA MENTRE SI SCRIVE NELLA RICERCA.
# Segnalato il 3 settembre 2026: "quando sta riproducendo dei MIDI con
# l'expander, se si scrive dentro i campi ricerca la riproduzione rallenta
# molto abbassando i BPM".
#
# PERCHE'. Con l'expander ogni nota non va a un synth dentro il programma: esce
# da una porta MIDI di sistema. A ogni uscita il thread della riproduzione molla
# il turno agli altri, e per riprenderlo aspetta fino a CINQUE MILLESIMI di
# secondo (il valore di serie di Python) - moltiplicati per ogni nota
# dell'accordo. Misurato su questo PC, con qualcuno che lavora (la ricerca che
# filtra la libreria a ogni tasto):
#
#     turno 5 ms (com'era) -> un giro da 8 note ritarda 40 ms, con punte oltre 50
#     turno 0,5 ms         -> lo stesso giro ritarda 0,66 ms
#
# I 50 ms sono la soglia oltre la quale il motore taglia il ritardo e quel tempo
# di musica va perso per sempre: da li' il calo dei BPM (120 misurati a 109-117).
#
# ⛔ PROVATO E TOLTO: accorciare il turno fra i thread (setswitchinterval a
# mezzo millesimo) migliorava la misura ma sul campo PEGGIORAVA - con 35 thread
# nel processo, cambiare turno di continuo costa piu' di quanto rende. Stessa
# sorte per il recupero del tempo perso: dentro il ciclo di riproduzione
# rimandava un centinaio di messaggi e poteva innescare altri blocchi.
#
# QUELLO CHE RESTA, e che spiega perche' RIAVVIANDO IL PROGRAMMA
# il rallentamento sparisce: cambiando brano, `play()` fa `stop()` - che aspetta
# il thread precedente **solo un secondo** - e subito dopo azzera il segnale di
# stop. Se quel thread era bloccato (con l'expander succede: le scritture sulla
# porta passano da un lock), il segnale che doveva ancora vedere non c'e' piu':
# resta vivo PER SEMPRE, a rubare turni e a contendere la porta MIDI. Ogni brano
# ne puo' lasciare uno, e il programma peggiora man mano che lo si usa.
# Provato: cambiando brano mentre il primo e' occupato restano vivi tutti e due;
# con la correzione (un evento di stop NUOVO a ogni riproduzione, cosi' il
# vecchio thread tiene il suo, gia' segnato, e muore) resta solo quello giusto.
#
# COSA FA QUESTA PATCH. Due cose, e nessuna delle due tocca il tempo della musica:
#
# 1) LA CORREZIONE: ogni riproduzione riceve il suo segnale di stop, cosi' il
#    thread di quella precedente muore anche se era rimasto bloccato.
#
# 2) LA SPIA: mentre suona, un controllo misura ogni due secondi QUANTO AVANZA
#    LA MUSICA rispetto a quanto avanza l'orologio. Se il brano perde tempo il
#    rapporto scende sotto 1 - ed e' esattamente il calo dei BPM, misurato
#    invece che sentito a orecchio. Scrive in log/karadom_debug.log, quindi
#    SOLO quando il programma e' avviato in modalita' debug (Extra > Riavvia
#    con debug); ad avvio normale non parte nemmeno e non costa niente.
#    Il cliente poi manda il log con Extra > Invia log a supporto.

import threading
import time

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
                dbg("MIDI-TIMING",
                    "la musica sta andando al %.0f%% del dovuto "
                    "(in %.1f s reali ne ha suonati %.1f) - expander=%s, "
                    "thread vivi=%d" % (
                        rapporto * 100, reale / 1000.0, musica / 1000.0,
                        "si" if getattr(player, "is_expander", False) else "no",
                        threading.active_count()))
        if peggio < 1.0:
            dbg("MIDI-TIMING",
                "RIEPILOGO brano: durata %.0f s, il peggio e' stato %.0f%%, "
                "musica persa in tutto %.0f ms" % (
                    time.perf_counter() - inizio, peggio * 100, persi))
    except Exception:
        pass


def _applica():
    import moduli.fluidsynth_player as fp

    P = getattr(fp, "FluidSynthPlayer", None)
    if P is None or not hasattr(P, "play"):
        print("patch 004: motore MIDI diverso, salto")
        return False
    if getattr(P, "_ha_stop_pulito", False):
        return True

    play_originale = P.play

    def play(self, *a, **k):
        # gli argomenti si inoltrano cosi' come sono: se una versione del
        # programma ne avesse di piu', la patch non deve rompere la riproduzione
        # il thread della riproduzione precedente non deve poter sopravvivere:
        # gli si lascia il suo evento di stop (gia' segnato) e se ne prepara uno
        # nuovo per questa riproduzione
        try:
            self.stop()
            self._stop_event = threading.Event()
            self._playback_thread = None
        except Exception:
            pass
        esito = play_originale(self, *a, **k)
        dbg = _log()
        if dbg is not None:
            threading.Thread(target=_sorveglia, args=(self, dbg), daemon=True).start()
        return esito

    P.play = play
    P._ha_stop_pulito = True

    print("patch 004: ogni riproduzione ha il suo stop; in modalita' debug "
          "la spia misura se la musica resta indietro")
    return True


try:
    _applica()
except Exception as _e:
    print("patch 004: %s" % _e)
