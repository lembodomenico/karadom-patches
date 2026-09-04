# 004_midi_expander_bpm.py
#
# [2026-09-04] QUESTA PATCH NON TOCCA PIU' IL MIDI.
# Il fix dei thread e la spia sono usciti di qui: la spia vive da sola nella
# 006, cosi' si puo' provare KaraDom col motore MIDI originale senza perdere
# le due correzioni che stanno qui sotto e non c'entrano niente col MIDI.
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
#    La patch corregge l'indirizzo e, in sottofondo, SCARICA dallo zip i file
#    che mancano nella cartella dipendenze (lettura per Range: solo i pezzi
#    necessari, non i 400 MB). Non tocca quelli gia' presenti, cosi' non puo'
#    riportare indietro roba piu' nuova.

import base64
import os
import sys
import threading
import time
import urllib.request
import zipfile

ZIP_DIPENDENZE = ("https://github.com/lembodomenico/KaraDom/releases/download/"
                  "dipendenze/dipendenze.zip")
import zlib

class _ZipRemoto:
    """Legge uno zip su HTTP a pezzi (Range), senza scaricarlo tutto.

    ⚠️ Sta qui dentro e non usa `moduli.dep_sync` perche' **quel modulo non
    esiste nella build**: Nuitka compila solo cio' che qualcuno importa, e
    dep_sync non era chiamato da nessuno (verificato: la stringa 'moduli.dep_sync'
    non compare in KaraDom.exe). La patch deve percio' bastare a se stessa."""

    def __init__(self, url, timeout=30):
        self.url, self.timeout, self.pos = url, timeout, 0
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            self.size = int(r.headers.get("Content-Length") or 0)
            self.url = r.geturl()          # segue il redirect di GitHub
        if not self.size:
            raise OSError("lunghezza dello zip sconosciuta")

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, offset, whence=0):
        self.pos = (offset if whence == 0 else
                    self.pos + offset if whence == 1 else self.size + offset)
        return self.pos

    def read(self, n=-1):
        if n is None or n < 0:
            n = self.size - self.pos
        if n <= 0 or self.pos >= self.size:
            return b""
        fine = min(self.pos + n, self.size) - 1
        req = urllib.request.Request(
            self.url, headers={"Range": "bytes=%d-%d" % (self.pos, fine)})
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            dati = r.read()
        self.pos += len(dati)
        return dati

    def close(self):
        pass


def _diario(riga):
    """Scrive SEMPRE cosa succede, anche fuori dalla modalita' debug.

    ⚠️ Senza questo si resta ciechi: ad avvio normale KaraDom non scrive log,
    quindi un errore qui (permessi, rete, cartella sbagliata) sparisce e sembra
    solo che "non scarica". Il file sta in %LOCALAPPDATA%, che e' scrivibile
    sempre, anche quando il programma e' installato in Program Files."""
    print("patch 004: %s" % riga)
    try:
        base = os.path.join(os.environ.get("LOCALAPPDATA") or
                            os.path.expanduser("~"), "KaraDom")
        os.makedirs(base, exist_ok=True)
        with open(os.path.join(base, "dipendenze_log.txt"), "a", encoding="utf-8") as f:
            f.write("%s  %s\n" % (time.strftime("%d/%m %H:%M:%S"), riga))
    except Exception:
        pass


def _cartella_scrivibile(d):
    try:
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, "_prova_scrittura.tmp")
        with open(p, "wb") as f:
            f.write(b"x")
        os.remove(p)
        return True
    except Exception:
        return False


def _cartella_dipendenze():
    """Dove mettere le dipendenze: accanto al programma se si puo' scrivere,
    altrimenti in %LOCALAPPDATA%\\KaraDom\\dipendenze.

    KaraDom installato in Program Files gira SENZA privilegi di amministratore:
    li' dentro non puo' scrivere. In quel caso i file vanno in una cartella
    dell'utente, e piu' sotto si insegna al programma a cercarli anche li'."""
    accanto = None
    try:
        import moduli.youtube_local as yl
        accanto = yl._dep_dir()
    except Exception:
        accanto = None
    if not accanto:
        base = os.path.dirname(os.path.abspath(sys.argv[0] or sys.executable))
        accanto = os.path.join(base, "dipendenze")

    if _cartella_scrivibile(accanto):
        return accanto, True
    alternativa = os.path.join(os.environ.get("LOCALAPPDATA") or
                               os.path.expanduser("~"), "KaraDom", "dipendenze")
    _diario("%s non e' scrivibile (serve l'amministratore): uso %s"
            % (accanto, alternativa))
    return alternativa, False


def _insegna_dove_cercare(cartella):
    """Il programma cerca il server yt-dlp solo accanto a se': se i file sono
    finiti nella cartella dell'utente, deve guardare anche li'."""
    try:
        import moduli.youtube_local as yl
    except Exception:
        return
    py_prima, sc_prima = yl._server_py, yl._server_script

    def _server_py():
        p = py_prima()
        if p:
            return p
        p = os.path.join(cartella, "pyserver", "python.exe")
        return p if os.path.exists(p) else None

    def _server_script():
        s = sc_prima()
        if s:
            return s
        s = os.path.join(cartella, "ytdlp_local_server.py")
        return s if os.path.exists(s) else None

    yl._server_py = _server_py
    yl._server_script = _server_script


def _scrivi_file(percorso, dati):
    os.makedirs(os.path.dirname(percorso), exist_ok=True)
    tmp = percorso + ".part"
    with open(tmp, "wb") as f:
        f.write(dati)
    os.replace(tmp, percorso)


def _dipendenze_youtube():
    """Scarica dallo zip i file che MANCANO nella cartella dipendenze.

    Non tocca quelli gia' presenti: cosi' non puo' riportare indietro roba piu'
    nuova (per esempio yt-dlp.exe, che si aggiorna per conto suo).
    """
    def lavora():
        try:
            dest, accanto = _cartella_dipendenze()
            if not accanto:
                _insegna_dove_cercare(dest)
            _diario("controllo le dipendenze in %s" % dest)

            zf = zipfile.ZipFile(_ZipRemoto(ZIP_DIPENDENZE))
            manca = [i for i in zf.infolist() if not i.is_dir() and not
                     os.path.exists(os.path.join(dest, i.filename.replace("/", os.sep)))]
            if not manca:
                _diario("dipendenze gia' complete, niente da scaricare")
                return
            _diario("mancano %d file su %d, li scarico" % (len(manca), len(zf.infolist())))
            presi = byte = 0

            # ⚠️ Un file alla volta costa una richiesta HTTP a testa: misurato,
            #    circa 2,5 file al secondo. Se ne mancano tanti (e' il caso di
            #    `pyserver/`, che da solo sono migliaia di file) conviene tirare
            #    giu' lo zip intero una volta sola: misurato, 4263 file in 25 s.
            if len(manca) > 200:
                _diario("sono tanti: scarico lo zip in una volta sola")
                tmp = os.path.join(os.environ.get("TEMP") or dest, "_dipendenze_kd.zip")
                with urllib.request.urlopen(ZIP_DIPENDENZE, timeout=60) as r, \
                        open(tmp, "wb") as f:
                    while True:
                        blocco = r.read(1024 * 512)
                        if not blocco:
                            break
                        f.write(blocco)
                zf = zipfile.ZipFile(tmp)
                try:
                    for info in manca:
                        try:
                            dati = zf.read(info.filename)
                            _scrivi_file(os.path.join(dest, info.filename.replace("/", os.sep)), dati)
                            presi += 1
                            byte += len(dati)
                        except Exception as e:
                            if presi == 0:
                                _diario("scrittura non riuscita (%s): %s" % (info.filename, e))
                finally:
                    zf.close()
                    try:
                        os.remove(tmp)
                    except Exception:
                        pass
            else:
                for info in manca:
                    try:
                        with zf.open(info) as f:
                            dati = f.read()
                        _scrivi_file(os.path.join(dest, info.filename.replace("/", os.sep)), dati)
                        presi += 1
                        byte += len(dati)
                    except Exception as e:
                        _diario("  %s non scaricato (%s)" % (info.filename, e))

            _diario("dipendenze completate: %d file, %.1f MB in %s"
                    % (presi, byte / 1048576.0, dest))
        except Exception as e:
            _diario("scaricamento non riuscito: %s: %s" % (type(e).__name__, e))

    threading.Thread(target=lavora, daemon=True).start()
    return True


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


try:
    _dipendenze_youtube()
except Exception as _e:
    print("patch 004 (dipendenze YouTube): %s" % _e)

try:
    _riavvio_debug()
except Exception as _e:
    print("patch 004 (riavvio debug): %s" % _e)
