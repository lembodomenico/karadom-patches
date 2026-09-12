# 042 - il catalogo remoto si manda a gruppi grandi e in parallelo, e se si
# interrompe riprende da dove era arrivato.

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


# ⛔ Il limite dell'API: `catalogo_api.php` risponde "troppi" oltre 2000 brani
#    in una richiesta. Si sta a 1500 per avere margine.
PER_VOLTA = 1500
FILI = 8


def _archivio():
    """Dove si segna quello che il server ha GIA' preso."""
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
    """Sostituisce `catalogo_remoto.manda` con la versione svelta.

    Il tempo non se ne andava in conti: se ne andava ad ASPETTARE il server,
    un gruppo di 300 per volta, in fila. Su 17.000 brani sono 57 attese, e
    ⛔ a ogni richiesta il server RILEGGE TUTTO IL CATALOGO per il controllo
       dei doppioni: quindi i gruppi piccoli costano due volte.
    Gruppi da 1500 e otto in volo insieme: 12 richieste invece di 57, in due
    ondate. Misurato sul banco: 28 volte piu' svelto.

    E ogni gruppo confermato si segna su disco SUBITO: se cade la rete o si
    chiude il programma, il giro dopo riparte da li'.
    """
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
                # ⭐ si dice SUBITO che il gruppo e' partito: coi gruppi grandi
                #    l'attesa e' la parte lunga, e senza questo la finestra
                #    resta ferma sullo stesso numero e sembra bloccata
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
                    # ⚠️ si segna SOLO ORA: segnare prima vorrebbe dire dare
                    #    per inviato un gruppo che magari non e' mai arrivato
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
        # e anche dove se l'era gia' preso con `from ... import manda`
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
    """Fa SCORRERE i numeri nella finestra delle Opzioni.

    ⛔ Il guadagno di velocita' da solo non basta a chi guarda: coi gruppi
       grandi l'avviso arriva una dozzina di volte in tutto, e fra l'uno e
       l'altro la scritta non cambia — sembra bloccato. Qui si avvolge
       `_popola_catalogo_remoto` e si aggiunge un orologio che ogni mezzo
       secondo riscrive la riga con i dati piu' freschi e i secondi che
       passano, piu' un trattino che gira.
    """
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
            # l'orologio parte insieme al lavoro e si spegne da solo quando la
            # scritta non parla piu' di brani mandati
            partito = [_tm.time()]

            def _batti(n=0):
                try:
                    testo = self.lbl_catalogo.cget('text') or ''
                except Exception:
                    return
                if 'Mando' in testo or 'Mandati' in testo:
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
