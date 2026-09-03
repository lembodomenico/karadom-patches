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
#
# 3) IL RIAVVIO IN DEBUG CHE NON FUNZIONAVA. Senza questo, il punto 2 e' inutile:
#    "Extra > Riavvia con debug" costruiva il comando con `sys.executable`, che
#    nella build e' il python.exe INTERNO del programma (verificato nel log del
#    cliente: Executable=...KaraDom\python.exe, Frozen=False). Lanciava quindi
#    `python.exe debug`: python cercava un file chiamato "debug", non lo trovava
#    e moriva in silenzio - nessuna finestra, nessun riavvio. Ora il programma
#    rilancia se stesso (sys.argv[0]).
#
# 4) LE DIPENDENZE DI YOUTUBE CHE NON ARRIVAVANO. Due difetti a catena:
#    - `dep_sync` scaricava lo zip delle dipendenze da
#      www.karadom.it/download/dipendenze.zip, che risponde **404**: la
#      sincronia non e' mai partita per nessuno. Lo zip lo pubblica la build su
#      GitHub Releases (200, e col supporto Range che serve a quel modulo).
#    - nell'installato mancavano `ytdlp_local_server.py` e `yt-dlp.conf`, cioe'
#      il server yt-dlp locale (quello preso da Karaoke 5) non partiva mai e si
#      ripiegava sull'exe.
#    La patch corregge l'indirizzo e si porta dentro i due file, scrivendoli
#    accanto al programma o - se la cartella non e' scrivibile - in
#    %LOCALAPPDATA%\KaraDom\dipendenze, dove il client impara a cercarli.
#    ⚠️ Il python embedded `pyserver/` (77 MB) non puo' stare in una patch:
#    arriva con lo zip delle dipendenze, che va rigenerato.

import base64
import os
import sys
import threading
import time
import zlib

SERVER_B64 = (
    "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"
    "p6xo7Uc/yNZeCiqXpKFjoPF/5+fs8g=="
)

CONF_B64 = (
    "eNpNjs1KAzEURvcD8w6Xdp1mP7vigGIRwepCcHMn+ZymTXJDfor69M6giPtzOGdLn1VZn3ZG4jspmhGRuQpZpgNnHiX0Xd9t"
    "6Z6vfDTZpUq5xeoCKCGTB5kTe484g16lPbcJfafUuahfrNDGIspwM+iXgly0R5hEjyiXKkkf9k/78fFBW5cQF/ALbyu+wwc2"
    "P+Wj4ewMr0e3rt61iRwZCUkilsCSB2VXxF8lCnn+92PhKUhYMFmfMoJUqD+3EM5lmF09tanvvgG5yVsV"
)

def _scrivi(cartella, nome, dati):
    try:
        os.makedirs(cartella, exist_ok=True)
        p = os.path.join(cartella, nome)
        if os.path.exists(p) and os.path.getsize(p) == len(dati):
            return p
        with open(p, "wb") as f:
            f.write(dati)
        return p
    except Exception:
        return None


def _dipendenze_youtube():
    """Indirizzo giusto dello zip + i due file che mancavano nell'installato."""
    fatte = []
    try:
        import moduli.dep_sync as ds
        giusto = ("https://github.com/lembodomenico/KaraDom/releases/download/"
                  "dipendenze/dipendenze.zip")
        if getattr(ds, "DEP_ZIP_URL", "") != giusto:
            ds.DEP_ZIP_URL = giusto
            fatte.append("indirizzo dello zip delle dipendenze corretto (era un 404)")
    except Exception:
        pass

    try:
        import moduli.youtube_local as yl
        dep = None
        try:
            dep = yl._dep_dir()
        except Exception:
            dep = None
        srv = zlib.decompress(base64.b64decode(SERVER_B64))
        cfg = zlib.decompress(base64.b64decode(CONF_B64))

        scritto = _scrivi(dep, "ytdlp_local_server.py", srv) if dep else None
        dove = dep
        if not scritto:      # cartella del programma non scrivibile (Program Files)
            dove = os.path.join(os.environ.get("LOCALAPPDATA") or
                                os.path.expanduser("~"), "KaraDom", "dipendenze")
            scritto = _scrivi(dove, "ytdlp_local_server.py", srv)
        if scritto:
            _scrivi(dove, "yt-dlp.conf", cfg)
            fatte.append("server yt-dlp locale installato in %s" % dove)

            # il client deve cercarlo anche dove l'abbiamo messo
            cerca_prima = yl._server_script

            def _server_script():
                s = cerca_prima()
                if s:
                    return s
                p = os.path.join(dove, "ytdlp_local_server.py")
                return p if os.path.exists(p) else None

            yl._server_script = _server_script
    except Exception as e:
        fatte.append("dipendenze YouTube: %s" % e)

    for f in fatte:
        print("patch 004: %s" % f)
    return bool(fatte)


def _riavvio_debug():
    """Ripara "Riavvia con debug": deve rilanciare KaraDom, non il python interno."""
    try:
        import os as _os
        import sys as _sys
        import moduli.debug_tools as dt
    except Exception:
        return False

    def _exe_karadom():
        a0 = _os.path.abspath(_sys.argv[0]) if (_sys.argv and _sys.argv[0]) else ""
        if a0.lower().endswith(".exe"):
            return a0
        exe = _os.path.abspath(_sys.executable) if _sys.executable else ""
        if exe.lower().endswith(".exe") and "python" not in _os.path.basename(exe).lower():
            return exe
        return ""

    def _launch_cmd_debug():
        exe = _exe_karadom()
        if exe:
            root_dir = _os.path.dirname(exe)
            target = '"%s" debug' % exe
        else:
            root_dir = dt._app_root()
            script = _os.path.abspath(_sys.argv[0]) if (_sys.argv and _sys.argv[0])                 else _os.path.join(root_dir, "KaraDom.py")
            target = '"%s" "%s" debug' % (_sys.executable, script)
        return ('cmd /c timeout /t 2 /nobreak >nul & start "" /d "%s" %s'
                % (root_dir, target))

    dt._exe_karadom = _exe_karadom
    dt._launch_cmd_debug = _launch_cmd_debug
    print("patch 004: 'Riavvia con debug' ora rilancia KaraDom (era il python interno)")
    return True


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
    _dipendenze_youtube()
except Exception as _e:
    print("patch 004 (dipendenze YouTube): %s" % _e)

try:
    _riavvio_debug()
except Exception as _e:
    print("patch 004 (riavvio debug): %s" % _e)

try:
    _applica()
except Exception as _e:
    print("patch 004: %s" % _e)
