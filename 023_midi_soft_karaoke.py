# 023 - i MIDI con due tracce di testo si leggono a righe, non tutte attaccate.


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_023', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def _vlq(d, i):
    n = 0
    while True:
        b = d[i]
        i += 1
        n = (n << 7) | (b & 0x7F)
        if not b & 0x80:
            return n, i


def _guarda_dentro(dati):
    """Legge i byte del MIDI e conta cosa c'e' nelle due possibili fonti.

    Ritorna (posizioni dei meta 0x05, quanti LYRIC, quante sillabe Soft
    Karaoke, c'e' la firma, quante righe segnate). Niente mido: qui si legge
    il file cosi' com'e'.
    """
    if dati[:4] != b'MThd':
        return None
    lung = int.from_bytes(dati[4:8], 'big')
    i = 8 + lung
    posti = []
    lyric = 0
    sillabe = 0
    firma = False
    righe = 0

    while i < len(dati) - 8 and dati[i:i + 4] == b'MTrk':
        n = int.from_bytes(dati[i + 4:i + 8], 'big')
        inizio = i + 8
        fine = inizio + n
        j = inizio
        stato = 0
        while j < fine:
            _d, j = _vlq(dati, j)
            if j >= fine:
                break
            b = dati[j]
            if b == 0xFF:
                tipo = dati[j + 1]
                lun, j2 = _vlq(dati, j + 2)
                testo = dati[j2:j2 + lun]
                if tipo == 0x05:
                    posti.append(j + 1)          # il byte del tipo
                    lyric += 1
                elif tipo == 0x01:
                    if testo[:2] in (b'@K', b'@T', b'@L'):
                        firma = True
                    elif not testo.startswith(b'@'):
                        sillabe += 1
                        if testo[:1] in (b'\\', b'/'):
                            righe += 1
                j = j2 + lun
                stato = 0
                continue
            if b in (0xF0, 0xF7):
                lun, j2 = _vlq(dati, j + 1)
                j = j2 + lun
                stato = 0
                continue
            if b & 0x80:
                stato = b
                j += 1
            j += 1 if (stato & 0xF0) in (0xC0, 0xD0) else 2
        i = fine

    return posti, lyric, sillabe, firma, righe


def _va_aggiustato(dati):
    """Solo quando il Soft Karaoke e' chiaramente la fonte migliore.

    Tre condizioni insieme, cosi' i file che oggi si leggono bene non
    cambiano di una virgola:
      1. c'e' la firma vera (@K / @T / @L, cioe' '@KMIDI KARAOKE FILE');
      2. i TEXT hanno davvero i separatori di riga (\\ oppure /);
      3. sono PIU' degli eventi LYRIC - sillabe contro righe intere.
    """
    try:
        fuori = _guarda_dentro(dati)
    except Exception:
        return None
    if not fuori:
        return None
    posti, lyric, sillabe, firma, righe = fuori
    if not lyric or not firma or righe <= 0 or sillabe <= lyric:
        return None
    return posti


def _copia_senza_lyric(percorso):
    """Una copia del file in cui i LYRIC 0x05 diventano cue point 0x07.

    Un byte per un byte: lunghezze, tempi e note restano intatti, e il
    lettore di KaraDom - che i cue point li ignora - si trova senza LYRIC e
    prende la strada del Soft Karaoke, quella che sa gia' fare le righe e ha
    i tempi per sillaba. Non si tocca il file dell'utente.
    """
    import os
    import tempfile
    dati = bytearray(open(percorso, 'rb').read())
    posti = _va_aggiustato(bytes(dati))
    if not posti:
        return None
    for p in posti:
        dati[p] = 0x07
    fd, nuovo = tempfile.mkstemp(prefix='kd023_', suffix='.mid')
    try:
        os.write(fd, bytes(dati))
    finally:
        os.close(fd)
    return nuovo


def apply():
    if _spenta():
        return False
    try:
        import os
        from moduli.engine import KaraokeTextEngine as C

        if not hasattr(C, 'extract_midi') or hasattr(C, '_orig_023_midi'):
            return hasattr(C, '_orig_023_midi')
        C._orig_023_midi = C.extract_midi

        def extract_midi(self, filepath, _orig=C._orig_023_midi):
            nuovo = None
            try:
                nuovo = _copia_senza_lyric(filepath)
            except Exception:
                nuovo = None
            if not nuovo:
                return _orig(self, filepath)
            try:
                return _orig(self, nuovo)
            finally:
                try:
                    os.remove(nuovo)
                except Exception:
                    pass

        C.extract_midi = extract_midi
        return True
    except Exception:
        return False


def revert():
    try:
        from moduli.engine import KaraokeTextEngine as C
        if hasattr(C, '_orig_023_midi'):
            C.extract_midi = C._orig_023_midi
            del C._orig_023_midi
            return True
    except Exception:
        pass
    return False


try:
    apply()
except Exception:
    pass
