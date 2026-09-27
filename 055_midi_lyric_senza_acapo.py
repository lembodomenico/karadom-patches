# 055 - MIDI con testo LYRIC senza a capo: ogni evento = una riga
def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_052', '1')) == '0'
    except Exception:
        return False


def _forse_aggiungi_acapo(percorso):
    import os
    import tempfile
    try:
        import mido
    except Exception:
        return None
    try:
        m = mido.MidiFile(percorso)
    except Exception:
        return None
    for tr in m.tracks:
        lyr = [msg for msg in tr if getattr(msg, 'type', None) == 'lyrics']
        if len(lyr) < 5:
            continue
        testi = [msg.text for msg in lyr]
        if any(('\r' in t) or ('\n' in t) for t in testi):
            return None
        frasi = sum(1 for t in testi if ' ' in t.strip())
        if frasi < 3 or frasi < len(testi) * 0.5:
            return None
        nuovi = []
        visto = False
        for msg in tr:
            if getattr(msg, 'type', None) == 'lyrics':
                if visto:
                    nuovi.append(mido.MetaMessage('lyrics', text='\r', time=msg.time))
                    msg = msg.copy(time=0)
                visto = True
            nuovi.append(msg)
        tr[:] = nuovi
        out = os.path.join(tempfile.gettempdir(),
                           'kd052_%d.mid' % (abs(hash(percorso)) % 100000000))
        try:
            m.save(out)
        except Exception:
            return None
        return out
    return None


def apply():
    if _spenta():
        return False
    try:
        from moduli.engine import KaraokeTextEngine as C
    except Exception as _e:
        print('patch 052: no engine %s' % _e)
        return False
    if hasattr(C, 'extract_midi') and not hasattr(C, '_orig_052_midi'):
        C._orig_052_midi = C.extract_midi

        def extract_midi(self, filepath, _orig=C._orig_052_midi):
            import os
            nuovo = None
            try:
                nuovo = _forse_aggiungi_acapo(filepath)
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


def revert():
    try:
        from moduli.engine import KaraokeTextEngine as C
        if hasattr(C, '_orig_052_midi'):
            C.extract_midi = C._orig_052_midi
            del C._orig_052_midi
    except Exception:
        pass


try:
    apply()
except Exception as _e:
    print('patch 052: %s' % _e)
