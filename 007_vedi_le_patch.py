# 007_vedi_le_patch.py
#
# UNA FINESTRA CHE DICE QUALI PATCH SONO ARRIVATE DAVVERO.
#
# Nasce da mezza giornata persa a chiedersi "e' arrivata o no?". Fino a ieri
# l'unico modo di saperlo era aprire KaraDom in modalita' debug e cercare le
# righe [HOTFIX] nel log: scomodo per noi e impossibile per un cliente al
# telefono. Ed e' proprio l'informazione che serve per prima, perche' fra la
# pubblicazione e l'arrivo ci sono di mezzo i cinque minuti di cache di GitHub
# e due riavvii del programma.
#
# DOVE. Menu Extra, subito sotto "Aggiorna": la voce "Patch applicate...".
#
# COSA MOSTRA, per ogni patch nella cartella:
#   - se e' stata APPLICATA, oppure scartata e perche' (firma mancante o non
#     valida: succede se il file e' stato toccato dopo la firma);
#   - la data in cui e' arrivata sul PC;
#   - la prima riga di commento del file, che dice a cosa serve.
#
# Le applicate le sa `moduli.hotfix.APPLICATE`, che il programma riempie
# all'avvio: non e' un elenco indovinato dai file presenti, e' quello che ha
# funzionato davvero.
#
# NOTA su come si aggancia al menu. Il menu Extra si costruisce dentro una
# funzione di ui.py e la sua variabile e' locale: da fuori non ci si arriva.
# Quindi si intercetta `Menu.add_command` e, appena passa la voce "Aggiorna",
# si aggiunge la nostra subito dopo. Finito quello, il metodo originale torna
# al suo posto: l'intercettazione dura il tempo di costruire il menu e non
# resta niente in mezzo.

import os
import time
import tkinter as tk
from tkinter import ttk


def _cartella():
    try:
        from moduli.hotfix import patches_dir
        return patches_dir()
    except Exception:
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        return os.path.join(base, "KaraDom", "patches")


def _descrizione(percorso):
    """La prima riga di commento che dice a cosa serve la patch."""
    try:
        with open(percorso, encoding="utf-8", errors="replace") as f:
            for _ in range(40):
                r = f.readline()
                if not r:
                    break
                r = r.strip()
                # si salta l'intestazione col nome del file e le righe vuote
                if r.startswith("#") and len(r) > 3 and not r[1:].strip().startswith(
                        os.path.basename(percorso)[:3]):
                    t = r.lstrip("# ").strip()
                    if len(t) > 12:
                        return t
    except Exception:
        pass
    return ""


def _stato(nome, percorso):
    """(stato, spiegazione) di una patch che sta nella cartella."""
    try:
        from moduli.hotfix import APPLICATE
        if nome in APPLICATE:
            return "attiva", ""
    except Exception:
        pass
    if not os.path.exists(percorso + ".sig"):
        return "scartata", "manca la firma"
    return "scartata", "firma non valida, o errore mentre si applicava"


def _finestra(parent=None):
    d = _cartella()
    try:
        file = sorted(f for f in os.listdir(d) if f.endswith(".py"))
    except Exception:
        file = []

    w = tk.Toplevel(parent)
    w.title("Patch applicate")
    w.configure(bg="#1a1a1a")
    w.geometry("760x420")
    try:
        from moduli.ui_utils import imposta_icona
        imposta_icona(w)
    except Exception:
        pass

    tk.Label(w, text="Correzioni ricevute da KaraDom",
             bg="#1a1a1a", fg="white", font=("Arial", 13, "bold")).pack(pady=(12, 2))
    tk.Label(w, text=d, bg="#1a1a1a", fg="#888", font=("Arial", 8)).pack()

    cornice = tk.Frame(w, bg="#1a1a1a")
    cornice.pack(fill="both", expand=True, padx=12, pady=10)

    col = ("stato", "patch", "arrivata", "cosa fa")
    t = ttk.Treeview(cornice, columns=col, show="headings", height=12)
    for c, larghezza in zip(col, (70, 210, 120, 340)):
        t.heading(c, text=c.upper())
        t.column(c, width=larghezza, anchor="w")
    barra = ttk.Scrollbar(cornice, orient="vertical", command=t.yview)
    t.configure(yscrollcommand=barra.set)
    t.pack(side="left", fill="both", expand=True)
    barra.pack(side="right", fill="y")

    t.tag_configure("ok", foreground="#4ade80")
    t.tag_configure("no", foreground="#f87171")

    attive = 0
    for nome in file:
        p = os.path.join(d, nome)
        stato, perche = _stato(nome, p)
        quando = time.strftime("%d/%m/%Y %H:%M", time.localtime(os.path.getmtime(p)))
        testo = _descrizione(p) if stato == "attiva" else (perche or _descrizione(p))
        t.insert("", "end", values=("attiva" if stato == "attiva" else "scartata",
                                    nome, quando, testo),
                 tags=("ok" if stato == "attiva" else "no",))
        attive += 1 if stato == "attiva" else 0

    if not file:
        t.insert("", "end", values=("", "(nessuna patch)", "",
                                    "il programma non ne ha ancora ricevute"))

    tk.Label(w, text="%d attive su %d ricevute  —  se ne hai appena pubblicata "
                     "una, ricorda i 5 minuti di attesa e due riavvii"
                     % (attive, len(file)),
             bg="#1a1a1a", fg="#aaa", font=("Arial", 9)).pack(pady=(0, 6))
    tk.Button(w, text="Chiudi", command=w.destroy, bg="#333", fg="white",
              relief="flat", padx=24, pady=6, cursor="hand2").pack(pady=(0, 12))

    w.transient(parent)
    try:
        w.grab_set()
    except Exception:
        pass


def _aggancia():
    """Mette 'Patch applicate...' subito sotto 'Aggiorna' nel menu Extra."""
    originale = tk.Menu.add_command
    fatto = {"si": False}

    def add_command(self, cnf={}, **kw):
        esito = originale(self, cnf, **kw)
        if fatto["si"]:
            return esito
        etichetta = str(kw.get("label") or (cnf or {}).get("label") or "")
        # la voce puo' essere tradotta: si guarda la radice della parola
        if etichetta.strip().lower() in ("aggiorna", "update", "actualizar",
                                         "mettre a jour", "aktualisieren"):
            try:
                originale(self, {}, label="Patch applicate...",
                          command=lambda: _finestra(self.master))
                fatto["si"] = True
                tk.Menu.add_command = originale     # il trucco finisce qui
            except Exception:
                pass
        return esito

    tk.Menu.add_command = add_command


try:
    _aggancia()
    print("patch 007: nel menu Extra c'e' 'Patch applicate...'")
except Exception as _e:
    print("patch 007: %s" % _e)
