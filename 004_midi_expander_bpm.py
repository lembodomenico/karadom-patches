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
# COSA FA QUESTA PATCH: una cosa sola, e non tocca in nessun modo il tempo della
# musica. Ogni riproduzione riceve il suo segnale di stop, cosi' il thread di
# quella precedente muore anche se era rimasto bloccato.

import threading

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
        return play_originale(self, *a, **k)

    P.play = play
    P._ha_stop_pulito = True

    print("patch 004: ogni riproduzione ha il suo stop, niente thread zombie")
    return True


try:
    _applica()
except Exception as _e:
    print("patch 004: %s" % _e)
