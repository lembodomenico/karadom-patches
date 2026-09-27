# 057 - MIDI con righe troppo lunghe: le spezza a fine parola (niente testo rimpicciolito) e chiude l'ultima
def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_057', '1')) == '0'
    except Exception:
        return False


def _forse_spezza_righe(percorso, maxlen=40):
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
    cambiato = False
    for tr in m.tracks:
        lyr = [msg for msg in tr if getattr(msg, 'type', None) == 'lyrics']
        if len(lyr) < 5:
            continue
        nuovi = []
        linelen = 0
        n_lyr = 0
        ultimo_era_acapo = True
        conf_parola = True   # siamo a confine di parola? (la sillaba prima finiva con spazio)
        for msg in tr:
            if getattr(msg, 'type', None) == 'lyrics':
                t = msg.text or ''
                if ('\r' in t) or ('\n' in t):
                    # e' un a capo: azzera la riga
                    nuovi.append(msg)
                    linelen = 0
                    ultimo_era_acapo = True
                    conf_parola = True
                    continue
                n_lyr += 1
                # a capo SOLO a confine di parola (per non spezzare "senso" o i melismi),
                # e solo se la riga ha gia' roba e sfora la larghezza.
                if linelen > 0 and conf_parola and (linelen + len(t)) > maxlen and t.strip():
                    nuovi.append(mido.MetaMessage('lyrics', text='\r', time=msg.time))
                    msg = msg.copy(time=0)
                    linelen = 0
                    cambiato = True
                nuovi.append(msg)
                linelen += len(t)
                ultimo_era_acapo = False
                # confine di parola = questa sillaba finisce con spazio (o punteggiatura)
                conf_parola = t.endswith(' ') or t.endswith((',', '.', '!', '?', ';', ':'))
            else:
                nuovi.append(msg)
        # chiudi l'ultima riga se non finisce con un a capo
        if n_lyr and not ultimo_era_acapo:
            nuovi.append(mido.MetaMessage('lyrics', text='\r', time=0))
            cambiato = True
        tr[:] = nuovi
    if not cambiato:
        return None
    out = os.path.join(tempfile.gettempdir(),
                       'kd057_%d.mid' % (abs(hash(percorso)) % 100000000))
    try:
        m.save(out)
    except Exception:
        return None
    return out


def apply():
    if _spenta():
        return False
    try:
        from moduli.engine import KaraokeTextEngine as C
    except Exception as _e:
        print('patch 057: no engine %s' % _e)
        return False
    if hasattr(C, 'extract_midi') and not hasattr(C, '_orig_057_midi'):
        C._orig_057_midi = C.extract_midi

        def extract_midi(self, filepath, _orig=C._orig_057_midi):
            import os
            nuovo = None
            try:
                nuovo = _forse_spezza_righe(filepath)
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
        if hasattr(C, '_orig_057_midi'):
            C.extract_midi = C._orig_057_midi
            del C._orig_057_midi
    except Exception:
        pass


try:
    apply()
except Exception as _e:
    print('patch 057: %s' % _e)
