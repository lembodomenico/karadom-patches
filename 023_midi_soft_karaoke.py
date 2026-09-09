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


def _impronta(t):
    return ''.join(c for c in str(t).upper() if c.isalnum())


def _titoli_del_file(dati):
    """I campi @T: il primo e' il titolo, il secondo l'artista.

    Nei Soft Karaoke il titolo e' SCRITTO nel file. KaraDom invece lo prendeva
    dalla prima riga del testo, che e' solo il primo verso cantato: su
    "PIANO PIANO DOCE DOCE" il titolo diventava "PIANO PIANO".
    """
    fuori = []
    try:
        if dati[:4] != b'MThd':
            return fuori
        i = 8 + int.from_bytes(dati[4:8], 'big')
        while i < len(dati) - 8 and dati[i:i + 4] == b'MTrk':
            n = int.from_bytes(dati[i + 4:i + 8], 'big')
            fine = i + 8 + n
            j = i + 8
            stato = 0
            while j < fine:
                _d, j = _vlq(dati, j)
                if j >= fine:
                    break
                b = dati[j]
                if b == 0xFF:
                    tipo = dati[j + 1]
                    lun, j2 = _vlq(dati, j + 2)
                    if tipo == 0x01 and dati[j2:j2 + 2] == b'@T':
                        t = dati[j2 + 2:j2 + lun].decode('latin-1').strip()
                        if t:
                            fuori.append(t)
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
    except Exception:
        pass
    return fuori


def _righe_dei_lyric(percorso):
    """Le righe della traccia LYRIC, col loro tempo in millisecondi."""
    import mido
    # scorrendo il file mido da' l'attesa fra un messaggio e l'altro, in
    # secondi e gia' col tempo applicato: sommandole si ha il tempo assoluto.
    fuori = []
    t = 0.0
    for msg in mido.MidiFile(percorso):
        t += msg.time
        if getattr(msg, 'type', '') == 'lyrics':
            fuori.append((int(t * 1000), msg.text))
    return fuori


def _rimetti_le_righe_perse(self, percorso):
    """Le fonti si FONDONO, non si scelgono.

    La traccia dei LYRIC puo' avere righe che il Soft Karaoke non ha: in
    "PIANO PIANO DOLCE" la prima riga cantata sta SOLO li', perche' la
    traccia Words comincia dopo. Scegliendo il Soft Karaoke e basta, quella
    riga spariva dallo schermo. Si rimettono davanti solo le righe che
    vengono PRIMA dell'inizio del testo e che non ci sono gia' - il confronto
    ignora spazi, apostrofi e maiuscole, perche' le due tracce scrivono lo
    stesso verso in modo un po' diverso ("NON E VITA" / "NON E' VITA").
    """
    syl = getattr(self, 'syllables_data', None)
    if not syl:
        return 0
    viste = set()
    riga = ''
    for s, _t in syl:
        if s == '\n':
            if riga.strip():
                viste.add(_impronta(riga))
            riga = ''
        else:
            riga += s
    if riga.strip():
        viste.add(_impronta(riga))

    inizio = syl[0][1]
    davanti = []
    for ms, testo in _righe_dei_lyric(percorso):
        t = str(testo).lstrip('<\\/').strip()
        if not t or ms >= inizio:
            continue
        if _impronta(t) in viste:
            continue
        viste.add(_impronta(t))
        davanti.append((t, ms))
        davanti.append(('\n', ms))
    if davanti:
        self.syllables_data = davanti + syl
        try:
            self.full_text = "".join(s[0] for s in self.syllables_data)
        except Exception:
            pass
    return len(davanti) // 2


def _soglia_adatta(syllables, minimo=3000):
    """Quanto dev'essere lunga una pausa per valere come stacco strumentale.

    Con 3 secondi fissi, su un brano lento - righe ogni 8 secondi - ogni
    intervallo supera la soglia e finisce una riga vuota FRA TUTTE le righe.
    Uno stacco non e' "una pausa di 3 secondi", e' una pausa molto piu' lunga
    del respiro normale di quel brano.

    ⚠️ Il respiro si misura sul PRIMO QUARTILE, non sulla mediana: in un brano
    con molte pause meta' dei salti SONO pause, e la mediana finirebbe sopra
    tutte - misurato, spariva ogni stacco (25 righe vuote diventavano 0).
    """
    salti = []
    ultimo = None
    a_capo = False
    for s, t in syllables:
        if s == '\n':
            a_capo = True
            continue
        if not s.strip():
            continue
        if a_capo and ultimo is not None:
            salti.append(t - ultimo)
        a_capo = False
        ultimo = t
    salti = sorted(x for x in salti if x > 0)
    if len(salti) < 4:
        return minimo
    return max(minimo, int(salti[len(salti) // 4] * 2.5))


def apply():
    if _spenta():
        return False
    try:
        import os
        from moduli.engine import KaraokeTextEngine as C

        fatto = False

        if hasattr(C, '_add_instrumental_breaks') and not hasattr(C, '_orig_023_stacchi'):
            C._orig_023_stacchi = C._add_instrumental_breaks

            def _add_instrumental_breaks(self, syllables, min_gap_ms=3000,
                                         _orig=C._orig_023_stacchi):
                try:
                    min_gap_ms = _soglia_adatta(syllables, min_gap_ms)
                except Exception:
                    pass
                return _orig(self, syllables, min_gap_ms)

            C._add_instrumental_breaks = _add_instrumental_breaks
            fatto = True

        if hasattr(C, 'extract_midi') and not hasattr(C, '_orig_023_midi'):
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
                    esito = _orig(self, nuovo)
                    if esito:
                        try:
                            _rimetti_le_righe_perse(self, filepath)
                        except Exception:
                            pass
                        try:
                            _t = _titoli_del_file(open(filepath, 'rb').read())
                            if _t:
                                self.title = _t[0][:50]
                                if len(_t) > 1:
                                    self.artist = _t[1][:50]
                        except Exception:
                            pass
                    return esito
                finally:
                    try:
                        os.remove(nuovo)
                    except Exception:
                        pass

            C.extract_midi = extract_midi
            fatto = True

        return fatto or hasattr(C, '_orig_023_midi')
    except Exception:
        return False


def revert():
    try:
        from moduli.engine import KaraokeTextEngine as C
        fatto = False
        if hasattr(C, '_orig_023_midi'):
            C.extract_midi = C._orig_023_midi
            del C._orig_023_midi
            fatto = True
        if hasattr(C, '_orig_023_stacchi'):
            C._add_instrumental_breaks = C._orig_023_stacchi
            del C._orig_023_stacchi
            fatto = True
        return fatto
    except Exception:
        return False


try:
    apply()
except Exception:
    pass
