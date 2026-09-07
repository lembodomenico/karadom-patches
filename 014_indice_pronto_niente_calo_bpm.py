# 014_indice_pronto_niente_calo_bpm.py
#
# SCRIVENDO NELLA RICERCA, CON L'EXPANDER, I BPM CALAVANO.
#
# L'indizio decisivo l'ha dato il cliente: **incollando** tutta la ricerca in
# una volta non succedeva niente, **digitandola** lettera per lettera si'.
# Incollare = una ricerca sola; digitare dieci lettere = dieci ricerche. Il
# costo, quindi, stava in cio' che OGNI ricerca rifaceva da capo.
#
# COS'ERA: l'indice di ricerca (`nome_lower`, `ext`, `parole`) non veniva
# costruito al caricamento. La 009 prepara `tokens` per i preferiti, ma non
# quello — cosi' se lo fabbricava `_ensure_search_index` dentro il thread di
# RICERCA, mentre l'utente digita e la musica suona.
#
# MISURATO su 400.000 brani:
#     costruire l'indice ........... 0,68 secondi
#     il thread del MIDI intanto ... 24 ms di ritardo medio, punte di 150 ms,
#                                    oltre i 50 ms venti volte su 137
# E 50 ms e' proprio la soglia oltre cui il player butta via il tempo
# (`if delta_time > 0.05: delta_time = 0.05`): quel tempo non torna piu', e i
# BPM calano. Con l'expander e' peggio, perche' ogni nota esce da una porta di
# sistema, molla il GIL e per riprenderlo aspetta il suo turno.
#
# COSA CAMBIA:
#   punto 1  l'indice si costruisce al CARICAMENTO, nello stesso ciclo che gia'
#            scorre i brani e si ferma ogni 2000 per lasciar respirare la
#            musica. La ricerca lo trova gia' pronto e non lo rifa' mai piu'.
#   punto 2  `_ensure_search_index` resta come rete di sicurezza, ma adesso
#            RESPIRA e si FERMA se l'utente ha digitato un'altra lettera.
#
# ------------------------------------------------------------------------
# SE NON VA BENE, SI TORNA INDIETRO IN DUE MODI
#
#   1. RITIRO PER TUTTI: dal menu (`PATCH KARADOM.bat`) si digita R14. Al
#      lancio successivo i client la cancellano e tutto torna com'era.
#      Il ritiro e' PULITO: questa patch sostituisce due metodi in memoria e
#      non scrive niente da nessuna parte. L'elenco salvato su disco contiene
#      solo i PERCORSI dei file (lo scriveva gia' la 009), non l'indice:
#      togliendo la patch quel file resta valido e non va cancellato.
#
#   2. SPEGNERLA SU UNA MACCHINA SOLA, senza toccare il manifest: nella
#      configurazione si mette   patch_014 = 0   e al riavvio la patch non
#      fa piu' niente. Serve quando si vuole provare "con e senza" sullo
#      stesso PC, o se un cliente ha un problema e gli altri no.
#
#   Gli originali dei due metodi vengono comunque conservati in
#   `_orig_014_ricostruisci` e `_orig_014_indice`, con nomi propri di questa
#   patch: nessun'altra patch puo' sovrascriverli (la 013 si era bloccata
#   proprio per due punti che usavano lo stesso nome).
# ------------------------------------------------------------------------
#
# Non tocca il player, il MIDI, il timing ne' il debounce della ricerca: le
# correzioni al timing erano gia' state provate sul campo e ritirate. Qui non
# si rattoppa il tempo perso, si toglie il lavoro che lo faceva perdere.


# ------------------------------------------------------------------ punto 1
#   L'INDICE DI RICERCA SI PREPARA AL CARICAMENTO
#
#   Si sostituisce `_ricostruisci_elenchi` (il percorso dell'elenco salvato,
#   quello di tutti i giorni) con una versione che mette nel dizionario anche
#   le tre chiavi della ricerca. Il ciclo e' lo stesso, il respiro e' lo
#   stesso: cambia solo cosa ci si porta dietro.

CODICE_ELENCHI = '''
def _voce_brano_014(path):
    """Il dizionario di un brano, gia' pronto per la ricerca."""
    nome = os.path.basename(path)
    nome_lower = nome.lower()
    senza, est = os.path.splitext(nome_lower)
    ext = est[1:] if est else ''
    if ' - ' in senza:                       # "Artista - Titolo"
        davanti, _sep, dietro = senza.partition(' - ')
        parole = davanti.split() + dietro.split()
    else:
        parole = senza.split()
    if ext:
        parole.append(ext)
    return {'nome': nome, 'path': path, 'tokens': senza.split(),
            'nome_lower': nome_lower, 'ext': ext, 'parole': parole}


def _ricostruisci_elenchi(self, brani, cartella, cache, chiave):
    """Da un elenco di percorsi rifa' nomi e indice, SENZA toccare il disco.

    In un thread e con pause: su 400.000 brani sono un paio di secondi, e
    nella finestra bloccherebbero tutto - musica compresa.

    [014] Adesso prepara anche l'indice della RICERCA. Prima mancava, e a
    farlo era il thread di ricerca a ogni tasto premuto: 0,68 s di macinio
    che facevano calare i BPM sull'expander.
    """
    import time as _time
    RESPIRO_OGNI = 2000

    def lavora():
        nuovi, indice = [], {}
        for n, path in enumerate(brani):
            if n % RESPIRO_OGNI == 0 and n:
                _time.sleep(0.002)
            senza = os.path.splitext(os.path.basename(path))[0].lower()
            nuovi.append(_voce_brano_014(path))
            indice[path] = re.findall(r"[a-zA-Z0-9\\u00e0\\u00e8\\u00e9\\u00ec\\u00f2\\u00f3\\u00f9]+", senza)

        def _assegna():
            self.brani_completi = brani
            self.brani_pc = nuovi
            self.indice_preferiti = indice
            cache[chiave] = (brani, nuovi, indice)
            print("\\u2705 %d brani pronti, ricerca gia' indicizzata" % len(brani))

        try:
            self.parent.after(0, _assegna)
        except Exception:
            _assegna()

    threading.Thread(target=lavora, daemon=True).start()
'''


# ------------------------------------------------------------------ punto 2
#   LA RETE DI SICUREZZA: SE L'INDICE MANCA LO STESSO, NON DEVE FAR MALE
#
#   Con la scansione dal disco (tasto destro) la lista arriva ancora senza
#   indice, perche' quel pezzo sta dentro `carica_brani` della 009 e non si
#   puo' sostituire da solo. Allora si rende innocuo il rimedio: respiro ogni
#   2000 brani, e stop appena arriva un altro tasto.

CODICE_INDICE = '''
def _ensure_search_index(self, gen=None):
    """Pre-calcola i campi di ricerca su brani_pc, se mancano.

    [014] RESPIRA e si FERMA. Prima era un ciclo su 400.000 brani dentro il
    thread di ricerca, senza mai mollare il turno: il thread del MIDI
    arrivava in ritardo di 24 ms in media, con punte di 150, e oltre i 50 ms
    il player butta via il tempo - da cui il calo dei BPM.
    """
    import time as _time
    if not self.brani_pc:
        return
    if 'parole' in self.brani_pc[0]:
        return
    for _n, b in enumerate(self.brani_pc):
        if _n % 2000 == 0 and _n:
            if gen is not None and getattr(self, '_search_generation', 0) != gen:
                return                      # l'utente ha digitato dell'altro
            _time.sleep(0.002)              # lascia il turno alla musica
        nome_lower = b['nome'].lower()
        nome_senza_ext, ext_con_punto = os.path.splitext(nome_lower)
        ext = ext_con_punto[1:] if ext_con_punto else ""
        if ' - ' in nome_senza_ext:
            parti = nome_senza_ext.split(' - ', 1)
            parole = parti[0].strip().split() + parti[1].strip().split()
        else:
            parole = nome_senza_ext.split()
        if ext:
            parole.append(ext)
        b['nome_lower'] = nome_lower
        b['ext'] = ext
        b['parole'] = parole
'''


def _spenta():
    """L'interruttore: `patch_014 = 0` nella configurazione la disattiva.

    Se la configurazione non si legge (non e' KaraDom, database assente), si
    considera ACCESA: una patch che si spegne da sola al primo intoppo non
    servirebbe a niente.
    """
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_014', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def apply():
    if _spenta():
        print("patch 014: spenta dalla configurazione (patch_014 = 0)")
        return False

    fatti = []

    # punto 1 --------------------------------------------------------------
    try:
        import moduli.libreria_scan_mixin as L
        C = getattr(L, "LibreriaScanMixin", None)
        if C is not None and hasattr(C, "_ricostruisci_elenchi"):
            # si compila NELLO SPAZIO DEI NOMI del modulo: dentro servono
            # os, re, threading, che qui non ci sono
            spazio_scan = L.__dict__
            exec(compile(CODICE_ELENCHI, "<patch014a>", "exec"), spazio_scan)
            # l'originale si conserva con un nome PROPRIO di questa patch:
            # nessun altro punto e nessun'altra patch puo' calpestarlo
            if not hasattr(C, "_orig_014_ricostruisci"):
                C._orig_014_ricostruisci = C._ricostruisci_elenchi
            setattr(C, "_ricostruisci_elenchi", spazio_scan["_ricostruisci_elenchi"])
            fatti.append("elenco salvato indicizzato al caricamento")
        else:
            print("patch 014: LibreriaScanMixin diverso, salto il punto 1")
    except Exception as e:
        print("patch 014 punto 1: %s" % e)

    # punto 2 --------------------------------------------------------------
    try:
        import moduli.libreria_search_mixin as S
        C2 = getattr(S, "LibreriaSearchMixin", None)
        if C2 is not None and hasattr(C2, "_ensure_search_index"):
            spazio_search = S.__dict__
            exec(compile(CODICE_INDICE, "<patch014b>", "exec"), spazio_search)
            if not hasattr(C2, "_orig_014_indice"):
                C2._orig_014_indice = C2._ensure_search_index
            setattr(C2, "_ensure_search_index", spazio_search["_ensure_search_index"])
            fatti.append("indice di riserva col respiro")
        else:
            print("patch 014: LibreriaSearchMixin diverso, salto il punto 2")
    except Exception as e:
        print("patch 014 punto 2: %s" % e)

    if fatti:
        print("patch 014: niente calo di BPM scrivendo nella ricerca (%s)"
              % ", ".join(fatti))
        return True
    return False


def revert():
    """Rimette i due metodi originali, senza riavviare.

    Non serve al ritiro normale (togliendo la patch dal manifest, al lancio
    dopo non viene proprio applicata): serve per provare "con e senza" nella
    stessa sessione, da una console.
    """
    rimessi = []
    try:
        import moduli.libreria_scan_mixin as L
        C = L.LibreriaScanMixin
        if hasattr(C, "_orig_014_ricostruisci"):
            C._ricostruisci_elenchi = C._orig_014_ricostruisci
            rimessi.append("_ricostruisci_elenchi")
    except Exception as e:
        print("revert 014 punto 1: %s" % e)
    try:
        import moduli.libreria_search_mixin as S
        C2 = S.LibreriaSearchMixin
        if hasattr(C2, "_orig_014_indice"):
            C2._ensure_search_index = C2._orig_014_indice
            rimessi.append("_ensure_search_index")
    except Exception as e:
        print("revert 014 punto 2: %s" % e)
    print("patch 014: rimessi gli originali (%s)" % (", ".join(rimessi) or "niente"))
    return bool(rimessi)
