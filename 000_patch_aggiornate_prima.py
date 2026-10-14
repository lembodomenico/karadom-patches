# 000 - aggiornamenti attivi a ogni avvio

import hashlib
import json
import os
import threading
import time
import urllib.request

_VER = 2
API = "https://api.github.com/repos/lembodomenico/karadom-patches/commits/main"
RAW = "https://raw.githubusercontent.com/lembodomenico/karadom-patches"
INTESTAZIONI = {"User-Agent": "KaraDom Pro Updater", "Cache-Control": "no-cache"}
TEMPO_MAX = 8.0          # mai piu' di cosi' all'avvio: senza rete si prosegue con le patch che ci sono


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_000', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def _leggi(url, timeout):
    req = urllib.request.Request(url, headers=INTESTAZIONI)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _impronta(p):
    try:
        return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
    except Exception:
        return None


def aggiorna_prima_di_caricare(d, verifica, scadenza):
    """Porta la cartella delle patch all'ultima versione pubblicata PRIMA che si carichino.
    Si scaricano SOLO le patch nuove o cambiate (confronto con l'impronta del manifest, fatto
    sul disco); se GitHub e' allo stesso commit dell'ultima volta non si scarica niente."""
    resta = lambda: max(0.5, scadenza - time.time())
    segno = os.path.join(d, '.ultimo_commit')
    try:
        sha = json.loads(_leggi(API, min(4.0, resta())).decode('utf-8'))['sha']
    except Exception as e:
        # ⛔ GitHub limita l'API (403 "rate limit exceeded", 60 richieste/ora per IP): NON ci si
        #    arrende, si confronta col manifest di main (le impronte decidono cosa scaricare)
        print('[000] commit non letto (%s): uso main' % e)
        sha = None
    if sha:
        try:
            if open(segno).read().strip() == sha:
                return 'gia\' aggiornate (stesso commit)'
        except Exception:
            pass
    base = RAW + '/' + (sha or 'main')
    man = json.loads(_leggi(base + '/manifest.json', resta()).decode('utf-8'))
    elenco = [n for n in man.get('patches') or [] if str(n).endswith('.py')]
    impronte = man.get('hash') or {}
    da_fare = []
    for n in elenco:
        p = os.path.join(d, n)
        if os.path.exists(p + '.prova'):
            continue                                   # prova locale: non si tocca
        if os.path.exists(os.path.join('/opt/karadom-os/patches_os', n)):
            continue                                   # KaraDom OS: versione Linux bloccata apposta
        if not os.path.exists(p) or not os.path.exists(p + '.sig') \
                or (impronte.get(n) and _impronta(p) != impronte[n]):
            da_fare.append(n)
    errori, fatte = [], []
    blocco = threading.Lock()

    def scarica(n):
        try:
            py = _leggi(base + '/' + n, resta())
            sig = _leggi(base + '/' + n + '.sig', resta())
            if not verifica(py, sig):
                raise ValueError('firma non valida')
            p = os.path.join(d, n)
            for dest, dati in ((p + '.sig', sig), (p, py)):
                tmp = dest + '.tmp000'
                with open(tmp, 'wb') as f:
                    f.write(dati)
                os.replace(tmp, dest)
            with blocco:
                fatte.append(n)
        except Exception as e:
            with blocco:
                errori.append('%s (%s)' % (n, e))

    fili = [threading.Thread(target=scarica, args=(n,), daemon=True) for n in da_fare]
    for t in fili:
        t.start()
    for t in fili:
        t.join(resta())
    # patch ritirate (non piu' nel manifest): via, tranne le prove locali
    attese = set(elenco)
    for f in os.listdir(d):
        if f.endswith('.py') and f not in attese and not os.path.exists(os.path.join(d, f + '.prova')):
            for x in (f, f + '.sig'):
                try:
                    os.remove(os.path.join(d, x))
                except Exception:
                    pass
    if sha and not errori and len(fatte) == len(da_fare):
        try:
            open(segno, 'w').write(sha)
        except Exception:
            pass
    return '%d aggiornate su %d pubblicate%s' % (len(fatte), len(elenco),
                                                ('; non scaricate: ' + ', '.join(errori[:5])) if errori else '')


# ---------------------------------------------------------------- dipendenze --
NON_TOCCARE = ('yt-dlp.exe', 'deno.exe')      # si aggiornano da soli: lo zip potrebbe riportarli indietro


def _crc_file(p):
    import zlib
    c = 0
    with open(p, 'rb') as f:
        while True:
            b = f.read(1 << 20)
            if not b:
                return c & 0xFFFFFFFF
            c = zlib.crc32(b, c)


def _metti_in_posto_i_nuovi(dest):
    """File scaricati mentre erano in uso (DLL aperte): si sostituiscono all'avvio dopo."""
    for radice, _cartelle, files in os.walk(dest):
        for f in files:
            if f.endswith('.nuovo000'):
                p = os.path.join(radice, f)
                try:
                    os.replace(p, p[:-len('.nuovo000')])
                except Exception:
                    pass


def aggiorna_dipendenze():
    """Delta delle dipendenze (DJ-set, Remix, VLC, ...): solo i file nuovi o cambiati di
    dipendenze.zip, letto a pezzi. Se lo zip e' uguale all'ultima volta, una sola richiesta."""
    import zipfile
    from moduli import dep_sync as D
    dest = D._dest_dir()
    os.makedirs(dest, exist_ok=True)
    _metti_in_posto_i_nuovi(dest)
    segno = os.path.join(dest, '.dep_versione')
    req = urllib.request.Request(D.DEP_ZIP_URL, method='HEAD', headers=INTESTAZIONI)
    with urllib.request.urlopen(req, timeout=20) as r:
        versione = '%s|%s' % (r.headers.get('ETag'), r.headers.get('Content-Length'))
    try:
        if open(segno).read().strip() == versione:
            return 'dipendenze gia\' aggiornate'
    except Exception:
        pass
    zf = zipfile.ZipFile(D._HttpRangeFile(D.DEP_ZIP_URL, 30))
    man = D._load_manifest(dest)
    presi, byte, errori, in_uso = 0, 0, 0, 0
    for info in zf.infolist():
        if info.is_dir() or os.path.basename(info.filename) in NON_TOCCARE:
            continue
        p = os.path.join(dest, info.filename.replace('/', os.sep))
        if os.path.exists(p):
            noto = man.get(info.filename)
            if noto is None:                            # messo dall'installazione: si guarda una volta
                try:
                    noto = _crc_file(p) if os.path.getsize(p) == info.file_size else -1
                except Exception:
                    noto = -1
                if noto == info.CRC:
                    man[info.filename] = info.CRC
                    continue
            elif noto == info.CRC and os.path.getsize(p) == info.file_size:
                continue
        try:
            dati = D._fetch_member(D.DEP_ZIP_URL, info, 60)
            try:
                D._write_atomic(p, dati)
            except PermissionError:
                D._write_atomic(p + '.nuovo000', dati)      # in uso: entra al prossimo avvio
                in_uso += 1
            man[info.filename] = info.CRC
            presi += 1
            byte += info.file_size
        except Exception as e:
            errori += 1
            print('[000] dipendenza %s non scaricata: %s' % (info.filename, e))
    D._save_manifest(dest, man)
    if not errori:
        try:
            open(segno, 'w').write(versione)
        except Exception:
            pass
    return 'dipendenze: %d file nuovi/cambiati (%.1f MB)%s%s' % (
        presi, byte / 1048576.0, (', %d entrano al riavvio' % in_uso) if in_uso else '',
        (', %d non scaricati' % errori) if errori else '')


def _dipendenze_in_sottofondo():
    def lavora():
        time.sleep(20)                                  # dopo l'apertura: non rallenta l'avvio
        try:
            print('[000] %s' % aggiorna_dipendenze())
        except Exception as e:
            print('[000] dipendenze: %s' % e)
    threading.Thread(target=lavora, daemon=True, name='Dipendenze000').start()


def apply():
    if _spenta():
        return False
    import sys
    if getattr(sys, '_kd000', None) == _VER:
        return True
    sys._kd000 = _VER
    try:
        from moduli import hotfix as H
    except Exception:
        import hotfix as H
    t0 = time.time()
    try:
        esito = aggiorna_prima_di_caricare(H.patches_dir(), H._verify, t0 + TEMPO_MAX)
    except Exception as e:
        esito = 'rete non raggiungibile (%s): si usano le patch che ci sono' % e
    print('[000] patch: %s in %.1f s' % (esito, time.time() - t0))
    if os.name == 'nt' and str(_cfg('patch_000_dipendenze', '1')) not in ('0', 'no', 'off'):
        _dipendenze_in_sottofondo()                    # KaraDom OS ha le sue: le Windows non servono
    return True


def _cfg(chiave, predef):
    try:
        from moduli.database import Database
        return str(Database.get_config(chiave, predef)).strip()
    except Exception:
        return predef


try:
    apply()
except Exception:
    pass
