# 042 - catalogo piu' veloce

import os
import threading


def traccia(testo):
    riga = '[042] %s' % testo
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


def _gia_mandati():
    try:
        with open(_archivio(), encoding='utf-8') as f:
            return {r.rstrip('\n') for r in f if r.strip()}
    except Exception:
        return set()


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
        if getattr(mod.manda, '_veloce042', False):
            return True

        chiedi = mod._chiedi

        def manda(brani, avviso=None, per_volta=PER_VOLTA, fili=FILI,
                  riprendi=True, fermati=None):
            from concurrent.futures import ThreadPoolExecutor
            conto = {'inseriti': 0, 'gia_presenti': 0, 'scartati': 0,
                     'totale': 0, 'saltati': 0, 'gruppi': 0,
                     'gruppi_fatti': 0, 'in_volo': 0, 'partiti': 0}
            da_fare = list(brani)
            if riprendi:
                fatti = _gia_mandati()
                if fatti:
                    prima = len(da_fare)
                    da_fare = [b for b in da_fare if _segno(b) not in fatti]
                    conto['saltati'] = prima - len(da_fare)
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
                    try:
                        with open(_archivio(), 'a', encoding='utf-8') as f:
                            f.write(''.join('%s\n' % _segno(b) for b in pezzo))
                    except Exception:
                        pass
                    if avviso:
                        avviso(quanti[0], len(da_fare), conto)

            with ThreadPoolExecutor(max_workers=max(1, int(fili))) as squadra:
                list(squadra.map(_uno, gruppi))
            if guaio:
                raise guaio[0]
            traccia('finito: %d nuovi, %d c-erano gia-'
                    % (conto['inseriti'], conto['gia_presenti']))
            return conto

        manda._veloce042 = True
        mod.manda = manda
        try:
            opz = sys.modules.get('moduli.opzioni')
            if opz is not None and hasattr(opz, 'manda'):
                opz.manda = manda
        except Exception:
            pass
        traccia('catalogo: %d per gruppo, %d insieme, con ripresa'
                % (PER_VOLTA, FILI))
        _mostra_che_lavora()
        return True
    except Exception as e:
        traccia('non agganciata: %s: %s' % (type(e).__name__, e))
        return False


def _mostra_che_lavora():
    try:
        import sys
        import time as _tm
        opz = sys.modules.get('moduli.opzioni')
        if opz is None:
            return
        cls = None
        for nome in dir(opz):
            o = getattr(opz, nome)
            if isinstance(o, type) and hasattr(o, '_popola_catalogo_remoto'):
                cls = o
                break
        if cls is None or getattr(cls._popola_catalogo_remoto,
                                  '_vivo042', False):
            return
        originale = cls._popola_catalogo_remoto
        GIRA = ('|', '/', '-', '\\')

        def _popola(self, _orig=originale):
            partito = [_tm.time()]

            def _batti(n=0):
                try:
                    testo = self.lbl_catalogo.cget('text') or ''
                except Exception:
                    return
                if n > 4 and testo.startswith(('Fatto', 'Fermato',
                                               'Non ha funzionato',
                                               'Nessun brano')):
                    return
                if (('Mando' in testo or 'Mandati' in testo)
                        and not getattr(self, '_orologio043', False)):
                    try:
                        self.lbl_catalogo.config(
                            text='%s %s — %d s' % (
                                GIRA[n % 4], testo.lstrip('|/-\\ ').split(' — ')[0],
                                _tm.time() - partito[0]))
                    except Exception:
                        pass
                try:
                    self.window.after(500, _batti, n + 1)
                except Exception:
                    pass
            try:
                self.window.after(1500, _batti)
            except Exception:
                pass
            return _orig(self)

        _popola._vivo042 = True
        cls._popola_catalogo_remoto = _popola
        traccia('i numeri ora scorrono nella finestra')
    except Exception as e:
        traccia('orologio non agganciato: %s' % e)


def revert():
    return False


try:
    apply()
except Exception:
    pass
