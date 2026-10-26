# 245 - db brani

import os
import sqlite3
import threading
import time

_VER = 3

# [25-10-2026] Utente: "basta che la prima volta che ci si posiziona legga il disco e copi tutto sul db, poi usa
# quello" + "non e' unico per tutti ma ognuno per se'... comincia con me".
# Un DB per PC (%LOCALAPPDATA%\KaraDom\elenchi\brani.db) al posto degli elenchi .txt.gz:
#  - la prima volta su un preferito si legge il disco (come prima) e l'elenco va nel DB;
#  - dopo si legge SOLO il DB (anche le sottocartelle di un preferito gia' letto: niente disco);
#  - gli elenchi .txt.gz gia' salvati entrano nel DB la prima volta che servono (niente disco nemmeno allora);
#  - niente aggiornamenti a sorpresa (delta): i file nuovi col tasto destro -> "Aggiorna preferito";
#  - all'avvio il preferito di prima si riprende dal DB, non piu' con una scansione completa del disco
#    (prima: 525.000 file riletti a ogni avvio e l'elenco costruito nel thread della finestra).
# Si spegne con patch_245=0 in config. Il .txt.gz resta scritto anche lui: altre parti lo leggono ancora.


def _titolare():
    """Solo sui PC del titolare: licenza FIRMATA intestata a Domenico Lembo (come la 233/239)."""
    try:
        from moduli.licensing import load_license
        d = load_license() or {}
        return (str(d.get('nome', '')).strip().lower(),
                str(d.get('cognome', '')).strip().lower()) == ('domenico', 'lembo')
    except Exception:
        return False


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_245', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def _log(msg):
    try:
        print('[245] %s' % msg)
    except Exception:
        pass


# ------------------------------------------------------------------ il DB --

# v3, utente 25-10 "la lentezza c'e' anche nello spostamento tra playlist": la finestra e' rimasta ferma 10 s in
# _letta ad aspettare il lucchetto mentre in sottofondo si copiavano 523.000 brani nel DB. Ora ogni thread ha la sua
# connessione e chi LEGGE non aspetta mai (WAL: mentre uno scrive, gli altri leggono la versione di prima).
# Il lucchetto resta solo fra chi scrive.
_wlock = threading.Lock()
_ilock = threading.Lock()         # solo per creare le tabelle la prima volta (mai lo stesso di _wlock: si bloccherebbe)
_loc = threading.local()
_pronto = {'si': False}


def _file_db():
    base = os.environ.get('LOCALAPPDATA') or os.path.expanduser('~')
    d = os.path.join(base, 'KaraDom', 'elenchi')
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, 'brani.db')


def _db():
    """La connessione di QUESTO thread."""
    c = getattr(_loc, 'con', None)
    if c is None:
        c = sqlite3.connect(_file_db(), timeout=30)
        if not _pronto['si']:
            with _ilock:
                c.executescript("""
                    PRAGMA journal_mode=WAL;
                    CREATE TABLE IF NOT EXISTS basi (chiave TEXT PRIMARY KEY, path TEXT) WITHOUT ROWID;
                    CREATE TABLE IF NOT EXISTS letti (cartella TEXT PRIMARY KEY, quando REAL, quanti INTEGER) WITHOUT ROWID;
                """)
            _pronto['si'] = True
        c.execute('PRAGMA synchronous=NORMAL')
        _loc.con = c
    return c


def _k(p):
    return os.path.normcase(os.path.normpath(p))


def _intervallo(cartella):
    """Le chiavi dei file sotto la cartella: [cartella\\ , cartella] (il carattere dopo il separatore)."""
    pre = _k(cartella).rstrip('\\/') + os.sep
    return pre, pre[:-1] + chr(ord(os.sep) + 1)


def _letta(cartella):
    """La cartella o una cartella che la contiene e' gia' nel DB?"""
    k = _k(cartella).rstrip('\\/')
    if True:                      # v3: niente lucchetto in lettura
        c = _db()
        while True:
            if c.execute('SELECT 1 FROM letti WHERE cartella=?', (k,)).fetchone():
                return True
            su = os.path.dirname(k)
            if not su or su == k:
                return False
            k = su


_ultima = {}      # v2: la stessa cartella chiesta di nuovo entro 60 s (all'avvio succede due volte) non si rilegge


def _leggi(cartella):
    a, b = _intervallo(cartella)
    u = _ultima.get(a)
    if u and time.time() - u[0] < 60:
        return list(u[1])
    brani = [r[0] for r in _db().execute('SELECT path FROM basi WHERE chiave >= ? AND chiave < ?', (a, b))]
    _ultima.clear()
    _ultima[a] = (time.time(), brani)
    return list(brani)


def _scrivi(cartella, brani):
    a, b = _intervallo(cartella)
    k = _k(cartella).rstrip('\\/')
    _ultima.clear()
    with _wlock:
        c = _db()
        with c:
            c.execute('DELETE FROM basi WHERE chiave >= ? AND chiave < ?', (a, b))
            c.executemany('INSERT OR REPLACE INTO basi VALUES (?,?)', ((_k(p), p) for p in brani))
            # le cartelle dentro questa non servono piu' come voci a se': ora c'e' l'elenco intero
            c.execute('DELETE FROM letti WHERE cartella >= ? AND cartella < ?', (a, b))
            c.execute('INSERT OR REPLACE INTO letti VALUES (?,?,?)', (k, time.time(), len(brani)))


def _in_sottofondo(cartella, brani, cosa):
    """Scrittura nel DB in un thread: mai nella finestra (la musica non deve perdere colpi).
    Finche' non ha finito, chi chiede la cartella usa ancora l'elenco .txt.gz: nessun buco."""
    def lavora():
        try:
            t = time.time()
            _scrivi(cartella, brani)
            _log('%s: %d brani di %s in %.1f s' % (cosa, len(brani), cartella, time.time() - t))
        except Exception as e:
            _log('%s NON riuscito: %s' % (cosa, e))
    threading.Thread(target=lavora, daemon=True, name='245-db').start()


# ---------------------------------------------------------------- l'aggancio --

def apply():
    if not _titolare():
        return False
    if _spenta():
        _log('spenta (patch_245=0)')
        return False
    try:
        import moduli.libreria as lib
        _db()
    except Exception as e:
        _log('non attiva: %s' % e)
        return False
    C = getattr(lib, 'LibreriaSlider', None)
    if C is None or not hasattr(C, '_leggi_cache_disco'):
        return False
    if getattr(C, '_ver245', None) == _VER:
        return True

    leggi0 = getattr(C, '_o245_leggi', None) or C._leggi_cache_disco
    scrivi0 = getattr(C, '_o245_scrivi', None) or C._scrivi_cache_disco
    ripristina0 = getattr(C, '_o245_ripristina', None) or getattr(C, '_ripristina_ultimo_preferito', None)
    delta0 = getattr(C, '_o245_delta', None) or getattr(C, '_delta_preferito', None)
    C._o245_leggi, C._o245_scrivi, C._o245_ripristina, C._o245_delta = leggi0, scrivi0, ripristina0, delta0

    def _leggi_cache_disco(self, cartella):
        try:
            if _letta(cartella):
                t = time.time()
                brani = _leggi(cartella)
                _log('%d brani dal DB in %.2f s (niente disco): %s' % (len(brani), time.time() - t, cartella))
                return brani
        except Exception as e:
            _log('DB non leggibile (%s): uso l\'elenco salvato' % e)
            return leggi0(self, cartella)
        # non ancora nel DB: se c'e' l'elenco .txt.gz di prima entra nel DB, senza leggere il disco.
        # La copia (qualche secondo su 300.000 brani) va in sottofondo: qui siamo nel thread della finestra.
        brani = leggi0(self, cartella)
        if brani:
            _in_sottofondo(cartella, list(brani), 'elenco salvato copiato nel DB')
        return brani

    def _scrivi_cache_disco(self, cartella, brani):
        # disco appena letto (prima volta o tasto destro "Aggiorna preferito"): si aggiorna il DB
        if brani:
            _in_sottofondo(cartella, list(brani), 'DB aggiornato')
        return scrivi0(self, cartella, brani)

    def _delta_preferito(self, cartella):
        # niente scansioni a sorpresa: i file nuovi si prendono col tasto destro "Aggiorna preferito"
        return None

    def _ripristina_ultimo_preferito(self):
        """All'avvio: lo stesso preferito di prima, ma dal DB (carica_brani), non con un giro completo del disco."""
        try:
            from moduli.database import Database
            ultimo = Database.get_config('ultimo_preferito', '')
            if not ultimo or not _letta(ultimo):
                return ripristina0(self) if ripristina0 else None      # mai letto: come prima
            for item in self.tree.get_children():
                v = self.tree.item(item)['values']
                if v and str(v[0]) == ultimo:
                    self._restoring_preferito = True
                    try:
                        self.tree.selection_set(item)
                        self.tree.see(item)
                    finally:
                        self._restoring_preferito = False
                    self.percorso_attivo = ultimo
                    self.carica_brani(ultimo)
                    _log('preferito di prima ripreso dal DB: %s' % ultimo)
                    return None
        except Exception as e:
            _log('ripristino dal DB non riuscito (%s): come prima' % e)
        return ripristina0(self) if ripristina0 else None

    C._leggi_cache_disco = _leggi_cache_disco
    C._scrivi_cache_disco = _scrivi_cache_disco
    if delta0 is not None:
        C._delta_preferito = _delta_preferito
    if ripristina0 is not None:
        C._ripristina_ultimo_preferito = _ripristina_ultimo_preferito
    C._ver245 = _VER
    _log('DB brani attivo: %s' % _file_db())
    return True


def revert():
    return False
