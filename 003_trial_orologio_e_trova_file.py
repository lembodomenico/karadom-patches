# 003_trial_orologio_e_trova_file.py
#
# TRE COSE, tutte segnalate il 3 settembre 2026.
#
# 1) LA PROVA DI 60 MINUTI NON SCADEVA MAI. Il conto alla rovescia veniva
#    appeso alla finestra mezzo secondo dopo l'avvio: a quel punto la finestra
#    di KaraDom non esiste ancora (lo splash e' appena stato chiuso e la
#    schermata vera deve ancora nascere), quindi il controllo non partiva e il
#    thread usciva SENZA RIPROVARE. Il potenziale cliente restava dentro per
#    sempre. Qui la prova la sorveglia un thread che non ha bisogno di nessuna
#    finestra: allo scadere chiude, con o senza interfaccia.
#
# 2) OROLOGIO INTERNO. I minuti non si contano piu' sull'ora di Windows - che
#    si sposta con due clic, allungando la prova all'infinito - ma con il tempo
#    monotono del sistema, che parte dall'accensione e non si puo' portare
#    indietro: cambiare la data di Windows non allunga piu' la prova nemmeno
#    di un secondo. La prova torna piena a ogni avvio, come e' sempre stata.
#
# 3) YOUTUBE: BOTTONE "TROVA IL FILE". Sotto "Copia link" e "Download MP4"
#    compare un terzo bottone che apre la cartella di destinazione con il file
#    di quel video gia' selezionato.
#
# Se qualcosa non combacia con questa versione di KaraDom, la patch si sfila da
# sola e l'applicazione parte come prima.

import base64
import hashlib
import hmac
import json
import os
import sys
import threading
import time

# ============================================================ 1+2. LA PROVA

_AVVIO_MONO = time.monotonic()
_SEGRETO = b"KaraDom-orologio-2026"
DURATA_PROVA = 60 * 60          # secondi


def _file_orologio():
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    cartella = os.path.join(base, "KaraDom")
    try:
        os.makedirs(cartella, exist_ok=True)
    except Exception:
        pass
    return os.path.join(cartella, "_orologio.dat")


def _chiave():
    """Legata alla macchina: il file copiato su un altro PC non vale."""
    pezzi = [os.environ.get("COMPUTERNAME", ""), os.environ.get("USERNAME", "")]
    return hashlib.sha256(_SEGRETO + "|".join(pezzi).encode("utf-8", "ignore")).digest()


def _firma(testo):
    return base64.b64encode(
        hmac.new(_chiave(), testo.encode("utf-8"), hashlib.sha256).digest()).decode()


def _leggi():
    try:
        with open(_file_orologio(), "r", encoding="utf-8") as f:
            grezzo = json.load(f)
        corpo = grezzo.get("dati", "")
        if _firma(corpo) != grezzo.get("firma"):
            return {}
        return json.loads(corpo)
    except Exception:
        return {}


def _scrivi(dati):
    try:
        corpo = json.dumps(dati, sort_keys=True)
        tmp = _file_orologio() + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"dati": corpo, "firma": _firma(corpo)}, f)
        os.replace(tmp, _file_orologio())
    except Exception:
        pass


def _batti():
    """Segna che siamo arrivati fin qui: l'ora registrata non torna mai
    indietro, cosi' spostare la data di Windows non regala tempo."""
    d = _leggi()
    d["ultima_ora"] = max(time.time(), float(d.get("ultima_ora", 0) or 0))
    _scrivi(d)


def _root_viva():
    try:
        import tkinter as tk
        if tk._default_root is not None and tk._default_root.winfo_exists():
            return tk._default_root
    except Exception:
        pass
    return None


def _guardia_prova():
    """Conta i minuti e allo scadere chiude, finestra o non finestra.

    I 60 minuti ripartono pieni a ogni avvio: il conto e' della SESSIONE, e si
    misura col tempo monotono, che nessuno puo' spostare all'indietro."""
    inizio = time.monotonic()
    avvisato = False
    while True:
        usati = time.monotonic() - inizio
        rimasti = DURATA_PROVA - usati
        if rimasti <= 0:
            _batti()
            r = _root_viva()
            if r is not None:
                try:
                    r.after(0, r.destroy)
                    time.sleep(1.5)
                except Exception:
                    pass
            print("Prova di 60 minuti terminata.")
            os._exit(0)
        if rimasti <= 300 and not avvisato:
            avvisato = True
            r = _root_viva()
            if r is not None:
                try:
                    import tkinter.messagebox as mb
                    r.after(0, lambda: mb.showwarning(
                        "Prova in scadenza",
                        "Mancano 5 minuti alla fine del periodo di prova.\n\n"
                        "Inserisci una licenza per continuare a usare KaraDom."))
                except Exception:
                    pass
        _batti()
        time.sleep(min(20.0, max(1.0, rimasti)))


def _aggancia_prova():
    principale = sys.modules.get("__main__")
    originale = getattr(principale, "start_app_trial", None)
    if principale is None or not callable(originale):
        print("patch 003: modalita' prova non trovata, salto")
        return False

    def start_app_trial_sorvegliata(*args, **kwargs):
        threading.Thread(target=_guardia_prova, daemon=True).start()
        return originale(*args, **kwargs)

    principale.start_app_trial = start_app_trial_sorvegliata
    print("patch 003: prova sorvegliata (%.0f minuti)" % (DURATA_PROVA / 60.0))
    return True


# ============================================================ 3. TROVA IL FILE

def _aggancia_trova_file():
    import subprocess
    import tkinter as tk
    from tkinter import messagebox
    import moduli.yt2mp3 as yt

    P = getattr(yt, "YoutubePanel", None)
    if P is None or not hasattr(P, "_card_risultato"):
        print("patch 003: pannello YouTube diverso, salto il bottone")
        return False
    if getattr(P, "_ha_trova_file", False):
        return True

    S, F, _ = yt.S, yt.F, yt._
    add_tooltip = yt.add_tooltip
    originale = P._card_risultato

    def _nudo(testo):
        """Il nome ridotto all'osso: yt-dlp ripulisce il titolo (via ? : / e le
        virgolette), quindi il nome sul disco non e' mai identico a quello
        mostrato nella scheda."""
        return "".join(c for c in (testo or "").lower() if c.isalnum())

    def _cerca_per_titolo(self, cartella, titolo):
        nudo = _nudo(titolo)
        if not nudo:
            return None
        try:
            elenco = os.listdir(cartella)
        except Exception:
            return None
        candidati = []
        for f in elenco:
            base = _nudo(os.path.splitext(f)[0])
            if base and (base == nudo or (len(base) >= 8 and (base in nudo or nudo in base))):
                candidati.append(os.path.join(cartella, f))
        if not candidati:
            return None
        video = [c for c in candidati
                 if c.lower().endswith((".mp4", ".mkv", ".webm", ".mp3", ".m4a"))]
        return max(video or candidati, key=os.path.getmtime)

    def _trova_file(self, url, titolo=""):
        cartella = (self.cartella_var.get() or "").strip()
        if not cartella or not os.path.isdir(cartella):
            messagebox.showwarning(_("Errore"),
                                   _("Seleziona una cartella di destinazione!"),
                                   parent=self.root)
            return
        path = getattr(self, "_scaricati", {}).get(url)
        if not path or not os.path.exists(path):
            path = self._cerca_per_titolo(cartella, titolo)
        try:
            if path and os.path.exists(path):
                if sys.platform == "win32":
                    # come STRINGA: passandolo come lista, Python racchiude tutto
                    # l'argomento appena il percorso ha uno spazio ed explorer
                    # smette di riconoscere /select (apriva Documenti).
                    subprocess.Popen('explorer /select,"%s"' % os.path.normpath(path))
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", "-R", path])
                else:
                    subprocess.Popen(["xdg-open", os.path.dirname(path)])
                return
            if sys.platform == "win32":
                os.startfile(cartella)
            else:
                subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open",
                                  cartella])
            messagebox.showinfo(
                "File non trovato",
                "Questo video non risulta ancora scaricato in:\n%s\n\n"
                "Ho aperto la cartella: se il file c'e' ma ha un altro nome, "
                "lo trovi qui dentro." % cartella, parent=self.root)
        except Exception as e:
            messagebox.showerror(_("Errore"),
                                 "Impossibile aprire la cartella:\n%s" % e,
                                 parent=self.root)

    def _card_con_trova(self, host, url, thumb, title, row, col, wl):
        """La scheda originale, piu' il terzo bottone in fondo alla pila."""
        card = originale(self, host, url, thumb, title, row, col, wl)
        try:
            scheda = host.winfo_children()[-1]
            for riga in scheda.winfo_children():
                for btns in riga.winfo_children():
                    figli = list(getattr(btns, "winfo_children", lambda: [])())
                    if len(figli) == 2 and all(isinstance(b, tk.Button) for b in figli):
                        figli[0].pack_configure(pady=(0, S(6)))
                        figli[1].pack_configure(pady=(0, S(6)))
                        b = tk.Button(btns, text="📂 Trova il file",
                                      command=lambda u=url, t=title: self._trova_file(u, t),
                                      bg="#6c3fb5", fg="white",
                                      font=F("Segoe UI", 9, "bold"),
                                      relief="flat", cursor="hand2", width=S(17))
                        b.pack(side="top", fill="x")
                        add_tooltip(b, "Apre la cartella di destinazione con il file "
                                       "gia' selezionato")
                        return card
        except Exception as e:
            print("patch 003: bottone non aggiunto (%s)" % e)
        return card

    # ricordarsi il file appena scaricato, per aprirlo con certezza
    scarica_orig = getattr(P, "_download_thread", None)
    if callable(scarica_orig):
        def _download_ricorda(self, url, cartella):
            prima = set(os.listdir(cartella)) if os.path.isdir(cartella) else set()
            esito = scarica_orig(self, url, cartella)
            try:
                nuovi = [os.path.join(cartella, f) for f in os.listdir(cartella)
                         if f not in prima and f.lower().endswith(".mp4")]
                if nuovi:
                    if not hasattr(self, "_scaricati"):
                        self._scaricati = {}
                    self._scaricati[url] = max(nuovi, key=os.path.getmtime)
            except Exception:
                pass
            return esito
        P._download_thread = _download_ricorda

    P._cerca_per_titolo = _cerca_per_titolo
    P._trova_file = _trova_file
    P._card_risultato = _card_con_trova
    P._ha_trova_file = True
    print("patch 003: bottone Trova il file aggiunto alla finestra YouTube")
    return True


# ============================================================ applicazione

try:
    _aggancia_prova()
except Exception as _e:
    print("patch 003 (prova): %s" % _e)

try:
    _aggancia_trova_file()
except Exception as _e:
    print("patch 003 (trova file): %s" % _e)
