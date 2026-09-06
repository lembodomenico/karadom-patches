# 013_migliorie_settembre.py
#
# UNA PATCH SOLA con tutto il lavoro del 5-6 settembre 2026.
#
#  1. CONTRASTO SUI BOTTONI DEL PLAYER — sul blu notte i bottoni neri
#     sparivano. Il bordo e' un Frame dietro al bottone: puro layout, quindi
#     si vede identico su Windows e Linux.
#     ⚠️ Due strade provate e SCARTATE: colorare lo sfondo (le icone PNG hanno
#     margini trasparenti diversi, il colore traspariva a macchie) e
#     highlightthickness (su Windows Tk non lo disegna affatto).
#
#  2. SUGGERIMENTI PER TIPO — prima gli mp3, poi i video (mp4), poi i midi.
#     ⚠️ Il solo ordine non basta: gli mp3 in archivio sono oltre 14.000 e da
#     soli riempiono il limite, quindi video e midi non si vedrebbero MAI
#     (misurato: "amore" dava 200 risultati su 200 mp3). Ogni tipo ha una
#     fetta garantita: amore -> mp3 x46, video x7, midi x7.
#
#  3. ARCHIVI SEMPRE NEI SUGGERIMENTI — con la cartella mappata ricca, i file
#     su disco riempivano tutti e 80 i posti e i database sparivano. Con 100
#     file su disco: prima disco 80 / archivi 0, ora disco 48 / archivi 24 /
#     online 8.
#
#  4. OROLOGIO CON I SECONDI (Windows e Linux).
#
#  5. SU LINUX VIA LA BARRA TITOLO DISEGNATA DENTRO L'APPLICAZIONE — logo,
#     edizione e versione stanno ora nella barra di sistema; quella dentro
#     l'app era un doppione che rubava sc(26) pixel di altezza.
#
#  6. CARICA BASI AL CONTRARIO — il database e' il DESTINATARIO, non la
#     sorgente: si sceglie una cartella di file e li si archivia dentro.
#     Prima la maschera ESTRAEVA i file dal database. L'estrazione resta dove
#     serve: una base per volta, quando si sceglie un risultato di ricerca.
#
#  7. CARTELLA DEGLI ARCHIVI IMPOSTABILE — bottone "Cartella archivi...".
#     Serviva davvero: i percorsi fissi nel codice (C:\KARAOKE\basi_*.db) non
#     erano quelli dell'installazione vera (C:\KARAOKE\Basi\db).
#     Una cartella impostata vince sulla DESTINAZIONE anche se l'archivio non
#     c'e' ancora; per la LETTURA si ricade sui percorsi noti, cosi'
#     un'impostazione sbagliata non fa sparire un archivio esistente.
#
#  8. FINESTRE PROPORZIONATE COME SU WINDOWS (solo Linux) — le finestre
#     secondarie uscivano piu' larghe. Non era il codice ne' lo scaling
#     (schermo, DPI 120 e scaling Tk 1.6683 erano gia' identici): erano i
#     valori predefiniti di Tk. Il font predefinito e' Segoe UI 9 su Windows
#     e Noto Sans 10 su Linux, e mezza interfaccia e' dimensionata in
#     CARATTERI. Piu' il margine interno dei bottoni, che su X11 e' di 3
#     MILLIMETRI contro 1 pixel.
#     Misurato:            prima      dopo     Windows
#       larghezza di "0"   10 px      8 px      8 px
#       Entry width=20    206 px    166 px    164 px
#       Button width=12   154x39    104x35    106x35

#
#  9. MONITOR PUBBLICO SENZA CONTATORI (Windows e Linux) — orologio, Elapsed,
#     Total, CountDown, Signature e Current servono a chi suona, non a chi
#     guarda. Sul monitor
#     rivolto al pubblico la barra non si mostra piu': la gente deve vedere le
#     parole.
#

#
# 10. PANNELLI DELLA BARRA BASSA IN BLU NOTTE — la 012 aveva colorato le
#     barre, ma i due pannelli al centro (Formato e Prossimo) restavano
#     grigi: #1a1a1a il fondo, #2a2a2a i riquadri. Ora seguono le barre.

#
# 11. SUONI DI SISTEMA SPENTI MENTRE KARADOM E' APERTO (Windows) — il
#     "ding" delle finestre di avviso lo fa Windows, non KaraDom, e in
#     una serata finisce dentro l'impianto. Si spengono all'apertura e si
#     rimettono alla chiusura; se KaraDom si chiude male, al primo avvio
#     successivo si rimettono da soli.

#
# 12. BARRA DEL TITOLO BLU NOTTE (Windows 11) - la caption la disegna
#     Windows, non Tk: restava una fascia chiara in cima a un programma
#     tutto blu notte. Si chiede al gestore delle finestre (DWM).


#
# 14. TONALITA' VERA SUI VIDEO - VLC non sa trasporre (ha solo la
#     velocita'): il fattore dei semitoni finiva dentro set_rate e il
#     video RALLENTAVA senza cambiare tono. Ora l'audio si estrae appena
#     parte il brano e la tonalita' la fa MPV, come sugli mp3.

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


# ==========================================================================
# 6-7. CARICA BASI AL CONTRARIO + CARTELLA ARCHIVI IMPOSTABILE
# ==========================================================================
# Il codice qui sotto e' quello VERO del sorgente aggiornato, non una
# riscrittura: si esegue dentro il namespace del modulo carica_basi del
# cliente, cosi' i nomi che usa (_, S, F, _CANDIDATI, filedialog, sqlite3,
# threading, _destinazione_estrazione_predefinita...) si risolvono da soli.

_CARICA_BASI_NUOVO = r'''
# Chiave di configurazione con la cartella scelta dall'utente per gli
# archivi. Se c'e', vince sui percorsi predefiniti qui sopra: gli archivi
# possono stare su un disco esterno, su una share di rete o dove si vuole,
# senza dover toccare il codice.
CONFIG_CARTELLA_ARCHIVI = 'cartella_archivi_basi'


def cartella_archivi():
    """Cartella degli archivi impostata dall'utente, o '' se non impostata."""
    try:
        from .database import Database
        d = Database.get_config(CONFIG_CARTELLA_ARCHIVI, '')
        if d and os.path.isdir(d):
            return os.path.normpath(d)
    except Exception:
        pass
    return ""


def imposta_cartella_archivi(cartella):
    """Salva la cartella degli archivi. Passare '' per tornare ai percorsi
    predefiniti. Il percorso si normalizza: su Windows la finestra di scelta
    restituisce barre in avanti ("C:/KARAOKE") che poi si mescolano con quelle
    rovesce aggiunte da os.path.join."""
    from .database import Database
    Database.set_config(CONFIG_CARTELLA_ARCHIVI,
                        os.path.normpath(cartella) if cartella else '')


def _trova_candidato(chiave):
    # 1) la cartella scelta dall'utente, se contiene l'archivio
    d = cartella_archivi()
    if d:
        p = os.path.join(d, 'basi_%s.db' % chiave)
        if os.path.exists(p):
            return p
    # 2) i percorsi predefiniti
    for p in _CANDIDATI.get(chiave, []):
        if os.path.exists(p):
            return p
    return ""


def _percorso_predefinito(chiave):
    """Dove si CREEREBBE l'archivio se non esiste: nella cartella scelta
    dall'utente, se impostata, altrimenti nel primo percorso predefinito."""
    d = cartella_archivi()
    if d:
        return os.path.join(d, 'basi_%s.db' % chiave)
    return (_CANDIDATI.get(chiave) or [''])[0]


def db_disponibili():
    """{chiave: path} dei DB trovati nei percorsi noti (mp3/video/midi)."""
    trovati = {}
    for chiave in _CANDIDATI:
        p = _trova_candidato(chiave)
        if p:
            trovati[chiave] = p
    return trovati


# Tipo MIME per estensione: si scrive nel database accanto ai dati, come
# faceva chi ha creato gli archivi esistenti.
_MIME = {
    'mp3': 'audio/mpeg', 'wav': 'audio/wav', 'm4a': 'audio/mp4',
    'flac': 'audio/flac', 'ogg': 'audio/ogg', 'wma': 'audio/x-ms-wma',
    'mp4': 'video/mp4', 'mkv': 'video/x-matroska', 'avi': 'video/x-msvideo',
    'mov': 'video/quicktime', 'webm': 'video/webm', 'mpg': 'video/mpeg',
    'mpeg': 'video/mpeg', 'm4v': 'video/x-m4v', 'wmv': 'video/x-ms-wmv',
    'mid': 'audio/midi', 'midi': 'audio/midi', 'kar': 'audio/midi',
}


def _artista_titolo_da_nome(nome_file):
    """Ricava artista e titolo dal nome, con la convenzione usata negli
    archivi esistenti: "Artista - Titolo.ext". Senza il trattino, tutto il
    nome finisce nel titolo e l'artista resta vuoto: meglio un campo vuoto
    che un artista inventato, perche' la ricerca cerca in tutti e tre i campi
    (artista, titolo, file_nome) e il brano si trova lo stesso."""
    base = os.path.splitext(nome_file)[0].strip()
    if ' - ' in base:
        artista, titolo = base.split(' - ', 1)
        return artista.strip(), titolo.strip()
    return '', base


class CaricaBasiWindow:
    """Mette le basi DENTRO il database: si sceglie una cartella di file e li
    si carica in basi_mp3.db / basi_video.db / basi_midi.db.

    ⛔ Prima faceva il contrario (database -> cartella, estraeva i file): era
    il verso sbagliato. Il database e' il DESTINATARIO dell'archiviazione, non
    la sorgente. L'estrazione di una singola base resta dove serve davvero -
    quando si sceglie un risultato di ricerca (estrai_una_base).
    """

    # Estensioni proposte in base all'archivio scelto. Non e' un divieto: e'
    # il filtro predefinito, che si puo' svuotare per caricare qualunque cosa.
    COLORE_ACCESO = '#0078D7'      # l'archivio scelto
    COLORE_SPENTO = '#3a3d44'      # gli altri due

    ESTENSIONI = {
        'mp3':   '.mp3 .wav .m4a .flac .ogg .wma',
        'video': '.mp4 .mkv .avi .mov .webm .mpg .mpeg .m4v .wmv',
        'midi':  '.mid .midi .kar',
    }

    def __init__(self, parent):
        self.win = tk.Toplevel(parent)
        self.win.title(_("Carica basi nel database"))
        self.win.configure(bg='#1e2024')
        self.win.geometry(f"{S(620)}x{S(420)}")
        self.win.transient(parent)
        self._ferma = False

        pad = {'padx': S(16), 'pady': S(6)}

        # ---------- SORGENTE: la cartella con i file ----------
        tk.Label(self.win, text=_("Cartella con le basi da caricare"),
                 bg='#1e2024', fg='#ffffff', font=F('Segoe UI', 11, 'bold')
                 ).pack(anchor='w', **pad)

        src_row = tk.Frame(self.win, bg='#1e2024')
        src_row.pack(fill='x', padx=S(16), pady=(0, S(4)))
        self.src_var = tk.StringVar(value=_destinazione_estrazione_predefinita())
        tk.Entry(src_row, textvariable=self.src_var, bg='#2a2d33', fg='white',
                 insertbackground='white').pack(side='left', fill='x', expand=True)
        tk.Button(src_row, text=_("Sfoglia..."), command=self._sfoglia_cartella,
                  bg='#3a3d44', fg='white', relief='flat', cursor='hand2').pack(side='left', padx=(S(6), 0))

        self.sub_var = tk.BooleanVar(value=True)
        tk.Checkbutton(self.win, text=_("Includi anche le sottocartelle"),
                       variable=self.sub_var, bg='#1e2024', fg='#cccccc',
                       selectcolor='#1e2024', activebackground='#1e2024',
                       activeforeground='#ffffff').pack(anchor='w', padx=S(16))

        # ---------- DESTINAZIONE: il database ----------
        tk.Label(self.win, text=_("Database di destinazione"),
                 bg='#1e2024', fg='#ffffff', font=F('Segoe UI', 11, 'bold')
                 ).pack(anchor='w', **pad)

        # Bastano i tre bottoni: il percorso di ciascun archivio e' sempre lo
        # stesso, quindi un campo da riempire a mano sarebbe solo una riga in
        # piu' da leggere. Sotto resta scritto DOVE si sta caricando, che e'
        # l'unica informazione che serve davvero.
        btn_row = tk.Frame(self.win, bg='#1e2024')
        btn_row.pack(fill='x', padx=S(16))
        self.btn_archivi = {}
        for chiave, etichetta in (('mp3', _("MP3 (audio)")), ('video', _("Video")), ('midi', _("MIDI"))):
            b = tk.Button(btn_row, text=etichetta, relief='flat', cursor='hand2',
                          fg='white', bg=self.COLORE_SPENTO,
                          command=lambda c=chiave: self._scegli_nota(c))
            b.pack(side='left', padx=(0, S(6)))
            self.btn_archivi[chiave] = b

        # Dove stanno gli archivi si puo' cambiare: possono essere su un disco
        # esterno, su una cartella di rete o dove si vuole. La scelta si
        # ricorda, quindi si fa una volta sola.
        tk.Button(btn_row, text=_("Cartella archivi..."), relief='flat',
                  cursor='hand2', fg='white', bg='#5a4b8a',
                  command=self._cambia_cartella_archivi).pack(side='right')

        self.dst_var = tk.StringVar(value=_trova_candidato('mp3'))
        self.dst_label = tk.Label(self.win, text="", bg='#1e2024', fg='#8a93a6',
                                  font=F('Segoe UI', 9), anchor='w')
        self.dst_label.pack(fill='x', padx=S(16), pady=(S(6), S(2)))

        # ---------- filtro sulle estensioni ----------
        ext_row = tk.Frame(self.win, bg='#1e2024')
        ext_row.pack(fill='x', padx=S(16), pady=(S(4), 0))
        tk.Label(ext_row, text=_("Estensioni (vuoto = tutte):"), bg='#1e2024',
                 fg='#cccccc', font=F('Segoe UI', 9)).pack(side='left')
        self.ext_var = tk.StringVar(value=self.ESTENSIONI['mp3'])
        tk.Entry(ext_row, textvariable=self.ext_var, bg='#2a2d33', fg='white',
                 insertbackground='white', width=40).pack(side='left', padx=(S(6), 0), fill='x', expand=True)

        self.skip_var = tk.BooleanVar(value=True)
        tk.Checkbutton(self.win, text=_("Salta le basi già presenti nel database"),
                       variable=self.skip_var, bg='#1e2024', fg='#cccccc',
                       selectcolor='#1e2024', activebackground='#1e2024',
                       activeforeground='#ffffff').pack(anchor='w', padx=S(16), pady=(S(4), 0))

        self.progress = ttk.Progressbar(self.win, mode='determinate')
        self.progress.pack(fill='x', padx=S(16), pady=(S(12), S(4)))

        self.status_label = tk.Label(self.win, text="", bg='#1e2024', fg='#aaaaaa',
                                      font=F('Segoe UI', 9))
        self.status_label.pack(anchor='w', padx=S(16))

        actions = tk.Frame(self.win, bg='#1e2024')
        actions.pack(fill='x', padx=S(16), pady=S(14))
        self.load_btn = tk.Button(actions, text=_("Carica"), command=self._avvia_caricamento,
                                  bg='#28a745', fg='white', relief='flat', cursor='hand2',
                                  font=F('Segoe UI', 10, 'bold'), width=12)
        self.load_btn.pack(side='left')
        self.stop_btn = tk.Button(actions, text=_("Ferma"), command=self._chiedi_stop,
                                  bg='#dc3545', fg='white', relief='flat', cursor='hand2',
                                  width=10, state='disabled')
        self.stop_btn.pack(side='left', padx=(S(8), 0))
        tk.Button(actions, text=_("Chiudi"), command=self.win.destroy,
                  bg='#6c757d', fg='white', relief='flat', cursor='hand2', width=12
                  ).pack(side='right')

        # si parte con MP3 gia' scelto: bottone acceso e percorso scritto sotto
        self._scegli_nota('mp3')

    # ---------- helper ----------
    def _scegli_nota(self, chiave):
        """Sceglie l'archivio di destinazione. Il percorso non si scrive a
        mano: e' sempre lo stesso per ciascuna delle tre famiglie, quindi un
        campo da riempire sarebbe solo una riga in piu' da leggere."""
        self.scelta = chiave
        self.ext_var.set(self.ESTENSIONI.get(chiave, ''))

        # Una cartella scelta dall'utente vince sempre: e' li' che vuole i
        # suoi archivi, esistano gia' o no.
        scelta_utente = cartella_archivi()
        trovato = _trova_candidato(chiave)
        if scelta_utente:
            percorso = _percorso_predefinito(chiave)
            self.dst_var.set(percorso)
            if os.path.exists(percorso):
                nota = _("Le basi verranno caricate in:  {p}").format(p=percorso)
            else:
                nota = _("Archivio nuovo, verrà creato in:  {p}").format(p=percorso)
        elif trovato:
            self.dst_var.set(trovato)
            nota = _("Le basi verranno caricate in:  {p}").format(p=trovato)
        else:
            # L'archivio puo' non esistere ancora: lo si crea al primo
            # caricamento, invece di limitarsi a dire che non c'e'.
            preferito = _percorso_predefinito(chiave)
            self.dst_var.set(preferito)
            nota = _("Archivio nuovo, verrà creato in:  {p}").format(p=preferito)

        self.dst_label.config(text=nota)
        for c, b in self.btn_archivi.items():
            b.config(bg=self.COLORE_ACCESO if c == chiave else self.COLORE_SPENTO)


    def _cambia_cartella_archivi(self):
        """Sceglie la cartella dove stanno (o staranno) i tre archivi.
        Cambiarla vale per tutto KaraDom, ricerca compresa: e' la stessa
        cartella che cerca_nei_db interroga."""
        attuale = cartella_archivi() or os.path.dirname(self.dst_var.get() or '') or None
        d = filedialog.askdirectory(
            title=_("Cartella dove tenere gli archivi delle basi"),
            initialdir=attuale, parent=self.win)
        if not d:
            return
        try:
            imposta_cartella_archivi(d)
        except Exception as e:
            messagebox.showerror(_("Errore"), str(e), parent=self.win)
            return
        # si riapplica la scelta corrente, cosi' percorso e scritta si aggiornano
        self._scegli_nota(getattr(self, 'scelta', 'mp3'))
        presenti = [k for k in ('mp3', 'video', 'midi') if _trova_candidato(k)]
        if presenti:
            messaggio = _("Cartella impostata:\n{d}\n\nArchivi trovati: {a}").format(
                d=d, a=", ".join(presenti))
        else:
            messaggio = _("Cartella impostata:\n{d}\n\nNon contiene ancora nessun "
                          "archivio: verranno creati qui al primo caricamento.").format(d=d)
        messagebox.showinfo(_("Cartella archivi"), messaggio, parent=self.win)

    def _sfoglia_cartella(self):
        d = filedialog.askdirectory(title=_("Scegli la cartella con le basi"), parent=self.win)
        if d:
            self.src_var.set(d)

    def _chiedi_stop(self):
        self._ferma = True
        self.status_label.config(text=_("Interruzione in corso..."))

    # ---------- caricamento ----------
    def _avvia_caricamento(self):
        src = self.src_var.get().strip()
        dst = self.dst_var.get().strip()
        if not src or not os.path.isdir(src):
            messagebox.showerror(_("Errore"), _("Cartella non trovata:\n{p}").format(p=src), parent=self.win)
            return
        if not dst:
            messagebox.showerror(_("Errore"), _("Scegli il database di destinazione."), parent=self.win)
            return
        try:
            os.makedirs(os.path.dirname(dst) or '.', exist_ok=True)
        except Exception as e:
            messagebox.showerror(_("Errore"), str(e), parent=self.win)
            return

        estensioni = tuple(e.strip().lower() for e in self.ext_var.get().replace(',', ' ').split() if e.strip())
        self._ferma = False
        self.load_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        threading.Thread(target=self._carica_worker,
                         args=(src, dst, self.sub_var.get(), estensioni, self.skip_var.get()),
                         daemon=True).start()

    def _elenca_file(self, cartella, sottocartelle, estensioni):
        trovati = []
        if sottocartelle:
            for radice, _dirs, files in os.walk(cartella):
                for n in files:
                    trovati.append(os.path.join(radice, n))
        else:
            for n in os.listdir(cartella):
                p = os.path.join(cartella, n)
                if os.path.isfile(p):
                    trovati.append(p)
        if estensioni:
            trovati = [p for p in trovati if os.path.splitext(p)[1].lower() in estensioni]
        return sorted(trovati)

    def _carica_worker(self, src, dst, sottocartelle, estensioni, salta_presenti):
        con = None
        try:
            self._stato(_("Cerco i file..."))
            file_da_caricare = self._elenca_file(src, sottocartelle, estensioni)
            totale = len(file_da_caricare)
            if not totale:
                self.win.after(0, lambda: messagebox.showinfo(
                    _("Niente da caricare"),
                    _("Nessun file da caricare in quella cartella."), parent=self.win))
                self.win.after(0, self._riabilita)
                return
            self.win.after(0, lambda: self.progress.config(maximum=totale, value=0))

            con = sqlite3.connect(dst)
            # La tabella si crea se il database e' nuovo: cosi' si puo'
            # cominciare un archivio da zero senza preparare niente a mano.
            con.execute("""
                CREATE TABLE IF NOT EXISTS basi (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    artista    TEXT DEFAULT '',
                    titolo     TEXT DEFAULT '',
                    file_nome  TEXT NOT NULL,
                    percorso   TEXT UNIQUE NOT NULL,
                    tipo       TEXT DEFAULT '',
                    dimensione INTEGER DEFAULT 0,
                    mime       TEXT DEFAULT '',
                    dati       BLOB NOT NULL,
                    creato     TEXT DEFAULT CURRENT_TIMESTAMP
                )""")
            con.commit()

            gia_dentro = set()
            if salta_presenti:
                try:
                    gia_dentro = set(r[0] for r in con.execute("SELECT percorso FROM basi"))
                except Exception:
                    gia_dentro = set()

            caricati = saltati = errori = 0
            for i, percorso in enumerate(file_da_caricare, 1):
                if self._ferma:
                    break
                nome = os.path.basename(percorso)
                chiave = os.path.relpath(percorso, src).replace('\\', '/')
                try:
                    if salta_presenti and chiave in gia_dentro:
                        saltati += 1
                    else:
                        with open(percorso, 'rb') as f:
                            dati = f.read()
                        artista, titolo = _artista_titolo_da_nome(nome)
                        ext = os.path.splitext(nome)[1].lower().lstrip('.')
                        con.execute(
                            "INSERT OR IGNORE INTO basi "
                            "(artista, titolo, file_nome, percorso, tipo, dimensione, mime, dati) "
                            "VALUES (?,?,?,?,?,?,?,?)",
                            (artista, titolo, nome, chiave, ext, len(dati),
                             _MIME.get(ext, 'application/octet-stream'), dati))
                        caricati += 1
                        gia_dentro.add(chiave)
                except Exception as e:
                    errori += 1
                    print(f"⚠️ Carica basi: errore su {nome}: {e}")

                # si salva ogni tanto: se si interrompe, il lavoro fatto resta
                if i % 25 == 0:
                    con.commit()
                    self._aggiorna_stato(i, totale, caricati, saltati, errori)
            con.commit()
            self._aggiorna_stato(min(i, totale), totale, caricati, saltati, errori)
            con.close()
            con = None
            self.win.after(0, lambda: self._fine(caricati, saltati, errori, self._ferma))
        except Exception as e:
            msg = str(e)
            self.win.after(0, lambda: messagebox.showerror(_("Errore"), msg, parent=self.win))
            self.win.after(0, self._riabilita)
        finally:
            if con is not None:
                try:
                    con.commit(); con.close()
                except Exception:
                    pass

    def _stato(self, testo):
        self.win.after(0, lambda: self.status_label.config(text=testo))

    def _aggiorna_stato(self, i, totale, caricati, saltati, errori):
        def _upd():
            self.progress['value'] = i
            self.status_label.config(
                text=f"{i}/{totale} — caricati {caricati}, saltati {saltati}, errori {errori}")
        self.win.after(0, _upd)

    def _riabilita(self):
        self.load_btn.config(state='normal')
        self.stop_btn.config(state='disabled')

    def _fine(self, caricati, saltati, errori, interrotto):
        self._riabilita()
        titolo = _("Caricamento interrotto") if interrotto else _("Caricamento completato")
        messagebox.showinfo(
            titolo,
            _("Caricati nel database: {c}\nGià presenti (saltati): {s}\nErrori: {r}")
            .format(c=caricati, s=saltati, r=errori),
            parent=self.win)
'''

try:
    from moduli import carica_basi as _cb

    if not getattr(_cb, '_finestra_girata', False):
        exec(compile(_CARICA_BASI_NUOVO, '<patch 013 carica_basi>', 'exec'), _cb.__dict__)
        _cb._finestra_girata = True
        print("\U0001F4E5 Carica basi: ora il database e' la destinazione, non la sorgente")
except Exception as _e:
    print("\u26A0\uFE0F patch 013, Carica basi non aggiornata: %s" % _e)


# ==========================================================================
# 8. FINESTRE PROPORZIONATE COME SU WINDOWS (solo Linux)
# ==========================================================================
if sys.platform.startswith('linux'):
    try:
        import tkinter as tk
        import tkinter.font as _tkfont

        for _nome in ('TkDefaultFont', 'TkTextFont', 'TkMenuFont', 'TkHeadingFont',
                      'TkCaptionFont', 'TkSmallCaptionFont', 'TkIconFont', 'TkTooltipFont'):
            try:
                _tkfont.nametofont(_nome).configure(family='Selawik', size=9)
            except Exception:
                pass

        # il margine interno dei bottoni: 3 MILLIMETRI su X11, 1 pixel su
        # Windows. Solo l'orizzontale: toccando anche il verticale l'altezza
        # scendeva a 27 px contro i 35 di Windows.
        _radice = tk._default_root
        if _radice is not None:
            _radice.option_add('*Button.padX', 1)
        print("\U0001F4D0 Finestre: font e margini allineati a Windows")
    except Exception as _e:
        print("\u26A0\uFE0F patch 013, proporzioni non allineate: %s" % _e)


# ==========================================================================
# 9. MONITOR PUBBLICO SENZA OROLOGIO E CONTATORI
# ==========================================================================
# La barra con orologio, Elapsed, Total, CountDown, Signature e Current viene
# creata dalla STESSA classe sia per la finestra di chi suona sia per il
# monitor rivolto al pubblico (cambia solo monitor_type). Sul pubblico non
# c'entra niente: si toglie dal layout.
#
# I widget continuano a esistere: decine di punti del codice ci scrivono
# dentro, e non crearli vorrebbe dire rincorrere ogni singolo uso.

try:
    from moduli import monitor as _mon

    if not getattr(_mon.KaraokeMonitor, '_barra_via_dal_pubblico', False):
        _crea_originale = _mon.KaraokeMonitor._create_widgets

        def _crea_senza_barra(self, _orig=_crea_originale):
            _orig(self)
            try:
                # Su OGNI piattaforma: quella barra serve a chi suona, non a
                # chi guarda. Sullo schermo del pubblico ci devono essere le
                # parole, non l'orologio.
                if getattr(self, 'monitor_type', 'main') == 'pub':
                    self.info_bar.pack_forget()
            except Exception:
                pass

        _mon.KaraokeMonitor._create_widgets = _crea_senza_barra

        # Uscendo dalla modalita' espansa la barra veniva ri-aggiunta al
        # layout: sul monitor pubblico sarebbe riapparsa.
        _exp_originale = getattr(_mon.KaraokeMonitor, 'toggle_expanded', None)
        if _exp_originale is not None:

            def _toggle_expanded_senza_barra(self, *a, **kw):
                r = _exp_originale(self, *a, **kw)
                try:
                    if getattr(self, 'monitor_type', 'main') == 'pub':
                        self.info_bar.pack_forget()
                except Exception:
                    pass
                return r

            _mon.KaraokeMonitor.toggle_expanded = _toggle_expanded_senza_barra

        _mon.KaraokeMonitor._barra_via_dal_pubblico = True
        print("\U0001F4FA Monitor pubblico: via orologio e contatori")
except Exception as _e:
    print("\u26A0\uFE0F patch 013, barra del monitor pubblico non tolta: %s" % _e)


# ==========================================================================
# 10. PANNELLI DELLA BARRA BASSA IN BLU NOTTE
# ==========================================================================
# La 012 ha portato al blu notte la barra dei menu e quella delle icone, ma i
# due pannelli al centro della barra bassa (quello con Cantante/Brano e
# "Formato", e quello di "Prossimo") erano rimasti grigi.
#
# Si interviene sulla creazione dei widget: quando nasce un Frame o una Label
# con lo sfondo grigio dei pannelli, gli si mette il colore giusto. Non serve
# sapere dove sono nel codice ne' quanti sono.

_GRIGIO_FONDO = '#1a1a1a'
_GRIGIO_BOX = '#2a2a2a'
_GRIGIO_BARRA = '#2b2b2b'      # il fondo vero della barra bassa (misurato)
_GRIGI_BOTTONE = ('#333', '#333333')
_BLU_FONDO = '#060c1c'
_BLU_BOX = '#132038'

try:
    import tkinter as tk

    if not getattr(tk.Frame, '_pannelli_blu_notte', False):

        def _e_blu(master):
            """Vero se il contenitore e' la finestra principale o e' gia' blu
            notte. Serve a NON toccare mixer, sampler e overlay: usano lo
            stesso grigio ma vivono in finestre loro, e li' ci sta bene."""
            try:
                if isinstance(master, tk.Tk):
                    return True
                return str(master.cget('bg')).lower() in (_BLU_FONDO, _BLU_BOX)
            except Exception:
                return False

        def _colore_giusto(master, kw):
            sfondo = str(kw.get('bg', kw.get('background', ''))).lower()
            if sfondo == _GRIGIO_FONDO:
                return _BLU_FONDO
            if sfondo == _GRIGIO_BOX:
                return _BLU_BOX
            if sfondo == _GRIGIO_BARRA and _e_blu(master):
                return _BLU_FONDO
            # NB: i bottoni restano col fondo NERO. Provato a portarli al blu
            # notte: sparivano dentro la barra, il contrasto serve.
            if sfondo in _GRIGI_BOTTONE and _e_blu(master):
                return _BLU_BOX
            return None

        for _classe in (tk.Frame, tk.Label, tk.Button):
            _init_originale = _classe.__init__

            def _init_blu(self, master=None, _orig=_init_originale, **kw):
                # fg_mimetico: alcune scritte sono volutamente INVISIBILI,
                # dello stesso colore del fondo, e servono solo da spaziatore
                # (la seconda nota musicale della barra bassa). Se si cambia
                # il fondo e non il testo, saltano fuori.
                for _c in ('fg', 'foreground'):
                    if str(kw.get(_c, '')).lower() in (_GRIGIO_BARRA, _GRIGIO_BOX):
                        kw[_c] = _BLU_FONDO
                nuovo = _colore_giusto(master, kw)
                if nuovo:
                    if 'bg' in kw:
                        kw['bg'] = nuovo
                    if 'background' in kw:
                        kw['background'] = nuovo
                _orig(self, master, **kw)

            _classe.__init__ = _init_blu

        # I due pannelli al centro sono GlowPanel: Canvas che RIDISEGNANO il
        # fondo con il colore tenuto in self.inner. Cambiare solo il Frame
        # interno non basta, al primo ridisegno tornerebbe grigio.
        try:
            from moduli import glow_panel as _gp
            if not getattr(_gp.GlowPanel, '_blu_notte', False):
                _glow_init = _gp.GlowPanel.__init__

                def _glow_blu(self, master, *a, **kw):
                    dentro = str(kw.get('inner', '')).lower()
                    if dentro in (_GRIGIO_FONDO, _GRIGIO_BARRA):
                        kw['inner'] = _BLU_FONDO
                    elif dentro == _GRIGIO_BOX:
                        kw['inner'] = _BLU_BOX
                    _glow_init(self, master, *a, **kw)

                _gp.GlowPanel.__init__ = _glow_blu
                _gp.GlowPanel._blu_notte = True
        except Exception:
            pass

        tk.Frame._pannelli_blu_notte = True
        print("🌑 Barra bassa: blu notte")
except Exception as _e:
    print("⚠️ patch 013, pannelli non ricolorati: %s" % _e)


# ==========================================================================
# 11. SUONI DI SISTEMA SPENTI MENTRE KARADOM E' APERTO (solo Windows)
# ==========================================================================
# Le finestre di messaggio, su Windows, sono finestre del SISTEMA: il "ding"
# lo fa Windows e non c'e' nessuna opzione per zittirlo dal programma.
#
# Si spegne il suono dei soli eventi di avviso all'apertura e lo si rimette
# alla chiusura. Il resto del computer non viene toccato.
#
# ⚠️ Se KaraDom si chiude male i suoni resterebbero spenti: per questo i
# valori di partenza si scrivono in un file, e al primo avvio successivo si
# rimette tutto prima di rispegnere.

_SUONI_SISTEMA = r'''
import json
import os
import sys

# Gli eventi che suonano nelle finestre di dialogo e negli avvisi. Non si
# tocca tutto lo schema dei suoni: solo questi.
_EVENTI = (
    'SystemAsterisk',        # avviso / informazione
    'SystemExclamation',     # attenzione
    'SystemHand',            # errore grave
    'SystemQuestion',        # domanda
    'SystemNotification',    # notifica
    'SystemDefault',         # il "beep" generico
    'MenuCommand',
    'MenuPopup',
    'Open',
    'Close',
    'MailBeep',
    'AppGPFault',
)

_CHIAVE = r'AppEvents\Schemes\Apps\.Default'


def _file_ripristino():
    base = os.environ.get('LOCALAPPDATA') or os.path.expanduser('~')
    return os.path.join(base, 'KaraDom', 'suoni_da_rimettere.json')


def _attivo():
    return os.name == 'nt' and sys.platform.startswith('win')


def _leggi_e_svuota(winreg, evento, salvati):
    """Legge il suono di un evento e lo svuota. Torna True se ha cambiato."""
    percorso = '%s\\%s\\.Current' % (_CHIAVE, evento)
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, percorso, 0,
                            winreg.KEY_READ | winreg.KEY_WRITE) as k:
            try:
                valore, tipo = winreg.QueryValueEx(k, '')
            except FileNotFoundError:
                return False
            if not valore:                      # gia' muto
                return False
            salvati[evento] = {'v': valore, 't': tipo}
            winreg.SetValueEx(k, '', 0, tipo, '')
            return True
    except FileNotFoundError:
        return False                            # evento non presente su questo PC
    except Exception:
        return False


def spegni():
    """Spegne i suoni di sistema degli avvisi. Torna quanti ne ha spenti."""
    if not _attivo():
        return 0
    import winreg

    # Se c'e' un file di ripristino, l'ultima chiusura e' andata male:
    # prima si rimette tutto a posto, poi si riparte da capo.
    rimetti()

    salvati = {}
    for evento in _EVENTI:
        _leggi_e_svuota(winreg, evento, salvati)

    if not salvati:
        return 0

    percorso = _file_ripristino()
    try:
        os.makedirs(os.path.dirname(percorso), exist_ok=True)
        with open(percorso, 'w', encoding='utf-8') as f:
            json.dump(salvati, f)
    except Exception as e:
        # senza il file non si potrebbe rimettere a posto dopo un crash:
        # meglio rinunciare che lasciare il computer muto per sempre
        print('⚠️ Suoni di sistema: non riesco a salvare il ripristino (%s)' % e)
        rimetti_da(salvati)
        return 0

    _avvisa_windows()
    return len(salvati)


def rimetti_da(salvati):
    """Rimette i suoni indicati."""
    if not _attivo() or not salvati:
        return 0
    import winreg
    rimessi = 0
    for evento, dati in salvati.items():
        percorso = '%s\\%s\\.Current' % (_CHIAVE, evento)
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, percorso, 0,
                                winreg.KEY_WRITE) as k:
                winreg.SetValueEx(k, '', 0, dati.get('t', winreg.REG_EXPAND_SZ),
                                  dati.get('v', ''))
                rimessi += 1
        except Exception:
            pass
    _avvisa_windows()
    return rimessi


def rimetti():
    """Rimette i suoni salvati e cancella il file di ripristino."""
    if not _attivo():
        return 0
    percorso = _file_ripristino()
    if not os.path.exists(percorso):
        return 0
    try:
        with open(percorso, encoding='utf-8') as f:
            salvati = json.load(f)
    except Exception:
        salvati = {}
    n = rimetti_da(salvati)
    try:
        os.remove(percorso)
    except Exception:
        pass
    return n


def _avvisa_windows():
    """Dice a Windows di rileggere le impostazioni: senza, i programmi gia'
    aperti continuano a usare i suoni di prima."""
    try:
        import ctypes
        # SPI_SETSOUNDSENTRY non serve: basta la notifica di cambio impostazioni
        ctypes.windll.user32.SendMessageTimeoutW(
            0xFFFF,      # HWND_BROADCAST
            0x001A,      # WM_SETTINGCHANGE
            0, 0, 0x0002, 200, None)
    except Exception:
        pass
'''

if sys.platform.startswith('win'):
    try:
        _ns_suoni = {}
        exec(compile(_SUONI_SISTEMA, '<patch 013 suoni>', 'exec'), _ns_suoni)
        _n = _ns_suoni['spegni']()
        if _n:
            print("\U0001F507 Suoni di sistema spenti (%d), si rimettono alla chiusura" % _n)

        # il ripristino si aggancia alla chiusura della finestra principale
        import atexit
        atexit.register(_ns_suoni['rimetti'])
    except Exception as _e:
        print("\u26A0\uFE0F patch 013, suoni di sistema non spenti: %s" % _e)


# ==========================================================================
# 12. BARRA DEL TITOLO BLU NOTTE (solo Windows 11)
# ==========================================================================
# La barra del titolo non la disegna Tk ma il gestore delle finestre: nessuna
# opzione di tkinter la tocca. Tutto il resto di KaraDom e' blu notte e quella
# fascia chiara restava in cima come la riga di un altro programma.
#
# Su Windows 10 e su Linux la chiamata non fa niente e si tira dritto.

try:
    import tkinter as _tkT

    if sys.platform.startswith('win') and not getattr(_tkT.Tk, '_titolo_blu_notte', False):

        def _colora_titolo(win, colore='#060c1c', testo='#ffffff'):
            try:
                import ctypes
                win.update_idletasks()
                hwnd = int(win.wm_frame(), 16)

                def _colorref(esa):
                    # Windows vuole i byte al contrario: 0x00BBGGRR
                    r, g, b = (int(esa[i:i + 2], 16) for i in (1, 3, 5))
                    return ctypes.c_int((b << 16) | (g << 8) | r)

                dwm = ctypes.windll.dwmapi
                dwm.DwmSetWindowAttribute(hwnd, 35, ctypes.byref(_colorref(colore)), 4)
                dwm.DwmSetWindowAttribute(hwnd, 36, ctypes.byref(_colorref(testo)), 4)
            except Exception:
                pass

        for _cls in (_tkT.Tk, _tkT.Toplevel):
            _vecchio = _cls.__init__

            def _nuovo(self, *a, _orig=_vecchio, **kw):
                _orig(self, *a, **kw)
                # non subito: la finestra deve esistere per il gestore
                try:
                    self.after(400, lambda: _colora_titolo(self))
                except Exception:
                    pass

            _cls.__init__ = _nuovo

        _tkT.Tk._titolo_blu_notte = True
        print("🌑 Barra del titolo: blu notte")
except Exception as _e:
    print("⚠️ patch 013, barra del titolo non colorata: %s" % _e)


# ==========================================================================
# 13. LO SPLASH DELLA PROVA STA DENTRO LO SCHERMO
# ==========================================================================
# La finestra di attivazione era alta 880 px fissi. Su un portatile 1366x768
# lo schermo ne ha 768: il fondo della finestra — dove stanno il bottone della
# prova e il campo del codice licenza — restava sotto il bordo e non si poteva
# raggiungere. Chi non aveva la licenza non riusciva nemmeno a partire.
#
# Qui la finestra non supera mai lo spazio disponibile e il contenuto si
# STRINGE per starci: prima si toglie il vuoto fra i campi, poi, solo se
# serve ancora, si rimpicciolisce il logo (il piu' grande che ci sta).
# Niente barra di scorrimento: si deve vedere tutto subito.
#
# Nella stessa finestra il seriale era scritto in verde acceso su fondo
# chiaro: va letto e ricopiato al telefono, quindi diventa bianco, grassetto
# e a spaziatura fissa (0 e O, 1 e I non si confondono).

try:
    import tkinter as _tkS
    from moduli import splash as _spl

    if not getattr(_spl.SplashScreen, '_finestra_adattata', False):

        def _kd_alta(w):
            # SOLO winfo_reqheight: sommare y+altezza dei figli non funziona,
            # il footer e' ancorato in basso e falsa il conto.
            w.update_idletasks()
            return w.winfo_reqheight()

        def _kd_stringi_spazi(w, fattore):
            for c in w.winfo_children():
                try:
                    info = c.pack_info()
                except Exception:
                    info = None
                if info:
                    nuovo = {}
                    for chiave in ('pady', 'ipady'):
                        v = info.get(chiave)
                        if isinstance(v, (tuple, list)):
                            nuovo[chiave] = tuple(int(int(x) * fattore) for x in v)
                        elif v not in (None, '', 0, '0'):
                            nuovo[chiave] = int(int(v) * fattore)
                    if nuovo:
                        c.pack_configure(**nuovo)
                try:
                    if int(c.cget('pady') or 0) > 2:
                        c.configure(pady=max(2, int(int(c.cget('pady')) * fattore)))
                except Exception:
                    pass
                _kd_stringi_spazi(c, fattore)

        def _kd_logo(w, quota, percorso=None):
            for c in w.winfo_children():
                try:
                    if c.cget('image'):
                        from PIL import Image, ImageTk
                        p = percorso or getattr(c, '_kd_logo_path', None)
                        if p:
                            img = Image.open(p)
                            img.thumbnail((10000, quota), Image.Resampling.LANCZOS)
                            nuova = ImageTk.PhotoImage(img)
                            c.configure(image=nuova)
                            c.image = nuova
                            return True
                except Exception:
                    pass
                if _kd_logo(c, quota, percorso):
                    return True
            return False

        def _kd_respira(w, avanzo):
            """Un po' d'aria in cima: i campi non partono incollati al logo."""
            if avanzo < 12:
                return
            for c in w.winfo_children():
                try:
                    info = c.pack_info()
                except Exception:
                    continue
                if info.get('side') in (None, '', 'top'):
                    v = info.get('pady', 0)
                    base = int(v[0]) if isinstance(v, (tuple, list)) else int(v or 0)
                    c.pack_configure(pady=(base + min(int(avanzo / 3), 20), base))
                    return

        _crea_orig_splash = _spl.SplashScreen._create_widgets
        _init_orig_splash = _spl.SplashScreen.__init__

        def _create_widgets_adattato(self, _orig=_crea_orig_splash):
            _orig(self)

            # il seriale, leggibile
            try:
                self.entry_serial.configure(fg='#ffffff',
                                            readonlybackground='#2d2d44',
                                            font=('Consolas', 12, 'bold'))
            except Exception:
                pass

            try:
                r = self.root
                libera = r.winfo_screenheight() - 80
                voluta = _kd_alta(r)
                reale = max(420, min(voluta, libera))
                self._kd_h_reale = reale

                if voluta > reale - 16:
                    percorso = None
                    try:
                        percorso = self._get_logo_path()
                    except Exception:
                        pass
                    _kd_stringi_spazi(r, 0.35)
                    for alto in (150, 132, 116, 100, 86, 72, 58):
                        _kd_logo(r, alto, percorso)
                        if _kd_alta(r) <= reale - 16:
                            _kd_respira(r, reale - 16 - _kd_alta(r))
                            break
                    else:
                        _kd_stringi_spazi(r, 0.4)
                    serve = _kd_alta(r) + 8
                    if 400 < serve < reale:
                        self._kd_h_reale = serve
            except Exception:
                pass

        def _init_adattato(self, *a, _orig=_init_orig_splash, **kw):
            _orig(self, *a, **kw)
            # __init__ rimette 880 dopo aver creato i widget: qui si ridà
            # l'altezza che sta davvero nello schermo.
            try:
                r = getattr(self, 'root', None)
                h = getattr(self, '_kd_h_reale', 0)
                if r is not None and h:
                    r.update_idletasks()
                    w = r.winfo_width() or 500
                    x = max(0, (r.winfo_screenwidth() - w) // 2)
                    y = max(0, (r.winfo_screenheight() - h) // 2)
                    r.geometry("%dx%d+%d+%d" % (w, h, x, y))
            except Exception:
                pass

        _spl.SplashScreen._create_widgets = _create_widgets_adattato
        _spl.SplashScreen.__init__ = _init_adattato
        _spl.SplashScreen._finestra_adattata = True
        print("\U0001F4D0 Splash della prova: sta nello schermo, seriale leggibile")
except Exception as _e:
    print("\u26A0\uFE0F patch 013, splash non adattato: %s" % _e)


# ==========================================================================
# 14. TONALITA' DEI VIDEO GESTITA DA BASS, COME GLI MP3
# ==========================================================================
# Sugli MP3 la tonalita' e' giusta: BASS alza la frequenza (FREQ) e SoundTouch
# ricompensa la durata (TEMPO), quindi cambia il TONO e non la velocita'.
#
# Sui VIDEO l'audio lo suonava VLC, che NON sa trasporre: espone solo set_rate,
# cioe' la velocita'. Il codice ci moltiplicava dentro il fattore dei semitoni
# (a -2 semitoni: 0,891) e il video andava all'89%: rallentato, e la tonalita'
# non cambiava affatto.
#
# Adesso l'audio del video lo prende in carico BASS, lo stesso motore degli
# MP3: stessa resa, stesso comportamento, tonalita' in SEMITONI interi.
#   1) l'audio si estrae appena parte il brano, non al primo tocco del tono
#      (prima, per tutta l'estrazione, si sentiva il rallentamento);
#   2) quando serve il tono: BASS suona l'audio estratto e VLC resta muto,
#      a fare solo l'immagine;
#   3) a VLC va SOLO la velocita', mai il fattore dei semitoni, cosi'
#      l'immagine resta sincronizzata con quello che si sente;
#   4) tornando a tonalita' 0, BASS si ferma e l'audio torna a VLC.
# Se BASS non c'e', si ripiega su MPV (rubberband) come prima.

def _aggancia_tonalita_video(_sys14):
    import os as _os14
    import threading as _th14

    _KD = getattr(_sys14, 'KaraokeMonitorSystem', None)
    if _KD is None:
        for _n in dir(_sys14):
            _c = getattr(_sys14, _n)
            if isinstance(_c, type) and hasattr(_c, '_apply_rate') and hasattr(_c, 'set_pitch'):
                _KD = _c
                break

    if _KD is not None and not getattr(_KD, '_tonalita_video_vera', False):

        # --- l'audio del video si estrae subito, per farsi trovare pronti ----
        def _preestrai_audio_video(self):
            try:
                if not self.engine.is_video or not self.current_file:
                    return
                if self._video_audio_extracted and _os14.path.exists(self._video_audio_extracted):
                    return
                _file = self.current_file

                def _bg():
                    try:
                        estratto = self._extract_video_audio(_file)
                        if estratto and _os14.path.exists(estratto):
                            if self.current_file == _file:   # brano non cambiato
                                self._video_audio_extracted = estratto
                                print("\U0001F3AC Audio del video pronto per la tonalita'")
                    except Exception as e:
                        print("\u26A0\uFE0F pre-estrazione audio video: %s" % e)

                _th14.Thread(target=_bg, daemon=True).start()
            except Exception as e:
                print("\u26A0\uFE0F pre-estrazione non avviata: %s" % e)

        _KD._preestrai_audio_video = _preestrai_audio_video

        # --- l'audio estratto lo suona BASS, come un MP3 --------------------
        def _audio_video_su_bass(self):
            try:
                from moduli.bass_engine import is_bass_available, get_bass_engine
            except Exception:
                return False
            if not is_bass_available():
                return False
            try:
                _be = get_bass_engine()
                if not _be.initialized:
                    _be.initialize()
                if not _be.initialized or not _be.load(self._video_audio_extracted):
                    return False

                pos_ms = max(0, self.engine.vlc_player.get_time())

                self.engine.vlc_player.audio_set_mute(True)
                if self.engine.vlc_player_pubblico:
                    try:
                        self.engine.vlc_player_pubblico.audio_set_mute(True)
                    except Exception:
                        pass

                self.bass_engine = _be
                self.is_bass_audio = True
                self.is_mpv_audio = False
                self._video_pitch_active = True

                _be.play()
                _be.seek_ms(pos_ms)
                try:
                    _be.set_volume(int(max(0, min(127, self._user_volume * 127))))
                except Exception:
                    pass
                _be.set_pitch(self.current_pitch)
                _be.set_speed(max(0.25, min(4.0, self.current_speed)))
                print("\U0001F3AC Audio del video su BASS: tonalita' %+d, posizione %dms"
                      % (self.current_pitch, pos_ms))
                return True
            except Exception as e:
                print("\u26A0\uFE0F audio del video su BASS non riuscito: %s" % e)
                return False

        _KD._audio_video_su_bass = _audio_video_su_bass

        # prima BASS, poi MPV
        _finish_orig = _KD._finish_activate_video_mpv

        def _finish_bass_o_mpv(self):
            try:
                if (self.is_playing and self.engine.is_video
                        and self._video_audio_extracted
                        and _os14.path.exists(self._video_audio_extracted)
                        and self._audio_video_su_bass()):
                    return
            except Exception as e:
                print("\u26A0\uFE0F BASS per il video: %s" % e)
            return _finish_orig(self)

        _KD._finish_activate_video_mpv = _finish_bass_o_mpv

        # tornando a tonalita' 0, BASS va fermato o resta a suonare sotto
        _deact_orig = _KD._deactivate_video_mpv_audio

        def _deact_anche_bass(self):
            try:
                if self.is_bass_audio and self.bass_engine and self.engine.is_video:
                    try:
                        self.bass_engine.stop()
                    except Exception:
                        pass
                    self.is_bass_audio = False
            except Exception:
                pass
            return _deact_orig(self)

        _KD._deactivate_video_mpv_audio = _deact_anche_bass

        # --- l'estrazione parte insieme al video ----------------------------
        _play_orig = _KD.play

        def _play_con_preestrazione(self, *a, **kw):
            r = _play_orig(self, *a, **kw)
            try:
                if self.engine.is_video and not self.is_midi:
                    self.master.after(800, self._preestrai_audio_video)
            except Exception:
                pass
            return r

        _KD.play = _play_con_preestrazione

        # --- allo stop BASS va fermato -------------------------------------
        # ⚠️ Nello stop() il ramo del video azzera i flag e piu' sotto c'e' un
        # "elif is_bass_audio" che con un video non viene MAI raggiunto:
        # chiudendo il video, l'audio restava a suonare da solo.
        _stop_orig = _KD.stop

        def _stop_ferma_bass(self, *a, **kw):
            try:
                if self.is_bass_audio and self.bass_engine and self.engine.is_video:
                    try:
                        self.bass_engine.stop()
                    except Exception:
                        pass
                    self.is_bass_audio = False
                    self._video_pitch_active = False
            except Exception:
                pass
            return _stop_orig(self, *a, **kw)

        _KD.stop = _stop_ferma_bass

        # --- a VLC solo la velocita', mai il fattore dei semitoni -----------
        _rate_orig = _KD._apply_rate

        def _apply_rate_corretto(self):
            r = _rate_orig(self)
            try:
                if not (self.engine.is_video and self.engine.vlc_player):
                    return r
                if not (self.is_playing or self.is_paused):
                    return r
                speed = max(0.25, min(4.0, self.current_speed))

                if self._video_pitch_active:
                    # audio su BASS/MPV: _apply_rate potrebbe essere uscita
                    # prima di arrivare a VLC (ramo BASS con return)
                    self.engine.vlc_player.set_rate(speed)
                    if self.engine.vlc_player_pubblico:
                        try:
                            self.engine.vlc_player_pubblico.set_rate(speed)
                        except Exception:
                            pass
                elif self.current_pitch != 0:
                    # _apply_rate ha appena messo pitch_factor*speed: si rimette
                    # la sola velocita' e si accende il motore della tonalita'
                    self.engine.vlc_player.set_rate(speed)
                    if self.engine.vlc_player_pubblico:
                        try:
                            self.engine.vlc_player_pubblico.set_rate(speed)
                        except Exception:
                            pass
                    print("\U0001F3AC VLC video: velocita' %.3f, tonalita' in arrivo" % speed)
                    if not self.is_midi:
                        self._activate_video_mpv_audio()
            except Exception as e:
                print("\u26A0\uFE0F tonalita' video: %s" % e)
            return r

        _KD._apply_rate = _apply_rate_corretto
        _KD._tonalita_video_vera = True
        print("\U0001F3B5 Video: tonalita' in semitoni con BASS, come gli MP3")


# \u26A0\uFE0F QUI NON SI IMPORTA moduli.system. Importarlo mentre le patch
# si applicano tirerebbe dentro pygame, VLC, MPV e il monitor PRIMA che il
# programma sia pronto, e l'avvio si inceppa (successo davvero).
# Si aspetta che sia il programma a caricarlo, poi ci si aggancia: i metodi
# stanno sulla classe, quindi valgono anche per le istanze gia' create.
try:
    import threading as _th14b
    import time as _t14b

    def _attendi_e_aggancia():
        for _ in range(900):          # fino a 90s, poi si lascia perdere
            _m = sys.modules.get("moduli.system")
            # ⚠️ Non basta che il MODULO sia in sys.modules: durante l'import
            # ci finisce subito, ancora mezzo vuoto, e la classe non c'e'
            # ancora. Si aspetta la CLASSE, se no ci si aggancia al nulla.
            if _m is not None and getattr(_m, 'KaraokeMonitorSystem', None) is not None:
                try:
                    _aggancia_tonalita_video(_m)
                except Exception as _e:
                    print("\u26A0\uFE0F patch 013, tonalita' video: %s" % _e)
                return
            _t14b.sleep(0.1)

    _th14b.Thread(target=_attendi_e_aggancia, daemon=True,
                  name="TonalitaVideo013").start()
except Exception as _e:
    print("\u26A0\uFE0F patch 013, tonalita' video non agganciata: %s" % _e)
