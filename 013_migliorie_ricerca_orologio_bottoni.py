# 013_migliorie_ricerca_orologio_bottoni.py
#
# UNA PATCH SOLA con tutto quello messo a punto nella notte fra il 5 e il 6
# settembre 2026. Sostituisce le tre separate (contrasto bottoni, ricerca per
# tipo, orologio) che non erano ancora state pubblicate.
#
# 1. CONTRASTO SUI BOTTONI DEL PLAYER
#    Con la barra bassa diventata blu notte scurissimo (#060c1c), i bottoni
#    neri (#000000) ci si mimetizzavano. Il bordo e' un Frame colorato messo
#    DIETRO al bottone: puro layout, quindi si vede identico su Windows e su
#    Linux.
#    ⚠️ Due strade gia' provate e SCARTATE: colorare lo sfondo del bottone
#    (le icone PNG hanno margini trasparenti diversi, il colore traspariva in
#    modo incoerente) e highlightthickness (su WINDOWS Tk non lo disegna
#    affatto: provato a 1, 2 e 3 pixel, a schermo non cambiava niente).
#
# 2. SUGGERIMENTI PER TIPO: prima gli mp3, poi i video (mp4), poi i midi.
#    Prima i tre archivi si interlacciavano e uscivano mescolati.
#    ⚠️ Il solo ordine non basta: gli mp3 in archivio sono oltre 14.000 e da
#    soli riempiono tutto il limite, quindi video e midi non si vedrebbero
#    MAI (misurato: cercando "amore", 200 risultati su 200 erano mp3). Ogni
#    tipo ha una fetta garantita. Sul notebook, con limite 60:
#        amore    mp3 x46  poi  video x7  poi  midi x7
#        volare   mp3 x28  poi  midi x16   (niente video: lo spazio va agli altri)
#
# 3. GLI ARCHIVI COMPAIONO SEMPRE NEI SUGGERIMENTI
#    Appena la cartella mappata e' ricca, i file su disco riempivano da soli
#    tutti e 80 i posti e gli archivi sparivano: sembrava che la ricerca non
#    guardasse nemmeno nei database, mentre li interrogava e poi ne buttava
#    via i risultati. Misurato con 100 file su disco:
#        prima:  disco 80,  archivi 0,   online 0
#        dopo:   disco 48,  archivi 24,  online 8
#
# 4. OROLOGIO CON I SECONDI (Windows e Linux)
#    Mostrava solo ore e minuti pur aggiornandosi gia' ogni secondo: per 59
#    secondi su 60 ridisegnava lo stesso testo.
#
# 5. SU LINUX SPARISCE LA BARRA TITOLO DISEGNATA DENTRO L'APPLICAZIONE
#    Logo, edizione e versione ora stanno nella barra di sistema in cima allo
#    schermo: quella dentro l'applicazione era un doppione una riga sotto
#    l'altra, e rubava sc(26) pixel di altezza. Su Windows non cambia nulla:
#    li' la titlebar la disegna il sistema.

import sys
import tkinter as tk


# ==========================================================================
# 1. CONTRASTO SUI BOTTONI DEL PLAYER
# ==========================================================================
_BORDO = '#5b78c4'      # blu, la variante scelta
_SPESSORE = 1           # pixel di bordo su ogni lato

_ORIG_INIT = tk.Button.__init__
_ORIG_PACK = tk.Button.pack


def _button_init_bordo(self, master=None, **kw):
    metti_bordo = False
    try:
        if str(kw.get('bg', '')).lower() == '#000000':
            metti_bordo = True
            # Se il genitore E' GIA' un Frame del colore del bordo, vuol dire
            # che il bordo c'e' gia' (versione del sorgente che lo fa da se',
            # oppure patch applicata due volte): un secondo Frame darebbe un
            # bordo doppio e piu' spesso.
            try:
                if isinstance(master, tk.Frame) and str(master.cget('bg')).lower() == _BORDO:
                    metti_bordo = False
            except Exception:
                pass
    except Exception:
        metti_bordo = False

    if not metti_bordo:
        _ORIG_INIT(self, master, **kw)
        return

    try:
        holder = tk.Frame(master, bg=_BORDO)
        _ORIG_INIT(self, holder, **kw)
        _ORIG_PACK(self, padx=_SPESSORE, pady=_SPESSORE)
        # chi posiziona il bottone in realta' posiziona il Frame che lo contiene
        self.pack = holder.pack
        self.pack_forget = holder.pack_forget
        self.grid = holder.grid
        self.grid_forget = holder.grid_forget
        self.place = holder.place
        self.place_forget = holder.place_forget
        self._bordo_holder = holder
    except Exception:
        # qualunque imprevisto: bottone normale, senza bordo. Meglio un bottone
        # senza contrasto che una schermata che non si apre.
        try:
            _ORIG_INIT(self, master, **kw)
        except Exception:
            pass


tk.Button.__init__ = _button_init_bordo

print("patch 013: bordo di contrasto sui bottoni del player (Frame, visibile anche su Windows)")


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



# ==========================================================================
# 1. OROLOGIO CON I SECONDI
# ==========================================================================
try:
    from moduli import monitor

    _classe_monitor = None
    for _nome in dir(monitor):
        _o = getattr(monitor, _nome)
        if isinstance(_o, type) and hasattr(_o, '_update_clock'):
            _classe_monitor = _o
            break

    if _classe_monitor is None:
        print("⚠️ patch 015: non trovo chi disegna l'orologio")
    elif getattr(_classe_monitor, '_orologio_con_secondi', False):
        pass
    else:
        def _update_clock_con_secondi(self):
            """Come l'originale, ma scrive anche i secondi."""
            import datetime
            try:
                self.time_label.config(text=datetime.datetime.now().strftime("%H:%M:%S"))
            except Exception:
                pass
            try:
                self.master.after(1000, self._update_clock)
            except Exception:
                pass

        _classe_monitor._update_clock = _update_clock_con_secondi
        _classe_monitor._orologio_con_secondi = True
        print("🕐 Orologio: ora con i secondi")
except Exception as _e:
    print("⚠️ patch 015, orologio non modificato: %s" % _e)


# ==========================================================================
# 2. ARCHIVI SEMPRE PRESENTI NEI SUGGERIMENTI
# ==========================================================================
# Il taglio agli 80 avviene dentro il thread di ricerca, in una variabile
# locale: non c'e' una funzione da sostituire. Si interviene un passo piu'
# avanti, su _mostra_risultati_filtro, che riceve la lista gia' pronta: se
# gli archivi sono stati tagliati fuori, si rifa' la ripartizione.

TETTO = 80
POSTI_ARCHIVI = 24
POSTI_ONLINE = 8


def _e_archivio(v):
    return bool(v.get('_virtuale'))


def _e_online(v):
    return bool(v.get('online'))


def _ripartisci(finali, ricerca):
    """Rifa' la lista tenendo un posto agli archivi e all'online."""
    if not ricerca:
        return finali
    dedup = [v for v in finali if not _e_archivio(v) and not _e_online(v)]
    archivi = [v for v in finali if _e_archivio(v)]
    online = [v for v in finali if _e_online(v)]

    # se archivi/online ci sono gia' in numero decente, non si tocca niente
    if len(dedup) < TETTO or (archivi and online):
        return finali

    riservati = (POSTI_ARCHIVI if archivi else 0) + (POSTI_ONLINE if online else 0)
    nuovi = dedup[:max(0, TETTO - riservati)] + archivi[:POSTI_ARCHIVI] + online[:POSTI_ONLINE]
    return nuovi[:TETTO] if nuovi else finali


try:
    from moduli import libreria_search_mixin as _lsm

    if not getattr(_lsm, '_archivi_sempre_attivo', False):
        _originale = _lsm.LibreriaSearchMixin._mostra_risultati_filtro

        def _mostra_con_archivi(self, finali):
            try:
                # la lista arriva gia' tagliata: se gli archivi sono spariti
                # perche' il disco ha riempito tutto, non c'e' modo di
                # recuperarli qui - li si richiede da capo.
                if finali and not any(_e_archivio(v) for v in finali):
                    testo = ''
                    try:
                        testo = self.entry_filtro.get().strip().lower()
                    except Exception:
                        pass
                    if len(testo) > 1:
                        from .carica_basi import cerca_nei_db
                        gia = set(v.get('nome_lower', '') for v in finali)
                        aggiunti = [r for r in cerca_nei_db(testo, limite=POSTI_ARCHIVI * 2)
                                    if r.get('nome_lower') not in gia][:POSTI_ARCHIVI]
                        if aggiunti:
                            finali = finali[:TETTO - len(aggiunti)] + aggiunti
                finali = _ripartisci(finali, True)
            except Exception as e:
                print("⚠️ patch 015, archivi nei suggerimenti: %s" % e)
            return _originale(self, finali)

        _lsm.LibreriaSearchMixin._mostra_risultati_filtro = _mostra_con_archivi
        _lsm._archivi_sempre_attivo = True
        print("🔎 Suggerimenti: gli archivi compaiono sempre")
except Exception as _e:
    print("⚠️ patch 015, archivi non agganciati: %s" % _e)
