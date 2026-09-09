# 024 - il campo Brano della riga in scaletta cerca nella tabella.

import re

TETTO = 500
ATTESA = 200          # gli stessi millisecondi di debounce dell'originale


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_024', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def _pezzi(testo):
    """La query spezzata come la spezza il campo in alto: '*' oppure spazi,
    e un pezzo che comincia con '.' e' un'estensione."""
    t = (testo or '').lower().strip()
    if '*' in t:
        grezzi = [p.strip() for p in t.split('*') if p.strip()]
    else:
        grezzi = [p for p in re.split(r'\s+', t) if p]
    parti, ext = [], []
    for p in grezzi:
        if p.startswith('.'):
            parti.append(p[1:])
            ext.append(True)
        else:
            parti.append(p)
            ext.append(False)
    return parti, ext


def _lista_corta(self, testo):
    """I brani candidati, presi dalla tabella della 016. None se non si puo'.

    ⚠️ La funzione originale RIFILTRA con lo stesso criterio, quindi qui basta
    darle i candidati giusti: quello che esce sullo schermo lo decide sempre
    lei. Se la tabella non c'e' - archivio sotto i 100.000 brani, o tabella non
    ancora pronta - si torna None e non si tocca niente.
    """
    parti, ext = _pezzi(testo)
    if not parti or len(''.join(parti)) < 2:
        return None
    brani = getattr(self, 'brani_pc', None) or ()
    if not brani:
        return None
    try:
        righe = self._cerca_in_tabella_016(parti, ext, brani, TETTO)
    except Exception:
        righe = None
    if righe is None:
        try:
            self._prepara_tabella_016()      # come fa il campo in alto
        except Exception:
            pass
        return None
    return [brani[i] for i in righe]


def _cattura_key_release(widget, quando_pronto):
    """Prende la funzione che l'originale ha agganciato a <KeyRelease>.

    Non si puo' chiedere a Tk quale funzione Python c'e' dietro un binding, e
    quella dell'originale e' una funzione interna: si intercetta `bind` mentre
    l'originale la registra. Fuori dalla finestra di cattura `bind` torna
    quello di sempre.
    """
    import tkinter as tk
    originale = tk.Misc.bind
    preso = {}

    def bind(self, sequence=None, func=None, add=None):
        esito = originale(self, sequence, func, add)
        if func is not None and str(sequence) == '<KeyRelease>':
            preso['w'] = self
            preso['f'] = func
        return esito

    tk.Misc.bind = bind
    try:
        esito = quando_pronto()
    finally:
        tk.Misc.bind = originale
    return preso.get('w'), preso.get('f'), esito


def _legge_i_brani(f):
    """Vero se quella funzione, dentro, va a leggere `brani_pc`."""
    try:
        co = f.__code__
        if 'brani_pc' in co.co_names:
            return True
        for c in co.co_consts:                # anche le sue funzioni interne
            if hasattr(c, 'co_names') and 'brani_pc' in c.co_names:
                return True
    except Exception:
        pass
    return False


def _dentro_la_chiusura(funzione):
    """La funzione che fa DAVVERO la ricerca, chiusa dentro quella del tasto.

    Il tasto e' agganciato a una funzione che aspetta 200 ms e poi ne chiama
    un'altra: chiamando noi quella seconda possiamo metterle davanti la lista
    corta e toglierla subito dopo, senza rincorrere i tempi.

    ⚠️ Si cerca per COMPORTAMENTO, non per nome: i due campi della scaletta
    chiamano le loro `on_key_release` e `_do_search`, e un domani potrebbero
    chiamarsi ancora diversamente. Si prende la prima funzione della chiusura
    che va a leggere `brani_pc` - che e' esattamente quella da accorciare.
    """
    try:
        for c in (funzione.__closure__ or ()):
            v = c.cell_contents
            if callable(v) and _legge_i_brani(v):
                return v
    except Exception:
        pass
    return None


def _aggancia_riga(self, entry, debounce):
    """Rimpiazza il tasto del campo con uno che passa dalla tabella."""
    import tkinter as tk

    vero = _dentro_la_chiusura(debounce)
    if vero is None:
        return False                 # non si e' capito: si lascia com'era

    ritardo = {'id': None}

    def lavora(e):
        ritardo['id'] = None
        try:
            testo = entry.get().lower().strip()
        except Exception:
            testo = ''
        corta = None
        try:
            corta = _lista_corta(self, testo)
        except Exception:
            corta = None
        if corta is None:
            vero(e)
            return
        pieni = self.brani_pc
        self.brani_pc = corta
        try:
            vero(e)              # legge brani_pc SUBITO, poi lancia il thread
        finally:
            self.brani_pc = pieni

    def al_tasto(e):
        if e.keysym in ('Up', 'Down', 'Return', 'Escape'):
            return
        if ritardo['id']:
            try:
                self.parent.after_cancel(ritardo['id'])
            except Exception:
                pass
        ritardo['id'] = self.parent.after(ATTESA, lambda: lavora(e))

    entry.unbind('<KeyRelease>')
    entry.bind('<KeyRelease>', al_tasto)
    return True


def apply():
    if _spenta():
        return False
    try:
        import sys
        import threading
        import time

        def quando_c_e():
            # ⚠️ Non si importa moduli.libreria durante apply_all: tirerebbe
            #    dentro mezzo programma prima che sia pronto. Si aspetta che
            #    la classe esista davvero (durante l'import il modulo e' gia'
            #    in sys.modules ma ancora mezzo vuoto).
            for _ in range(1200):            # due minuti al massimo
                time.sleep(0.1)
                m = sys.modules.get('moduli.libreria')
                C = getattr(m, 'LibreriaSlider', None) if m else None
                if C is None or not hasattr(C, '_setup_brano_autocomplete'):
                    continue
                if hasattr(C, '_orig_024__setup_brano_autocomplete'):
                    return

                # I DUE campi della scaletta: quello della riga nuova e
                # quello che si apre modificando un brano gia' in tabella.
                # Struttura diversa (uno chiama on_key_release, l'altro
                # _do_search) ma stesso schema: il tasto -> attesa -> ricerca.
                for _nome in ('_setup_brano_autocomplete', '_sc_edit_brano'):
                    if not hasattr(C, _nome):
                        continue
                    _marchio = '_orig_024_' + _nome
                    if hasattr(C, _marchio):
                        continue
                    setattr(C, _marchio, getattr(C, _nome))

                    def avvolto(self, *a, _orig=getattr(C, _marchio), **k):
                        entry, debounce, esito = _cattura_key_release(
                            None, lambda: _orig(self, *a, **k))
                        try:
                            if entry is not None and debounce is not None:
                                _aggancia_riga(self, entry, debounce)
                        except Exception:
                            pass
                        return esito

                    setattr(C, _nome, avvolto)
                return

        threading.Thread(target=quando_c_e, daemon=True,
                         name="RigaScaletta024").start()
        return True
    except Exception:
        return False


def revert():
    try:
        import sys
        m = sys.modules.get('moduli.libreria')
        C = getattr(m, 'LibreriaSlider', None) if m else None
        fatto = False
        for nome in ('_setup_brano_autocomplete', '_sc_edit_brano'):
            marchio = '_orig_024_' + nome
            if C is not None and hasattr(C, marchio):
                setattr(C, nome, getattr(C, marchio))
                delattr(C, marchio)
                fatto = True
        return fatto
    except Exception:
        pass
    return False


try:
    apply()
except Exception:
    pass
