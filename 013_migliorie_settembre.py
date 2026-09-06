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











#
# 15. SU YOUTUBE IL BOTTONE DOWNLOAD CHIEDE MP4 O MP3 - per farne una base
#     serve spesso il solo audio, e scaricare il video per poi buttarlo e'
#     tempo e spazio sprecati. Si sceglie in una finestrella.
#
# 16. I PRIMI 3 RISULTATI YOUTUBE SI PREPARANO DA SOLI - premendo Play il
#     tempo se ne va nel ricavare l'indirizzo del flusso (yt-dlp +
#     anti-bot: 6,6s misurati). Si risolve mentre guardi l'elenco.

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

        # --- ffmpeg col PERCORSO, non col nome nudo ------------------------
        # ⚠️ CAUSA VERA del "sui video la tonalita' non funziona" segnalata da
        # un cliente: _extract_video_audio chiamava 'ffmpeg' senza percorso.
        # Sul PC di chi sviluppa ffmpeg e' nel PATH e va; sui PC dei clienti NO
        # (sta in dipendenze\, spedito col programma). L'estrazione falliva in
        # silenzio, l'audio non arrivava a BASS e si ricadeva sulla velocita':
        # il video rallentava invece di cambiare tono.
        _estrai_orig = _KD._extract_video_audio

        def _kd_extract_video_audio(self, video_path, _orig=_estrai_orig):
            import subprocess as _sp, tempfile as _tf
            try:
                base = _os14.path.splitext(_os14.path.basename(video_path))[0]
                out = _os14.path.join(_tf.gettempdir(), base + "_extracted_audio.wav")
                if _os14.path.exists(out) and _os14.path.getsize(out) > 1000:
                    return out
                # nel compilato la cartella si ricava da sys.argv[0], non da
                # __file__ (Nuitka lo mette altrove): si usa _dep di yt2mp3
                ffmpeg = 'ffmpeg'
                try:
                    from moduli.yt2mp3 import _dep as _dip
                    _f = _dip('ffmpeg.exe' if _os14.name == 'nt' else 'ffmpeg')
                    if _os14.path.exists(_f):
                        ffmpeg = _f
                    else:
                        from moduli.normalizzazione import _get_ffmpeg_path
                        ffmpeg = _get_ffmpeg_path()
                except Exception:
                    pass
                _sp.run([ffmpeg, '-y', '-i', video_path, '-vn', '-acodec', 'pcm_s24le',
                         '-ar', '48000', '-ac', '2', out],
                        capture_output=True, timeout=120,
                        creationflags=0x08000000 if _os14.name == 'nt' else 0)
                if _os14.path.exists(out) and _os14.path.getsize(out) > 1000:
                    print("🎬 Audio del video estratto (%.1f MB) con %s"
                          % (_os14.path.getsize(out) / 1048576.0, ffmpeg))
                    return out
            except Exception as e:
                print("⚠️ estrazione audio del video: %s" % e)
            return _orig(self, video_path)

        _KD._extract_video_audio = _kd_extract_video_audio

        # --- dopo un MIDI, il video non cambiava tonalita' -----------------
        # I flag del brano precedente (is_midi, is_bass_audio) erano azzerati
        # SOLO nel ramo "non video" di load_file: caricando un video restavano
        # accesi. Con is_midi=True set_pitch non da' l'audio del video a BASS,
        # e il tono non cambia. Sintomo: suoni un MIDI, poi un video, e il
        # pitch non funziona finche' non passi da un mp3.
        _load_orig = _KD.load_file

        def _kd_load_file(self, *a, **kw):
            r = _load_orig(self, *a, **kw)
            try:
                if getattr(self.engine, 'is_video', False):
                    if self.is_midi or self.is_bass_audio:
                        print("🎬 Video: azzerati i flag del brano precedente")
                    self.is_midi = False
                    self.is_bass_audio = False
                    self.is_cdg = False
            except Exception:
                pass
            return r

        _KD.load_file = _kd_load_file

        # --- il fade out deve spegnere anche BASS ---------------------------
        # Nel fade del video si sfumavano VLC e MPV: BASS non era previsto,
        # perche' prima l'audio del video non ci passava mai. Risultato: il
        # video si fermava e la musica restava a suonare.
        _fade_orig = _KD.fade_out

        def _kd_fade_out(self, *a, **kw):
            r = _fade_orig(self, *a, **kw)
            try:
                if self.is_bass_audio and self.bass_engine:
                    try:
                        self.bass_engine.stop()
                    except Exception:
                        pass
                    try:
                        self.bass_engine.set_volume(
                            int(max(0, min(127, self._user_volume * 127))))
                    except Exception:
                        pass
                    self.is_bass_audio = False
                    self._video_pitch_active = False
                    print("🎬 Fade out: fermato anche l'audio su BASS")
            except Exception as e:
                print("⚠️ fade out, BASS non fermato: %s" % e)
            return r

        _KD.fade_out = _kd_fade_out

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


# ==========================================================================
# 15. SU YOUTUBE IL BOTTONE DOWNLOAD CHIEDE MP4 O MP3
# ==========================================================================
# Nei risultati c'era "Download MP4" e basta. Per farne una base karaoke serve
# spesso il solo audio: scaricare il video per poi buttarlo e' tempo e spazio
# sprecati, e su una connessione lenta si aspetta per niente.
#
# Il bottone diventa "Download" e apre una finestrella con due scelte. La
# finestrella ha la STESSA misura fissa di quella del download: due finestre
# della stessa famiglia che cambiano taglia sembrano due programmi diversi.
#
# Scaricando un MP3, la finestra di avanzamento diceva "Download MP4 in corso"
# e alla fine "Video scaricato"; peggio, cercava un file .mp4 e avvisava
# "nessun MP4 trovato" anche a download riuscito.
#
# ⚠️ NON si aggiungono bottoni alla scheda: la scheda viene RIDISEGNATA a ogni
# ridimensionamento della finestra, e un bottone aggiunto si accumula a ogni
# giro (provato: decine di "MP3" uno sotto l'altro). Si cambia il testo e il
# comando di quello che c'e' gia'.
#
# ⚠️ Il codice gira DENTRO il modulo yt2mp3 (exec nel suo __dict__): usa nomi
# suoi — _dep, _YT_FORMAT_DL, tk, S, F, messagebox, la traduzione — che nel
# namespace della patch non esistono.

_KD_YT = r'''
def _kd_download_thread(self, url, cartella, formato=None):
    formato = formato or getattr(self, '_kd_formato', 'mp4')
    yt_dlp_exe = _dep("yt-dlp.exe")
    ffmpeg_loc = _dep("ffmpeg.exe")
    ffprobe_loc = _dep("ffprobe.exe")
    for path, nome in ((yt_dlp_exe, "yt-dlp.exe"), (ffmpeg_loc, "ffmpeg.exe"), (ffprobe_loc, "ffprobe.exe")):
        if not os.path.exists(path):
            self.root.after(0, self._chiudi_progresso)
            self.root.after(50, lambda n=nome: messagebox.showerror(
                _("Errore"), _("{n} non trovato nella cartella dipendenze!").format(n=n), parent=self.root))
            return

    output_template = os.path.join(cartella, "%(title)s.%(ext)s")
    # Anti-bot come lo streaming desktop: client web_safari/tv + deno per la
    # sfida JS (evita "Sign in to confirm you're not a bot"). Vedi youtube_local.
    deno = None
    supporta_rc = False
    try:
        from .youtube_local import _deno_exe, _ytdlp_supports
        deno = _deno_exe()
        if deno:
            supporta_rc = _ytdlp_supports(yt_dlp_exe, "--remote-components")
    except Exception:
        deno = None
    js = ["--js-runtimes", "deno:" + deno] if deno else []
    # con deno, i solver EJS aggiornati da GitHub: senza, "n challenge solving failed"
    # e meta' dei formati sparisce. Il flag si passa SOLO se questo exe lo conosce.
    if supporta_rc:
        js += ["--remote-components", "ejs:github"]
    antibot = ["--extractor-args", "youtube:player_client=" + _YT_PLAYER_CLIENT]

    if formato == 'mp3':
        # Solo audio: si prende la traccia migliore e la si converte in MP3
        # con ffmpeg. Niente "--merge-output-format mp4", che qui non ha
        # senso e farebbe uscire un contenitore video vuoto.
        scelta = [
            "-f", "bestaudio/best",
            "-x", "--audio-format", "mp3", "--audio-quality", "0",
        ]
    else:
        scelta = [
            "-f", _YT_FORMAT_DL,
            "--merge-output-format", "mp4",
        ]

    args = [
        yt_dlp_exe, *js, *antibot,
        *scelta,
        "--ffmpeg-location", ffmpeg_loc,
        "--no-mtime",
        "-o", output_template,
        url,
    ]
    files_before = set(os.listdir(cartella)) if os.path.exists(cartella) else set()
    try:
        proc = subprocess.Popen(
            args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding='utf-8', errors='replace',
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
        pat = re.compile(r"\[download\]\s+([\d.]+)%")
        for line in proc.stdout:
            m = pat.search(line)
            if m:
                try:
                    self._aggiorna_progresso(float(m.group(1)))
                except Exception:
                    pass
        proc.wait()
        exit_code = proc.returncode
    except Exception as e:
        self.root.after(0, self._chiudi_progresso)
        self.root.after(50, lambda: messagebox.showerror(
            _("Errore"), _("Errore esecuzione yt-dlp:") + f"\n{e}", parent=self.root))
        return

    if exit_code != 0:
        self.root.after(0, self._chiudi_progresso)
        self.root.after(50, lambda: messagebox.showerror(
            _("Errore"), _("yt-dlp ha restituito un errore (exit code: {c})").format(c=exit_code),
            parent=self.root))
        return

    time.sleep(1.5)
    new_files = set(os.listdir(cartella)) - files_before
    for f in list(new_files):
        if f.lower().endswith(".mhtml"):
            try:
                os.remove(os.path.join(cartella, f))
            except Exception:
                pass
    # si cerca il file del formato CHIESTO: con l'MP3 la vecchia ricerca
    # dei soli .mp4 non trovava niente e diceva "nessun MP4 trovato"
    _ext = (".mp3", ".m4a", ".opus", ".webm") if formato == 'mp3' else (".mp4",)
    trovati = [os.path.join(cartella, f) for f in new_files
               if f.lower().endswith(_ext)]
    self.root.after(0, self._chiudi_progresso)
    if not trovati:
        _nome = formato.upper()
        self.root.after(50, lambda n=_nome: messagebox.showwarning(
            _("Attenzione"),
            _("Download finito ma nessun {f} trovato.").format(f=n),
            parent=self.root))
        return
    finale = max(trovati, key=os.path.getmtime)
    # cosi' il bottone "Trova il file" sa esattamente quale file aprire
    try:
        self._scaricati[url] = finale
    except Exception:
        pass
    size_mb = os.path.getsize(finale) / (1024 * 1024)
    _cosa = _("Audio scaricato") if formato == 'mp3' else _("Video scaricato")
    self.root.after(50, lambda f=os.path.basename(finale), s=size_mb, p=finale,
                    c=_cosa: messagebox.showinfo(
        _("✅ Download completato"),
        _("{c}:\n{f}\n\nDimensione: {s:.2f} MB\n\nPercorso:\n{p}").format(c=c, f=f, s=s, p=p),
        parent=self.root))


def _kd_chiedi_e_scarica(self, url):
    """Chiede il formato e scarica. Una finestrella, due bottoni."""
    dlg = tk.Toplevel(self.root)
    dlg.title(_("Come vuoi scaricarlo?"))
    dlg.configure(bg='#1a1a2e')
    dlg.transient(self.root)
    dlg.resizable(False, False)

    tk.Label(dlg, text=_("Cosa vuoi scaricare?"), bg='#1a1a2e', fg='white',
             font=F('Segoe UI', 11, 'bold')).pack(padx=S(24), pady=(S(18), S(4)))
    tk.Label(dlg, text=_("L'MP3 prende solo l'audio: piu' veloce e occupa molto meno."),
             bg='#1a1a2e', fg='#9aa4bf', font=F('Segoe UI', 9),
             wraplength=S(480)).pack(padx=S(24), pady=(0, S(14)))

    def scegli(formato):
        dlg.destroy()
        self._scarica(url, formato)

    riga = tk.Frame(dlg, bg='#1a1a2e')
    riga.pack(padx=S(24), pady=(0, S(10)))
    tk.Button(riga, text=_("🎬 MP4  (video)"), command=lambda: scegli('mp4'),
              bg='#007bff', fg='white', font=F('Segoe UI', 10, 'bold'),
              relief='flat', cursor='hand2', width=S(16), pady=S(6)).pack(side='left')
    tk.Button(riga, text=_("🎵 MP3  (solo audio)"), command=lambda: scegli('mp3'),
              bg='#e67e22', fg='white', font=F('Segoe UI', 10, 'bold'),
              relief='flat', cursor='hand2', width=S(16), pady=S(6)).pack(side='left', padx=(S(8), 0))

    tk.Button(dlg, text=_("Annulla"), command=dlg.destroy, bg='#33374d', fg='white',
              font=F('Segoe UI', 9), relief='flat', cursor='hand2').pack(pady=(0, S(16)))

    # Misura FISSA e uguale a quella del download: due finestre della stessa
    # famiglia che cambiano taglia a seconda del testo sembrano due
    # programmi diversi. Stessa larghezza, stesso posto.
    W, H = S(560), S(200)
    x = (dlg.winfo_screenwidth() - W) // 2
    y = (dlg.winfo_screenheight() - H) // 2
    dlg.geometry(f"{W}x{H}+{x}+{y}")
    dlg.grab_set()


def _kd_crea_finestra_progresso(self, formato=None):
    formato = (formato or getattr(self, '_kd_formato', 'mp4')).upper()
    win = tk.Toplevel(self.root)
    # il titolo dice il formato VERO: scaricando un MP3 leggere "MP4" fa
    # solo dubitare di aver premuto il bottone sbagliato
    win.title(_("Download {f} in corso…").format(f=formato))
    win.configure(bg="#2a2a2a")
    win.transient(self.root)
    win.resizable(False, False)
    W, H = S(560), S(180)
    x = (win.winfo_screenwidth() - W) // 2
    y = (win.winfo_screenheight() - H) // 2
    win.geometry(f"{W}x{H}+{x}+{y}")
    tk.Label(win, text="⏬ " + _("Download in corso…"), font=F("Segoe UI", 15, "bold"),
             fg="#00aaff", bg="#2a2a2a").pack(pady=(S(18), S(10)))
    win._lbl = tk.Label(win, text=_("Inizializzazione…"), font=F("Segoe UI", 10),
                        fg="#cccccc", bg="#2a2a2a")
    win._lbl.pack(pady=S(4))
    win._bar = ttk.Progressbar(win, mode="determinate", length=S(460))
    win._bar.pack(pady=S(8))
    win._pct = tk.Label(win, text="0%", font=F("Segoe UI", 12, "bold"),
                       fg="#00aaff", bg="#2a2a2a")
    win._pct.pack(pady=S(4))
    try:
        win.grab_set()
    except Exception:
        pass
    return win
'''

try:
    import tkinter as _tk15
    from moduli import yt2mp3 as _yt15

    # Se il programma ha GIA' la scelta (compilato nuovo) non si tocca niente.
    if (not getattr(_yt15.YoutubePanel, '_scelta_mp4_mp3', False)
            and not hasattr(_yt15.YoutubePanel, '_chiedi_e_scarica')):

        exec(compile(_KD_YT, '<patch 013 punto 15>', 'exec'), _yt15.__dict__)
        _yt15.YoutubePanel._download_thread = _yt15.__dict__['_kd_download_thread']
        _yt15.YoutubePanel._chiedi_e_scarica = _yt15.__dict__['_kd_chiedi_e_scarica']
        _yt15.YoutubePanel._crea_finestra_progresso = _yt15.__dict__['_kd_crea_finestra_progresso']

        _scarica_orig_yt = _yt15.YoutubePanel._scarica_mp4

        def _scarica_yt(self, url, formato='mp4', _orig=_scarica_orig_yt):
            """Ricorda il formato e riusa il percorso di download gia' esistente."""
            self._kd_formato = formato
            return _orig(self, url)

        _yt15.YoutubePanel._scarica = _scarica_yt

        def _card_con_scelta(self, host, url, thumb, title, row, col, wl,
                             _orig=_yt15.YoutubePanel._card_risultato):
            _orig(self, host, url, thumb, title, row, col, wl)
            try:
                _cambia_bottone_download(self, host, url)
            except Exception as e:
                print("\u26A0\uFE0F scelta del formato non agganciata: %s" % e)

        def _cambia_bottone_download(pannello, host, url):
            """Il bottone 'Download MP4' diventa 'Download' e chiede il formato."""
            def cerca(w):
                for c in w.winfo_children():
                    try:
                        if isinstance(c, _tk15.Button) and 'MP4' in str(c.cget('text')):
                            return c
                    except Exception:
                        pass
                    trovato = cerca(c)
                    if trovato is not None:
                        return trovato
                return None

            b = cerca(host)
            if b is None:
                return
            b.configure(text="\u2B07\uFE0F Download",
                        command=lambda u=url: pannello._chiedi_e_scarica(u))

        _yt15.YoutubePanel._card_risultato = _card_con_scelta
        _yt15.YoutubePanel._scelta_mp4_mp3 = True
        print("\U0001F3B5 YouTube: il Download chiede MP4 o MP3")
except Exception as _e:
    print("\u26A0\uFE0F patch 013, scelta del formato non aggiunta: %s" % _e)


# ==========================================================================
# 16. I PRIMI 3 RISULTATI YOUTUBE SI PREPARANO DA SOLI
# ==========================================================================
# Premendo Play su un video YouTube il tempo se ne va quasi tutto nel ricavare
# l'indirizzo del flusso: yt-dlp interroga YouTube e supera il controllo
# anti-bot. MISURATO su un video vero: 6,6 secondi, su linea lenta di piu'.
#
# Il brano non e' ancora stato scelto, ma i primi risultati sono quelli che si
# scelgono quasi sempre: si risolvono in background mentre l'utente guarda
# l'elenco, e l'indirizzo resta pronto per 2 ore (quelli di YouTube durano ~6).
#
# NON si scarica niente: sono richieste piccole, la banda resta libera per il
# video — che e' il punto, dove la connessione e' lenta.
# Misurato dopo: indirizzo gia' pronto, 0,0000s.

_KD_PRONTI = r'''
import threading as _thP
import time as _tP

_url_lock = _thP.Lock()
_url_pronti = {}
_url_in_corso = {}
_URL_VALIDO_SEC = 2 * 3600


def _url_in_cache(vid):
    """Indirizzo gia' risolto e ancora buono, oppure None."""
    import time as _t
    with _url_lock:
        dati = _url_pronti.get(vid)
    if not dati:
        return None
    url, titolo, scade = dati
    if _t.time() > scade:
        with _url_lock:
            _url_pronti.pop(vid, None)
        return None
    return url, titolo


# ⛔ TOLTA la "scaldata" della connessione (leggere i primi 256 KB di ogni
# indirizzo risolto). Sulla carta toglieva DNS e TLS di mezzo; nei fatti, con
# dieci risultati, sono 2,5 MB scaricati mentre l'utente fa partire il video:
# su linea lenta gli rubano la banda proprio nel momento sbagliato, e la
# riproduzione si e' piantata. Si risolve solo l'indirizzo, che non costa nulla.


def prepara_risultati(urls, quanti=3):
    """Risolve in anticipo l'indirizzo dei risultati di una ricerca.

    PERCHE': quando si preme Play su un video YouTube il tempo se ne va quasi
    tutto in `risolvi_url` — yt-dlp interroga YouTube e supera il controllo
    anti-bot: secondi (misurati 6,6 su un video vero, fino a 45 di timeout).
    Risolvendoli mentre l'utente guarda l'elenco, l'indirizzo e' gia' pronto.

    `quanti` = quanti se ne preparano PER VOLTA, non in tutto: si lavora a
    scaglioni, cosi' si preparano tutti senza aprire venti richieste insieme.
    Appena uno finisce, parte il successivo.

    NON scarica niente: sono richieste piccole e la banda resta libera per il
    video — che e' il punto, su una connessione lenta.
    """
    import time as _t

    da_fare = []
    for u in urls:
        vid = _id_da(u)
        if not vid or _url_in_cache(vid):
            continue
        with _url_lock:
            in_corso = _url_in_corso.get(vid)
            if in_corso is not None and in_corso.is_alive():
                continue
        if vid not in da_fare:
            da_fare.append(vid)
    if not da_fare:
        return

    coda = list(da_fare)
    coda_lock = threading.Lock()

    def _prendi():
        with coda_lock:
            return coda.pop(0) if coda else None

    def _lavoratore():
        while True:
            vid = _prendi()
            if vid is None:
                return
            try:
                url, titolo = risolvi_url(vid)
                if url:
                    with _url_lock:
                        _url_pronti[vid] = (url, titolo, _t.time() + _URL_VALIDO_SEC)
                    print("[YT-PRONTO] indirizzo gia' risolto per %s" % vid)
            except Exception as e:
                print("[YT-PRONTO] %s non risolto: %s" % (vid, e))

    quanti = max(1, int(quanti))
    for n in range(min(quanti, len(da_fare))):
        th = threading.Thread(target=_lavoratore, daemon=True,
                              name="yt-pronto-%d" % n)
        with _url_lock:
            for vid in da_fare:
                _url_in_corso.setdefault(vid, th)
        th.start()
    print("[YT-PRONTO] %d da preparare, %d per volta" % (len(da_fare), quanti))
'''

try:
    from moduli import youtube_local as _yl16

    if not getattr(_yl16, '_primi_pronti', False):
        # il codice gira DENTRO youtube_local: usa i suoi nomi (_id_da, risolvi_url)
        exec(compile(_KD_PRONTI, '<patch 013 punto 16>', 'exec'), _yl16.__dict__)

        _ripro_orig = _yl16.riproduci_youtube

        def _riproduci_da_pronto(system, parent, video_id, tonalita=0,
                                 ripiego_browser=None):
            try:
                vid = _yl16._id_da(video_id)
                pronto = _yl16._url_in_cache(vid) if vid else None
                if pronto:
                    print("[YT] indirizzo gia' pronto: nessuna attesa")

                    def _play():
                        try:
                            try:
                                system.engine.yt_title = pronto[1]
                            except Exception:
                                pass
                            if system.load_file(pronto[0], tonalita):
                                system.play(tonalita)
                            elif ripiego_browser:
                                ripiego_browser()
                        except Exception as e:
                            print("[YT] partenza da indirizzo pronto fallita: %s" % e)
                            _ripro_orig(system, parent, video_id, tonalita, ripiego_browser)

                    try:
                        parent.after(0, _play)
                    except Exception:
                        _play()
                    return
            except Exception as e:
                print("[YT-PRONTO] %s" % e)
            return _ripro_orig(system, parent, video_id, tonalita, ripiego_browser)

        _yl16.riproduci_youtube = _riproduci_da_pronto

        from moduli import yt2mp3 as _yt16
        _mostra_orig = _yt16.YoutubePanel._mostra_risultati

        def _mostra_e_prepara(self, lista, _orig=_mostra_orig):
            _orig(self, lista)
            try:
                # ogni risultato e' una tupla (url, miniatura, titolo)
                urls = [r[0] for r in (self._results or [])[:3] if r and r[0]]
                if urls:
                    _yl16.prepara_risultati(urls, quanti=3)
            except Exception as e:
                print("[YT-PRONTO] non avviato: %s" % e)

        _yt16.YoutubePanel._mostra_risultati = _mostra_e_prepara
        _yl16._primi_pronti = True
        print("\U0001F680 YouTube: i primi 3 risultati si preparano da soli")
except Exception as _e:
    print("\u26A0\uFE0F patch 013, preparazione dei risultati non attiva: %s" % _e)
