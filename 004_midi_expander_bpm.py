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
# COSA FA QUESTA PATCH. Mentre suona un MIDI SULL'EXPANDER, accorcia il turno fra
# i thread a mezzo millesimo, e lo rimette com'era appena la riproduzione
# finisce. Non tocca niente quando si suona col SoundFont interno.
#
# ⚠️ La seconda meta' della correzione - il tempo perso che invece di sparire
# viene recuperato - sta nel motore di riproduzione, troppo lungo da riscrivere
# a caldo: arriva con la prossima compilazione. Con questa patch, comunque, il
# ritardo non arriva quasi mai alla soglia dove il tempo si perde.

import sys
import threading
import time

TURNO_CORTO = 0.0005


def _applica():
    import moduli.fluidsynth_player as fp

    P = getattr(fp, "FluidSynthPlayer", None)
    if P is None or not hasattr(P, "play"):
        print("patch 004: motore MIDI diverso, salto")
        return False
    if getattr(P, "_ha_turno_corto", False):
        return True

    play_originale = P.play
    stop_originale = getattr(P, "stop", None)
    stato = {"prima": None}

    def _accorcia():
        if stato["prima"] is None:
            try:
                stato["prima"] = sys.getswitchinterval()
                sys.setswitchinterval(TURNO_CORTO)
            except Exception:
                stato["prima"] = None

    def _rimetti():
        if stato["prima"] is not None:
            try:
                sys.setswitchinterval(stato["prima"])
            except Exception:
                pass
            stato["prima"] = None

    def _guardia(player):
        """Se la riproduzione finisce da sola (fine del brano), nessuno chiama
        stop(): il turno lo rimette a posto questo controllo."""
        while True:
            time.sleep(2.0)
            try:
                if not getattr(player, "is_playing", False):
                    _rimetti()
                    return
            except Exception:
                _rimetti()
                return

    def play(self, start_tick=0):
        if getattr(self, "is_expander", False):
            _accorcia()
            threading.Thread(target=_guardia, args=(self,), daemon=True).start()
        return play_originale(self, start_tick)

    P.play = play

    if callable(stop_originale):
        def stop(self, *a, **k):
            try:
                return stop_originale(self, *a, **k)
            finally:
                _rimetti()
        P.stop = stop

    P._ha_turno_corto = True
    print("patch 004: con l'expander i thread si alternano ogni 0,5 ms (erano 5)")
    return True


try:
    _applica()
except Exception as _e:
    print("patch 004: %s" % _e)
