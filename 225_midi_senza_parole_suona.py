# 225 - midi senza parole

_VER = 1
MIN_PAROLE = 8


def _parole(self):
    n = 0
    for s in getattr(self, 'syllables_data', None) or ():
        t = str(s[0]).replace('\x00', '').strip()
        if t and any(c.isalpha() for c in t):
            n += 1
    return n


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_225', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def _durata_se_suona(percorso):
    try:
        from moduli.midi_riparo import apri
        mid = apri(percorso)
    except Exception:
        try:
            import mido
            mid = mido.MidiFile(percorso)
        except Exception:
            return None
    for traccia in mid.tracks:
        for msg in traccia:
            if msg.type == 'note_on' and getattr(msg, 'velocity', 0) > 0:
                try:
                    return int(mid.length * 1000)
                except Exception:
                    return 0
    return None


def apply():
    if _spenta():
        return False
    try:
        from moduli.engine import KaraokeTextEngine as C
    except Exception:
        return False
    if getattr(C, '_ver225', None) == _VER:
        return True
    prima = C.extract_midi

    def extract_midi(self, filepath):
        esito = prima(self, filepath)
        if esito and _parole(self) >= MIN_PAROLE:
            return esito
        try:
            durata = _durata_se_suona(filepath)
            if durata is None:
                return esito
            import os
            self.syllables_data = []
            self.full_text = ""
            self.is_video = False
            self.total_duration_ms = durata
            self.title = os.path.splitext(os.path.basename(filepath))[0].upper()[:50]
            self.artist = ''
            print('[225] MIDI senza testo: suona solo la musica')
            return True
        except Exception:
            return esito

    C.extract_midi = extract_midi
    C._ver225 = _VER
    return True


def revert():
    return False


try:
    apply()
except Exception:
    pass
