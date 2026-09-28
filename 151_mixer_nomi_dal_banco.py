def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_151', '1')) == '0'
    except Exception:
        return False


def _load_map(path):
    m = {}
    try:
        import os
        if not path or not os.path.isfile(path):
            return m
        raw = open(path, 'rb').read()
        if raw[:4] != b'RIFF':
            return m
        def chunks(b, s, e):
            j = s; o = []
            while j + 8 <= e:
                t = b[j:j+4]; z = int.from_bytes(b[j+4:j+8], 'little')
                o.append((t, j+8, z)); j += 8 + z + (z & 1)
            return o
        for t, s, z in chunks(raw, 12, len(raw)):
            if t == b'LIST' and raw[s:s+4] == b'pdta':
                for c, cs, cz in chunks(raw, s+4, s+4+z-4):
                    if c == b'phdr':
                        n = cz // 38
                        for k in range(n - 1):
                            rec = raw[cs+k*38: cs+k*38+38]
                            name = rec[:20].split(b'\x00')[0].decode('latin1', 'replace')
                            prog = int.from_bytes(rec[20:22], 'little')
                            bank = int.from_bytes(rec[22:24], 'little')
                            m[(bank, prog)] = name
    except Exception as e:
        print('[NOMI151] parse banco:', e)
    return m


def _expander_software_attivo():
    try:
        from moduli.expander_midi import get_active_player
        exp = get_active_player()
        if not exp:
            return False
        np = (getattr(exp, 'nome_porta', '') or '').lower()
        return ('loop' in np) or ('software' in np)
    except Exception:
        return False


def apply():
    if _spenta():
        return False
    try:
        import moduli.mixer as MX
        from moduli.database import Database
    except Exception as e:
        print('[NOMI151] moduli:', e); return False
    P = getattr(MX, 'MIDIMixerPanel', None) or getattr(MX, 'MidiMixerPanel', None)
    if P is None or not hasattr(P, 'load_midi_file'):
        print('[NOMI151] mixer/load_midi_file assente'); return False
    if getattr(P, '_names151', False):
        return True

    path = Database.get_config('exp_banco_path', '') or Database.get_config('soundfont_path', '')
    MAP = _load_map(path)
    print('[NOMI151] nomi dal banco: %d preset da %s' % (len(MAP), path))
    if not MAP:
        print('[NOMI151] banco vuoto/illeggibile: non aggancio'); return False

    _orig = P.load_midi_file

    def load_midi_file(self, *a, **k):
        r = _orig(self, *a, **k)
        try:
            if _expander_software_attivo():
                nch = 0
                for i, ch in enumerate(getattr(self, 'channels', []) or []):
                    prog = ch.get('program')
                    bank = ch.get('bank')
                    if prog is None:
                        continue
                    bk = 128 if (i == 9 or bank == 128) else bank
                    nm = MAP.get((bk, prog)) or MAP.get((0, prog))
                    if nm:
                        ch['name_var'].set(nm)
                        nch += 1
                if nch:
                    print('[NOMI151] %d nomi presi dal banco (expander software)' % nch)
        except Exception as e:
            print('[NOMI151] override nomi:', e)
        return r

    P.load_midi_file = load_midi_file
    P._names151 = True
    print('[NOMI151] agganciato load_midi_file: nomi dal banco in modalita\' expander software')
    return True


def revert():
    pass


try:
    apply()
except Exception as _e:
    print('patch 151: %s' % _e)
