# 053 - il catalogo in sottofondo non rallenta piu' i video

# Il catalogo remoto, mentre lavora in sottofondo, mandava i brani a
# blocchi (patch 042/043/045). A OGNI blocchetto pero' rileggeva da disco
# TUTTO l'elenco dei gia' mandati (catalogo_mandati.txt, centinaia di
# migliaia di righe) per non rimandarli: con una libreria grande succedeva
# piu' volte al secondo, tenendo occupato il processo (lettura disco +
# scansione) proprio mentre un video era in riproduzione -> toccando il
# video KaraDom si impuntava.
#
# Qui l'elenco dei gia' mandati si tiene IN MEMORIA: si legge una volta
# sola, poi si aggiorna man mano (e si continua a salvarlo su file per la
# ripresa dopo un riavvio). E se il blocco e' uno solo non si apre piu' una
# squadra di 8 fili per niente. Il lavoro resta uguale, ma leggero.

import os
import threading


def traccia(testo):
    riga = '[053] %s' % testo
    try:
        print(riga)
    except Exception:
        pass
    try:
        import datetime
        d = os.path.join(os.environ.get('LOCALAPPDATA') or
                         os.path.expanduser('~'), 'KaraDom')
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, 'patch042.log'), 'a', encoding='utf-8') as f:
            f.write('%s  %s%s' % (
                datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                riga, chr(10)))
    except Exception:
        pass


PER_VOLTA = 1500
FILI = 8

_GIA = set()                 # i gia' mandati, IN MEMORIA
_CARICATO = [False]
_LOCK = threading.Lock()


def _archivio():
    d = os.path.join(os.environ.get('LOCALAPPDATA') or
                     os.path.expanduser('~'), 'KaraDom')
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    return os.path.join(d, 'catalogo_mandati.txt')


def _segno(brano):
    return '%s\t%s' % (str(brano.get('artista', '')).strip().lower(),
                       str(brano.get('titolo', '')).strip().lower())


def _carica_una_volta():
    """Legge il file dei gia' mandati UNA sola volta e lo tiene in `_GIA`."""
    if _CARICATO[0]:
        return
    with _LOCK:
        if _CARICATO[0]:
            return
        try:
            with open(_archivio(), encoding='utf-8') as f:
                for r in f:
                    r = r.rstrip('\n')
                    if r:
                        _GIA.add(r)
        except Exception:
            pass
        _CARICATO[0] = True
        traccia('elenco gia- mandati in memoria: %d' % len(_GIA))


def apply():
    try:
        import sys
        mod = sys.modules.get('moduli.catalogo_remoto')
        if mod is None:
            try:
                from moduli import catalogo_remoto as mod
            except Exception:
                traccia('il catalogo remoto non c-e- in questa versione')
                return False
        if getattr(mod.manda, '_veloce053', False):
            return True

        chiedi = mod._chiedi

        def manda(brani, avviso=None, per_volta=PER_VOLTA, fili=FILI,
                  riprendi=True, fermati=None):
            _carica_una_volta()
            conto = {'inseriti': 0, 'gia_presenti': 0, 'scartati': 0,
                     'totale': 0, 'saltati': 0, 'gruppi': 0,
                     'gruppi_fatti': 0, 'in_volo': 0, 'partiti': 0}
            da_fare = list(brani)
            if riprendi and _GIA:
                prima = len(da_fare)
                # NIENTE lettura da disco: si guarda l'insieme in memoria
                da_fare = [b for b in da_fare if _segno(b) not in _GIA]
                conto['saltati'] = prima - len(da_fare)
                if conto['saltati']:
                    traccia('ne salto %d: gia- arrivati' % conto['saltati'])
            if not da_fare:
                if avviso:
                    avviso(0, 0, conto)
                return conto

            gruppi = [da_fare[i:i + per_volta]
                      for i in range(0, len(da_fare), per_volta)]
            traccia('%d brani in %d richieste, %d insieme'
                    % (len(da_fare), len(gruppi), fili))
            chiave = threading.Lock()
            quanti = [0]
            guaio = []
            conto['gruppi'] = len(gruppi)

            def _segna_mandati(pezzo):
                """Aggiorna l'insieme in memoria E il file (per la ripresa)."""
                with _LOCK:
                    for b in pezzo:
                        _GIA.add(_segno(b))
                try:
                    with open(_archivio(), 'a', encoding='utf-8') as f:
                        f.write(''.join('%s\n' % _segno(b) for b in pezzo))
                except Exception:
                    pass

            def _uno(pezzo):
                if guaio or (fermati and fermati()):
                    return
                with chiave:
                    conto['partiti'] = conto.get('partiti', 0) + 1
                    conto['in_volo'] = conto.get('in_volo', 0) + 1
                    if avviso:
                        avviso(quanti[0], len(da_fare), conto)
                try:
                    esito = chiedi('aggiungi', brani=pezzo)
                except Exception as e:
                    if not guaio:
                        guaio.append(e)
                    return
                finally:
                    with chiave:
                        conto['in_volo'] = max(0, conto.get('in_volo', 1) - 1)
                with chiave:
                    conto['gruppi_fatti'] = conto.get('gruppi_fatti', 0) + 1
                    for k in ('inseriti', 'gia_presenti', 'scartati'):
                        conto[k] += int(esito.get(k) or 0)
                    conto['totale'] = int(esito.get('totale')
                                          or conto['totale'])
                    quanti[0] += len(pezzo)
                _segna_mandati(pezzo)
                with chiave:
                    if avviso:
                        avviso(quanti[0], len(da_fare), conto)

            if len(gruppi) <= 1:
                # un blocco solo: niente squadra di fili, si manda qui
                for g in gruppi:
                    _uno(g)
            else:
                from concurrent.futures import ThreadPoolExecutor
                with ThreadPoolExecutor(max_workers=max(1, int(fili))) as sq:
                    list(sq.map(_uno, gruppi))
            if guaio:
                raise guaio[0]
            traccia('finito: %d nuovi, %d c-erano gia-'
                    % (conto['inseriti'], conto['gia_presenti']))
            return conto

        manda._veloce053 = True
        manda._veloce042 = True
        mod.manda = manda
        try:
            opz = sys.modules.get('moduli.opzioni')
            if opz is not None and hasattr(opz, 'manda'):
                opz.manda = manda
        except Exception:
            pass
        traccia('catalogo: gia- mandati in memoria, blocco singolo senza fili')
        return True
    except Exception as e:
        traccia('non agganciata: %s: %s' % (type(e).__name__, e))
        return False


def revert():
    return False


try:
    apply()
except Exception:
    pass
