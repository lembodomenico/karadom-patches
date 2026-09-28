def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_149', '1')) == '0'
    except Exception:
        return False


def apply():
    if _spenta():
        return False
    try:
        import moduli.mixer as MX
    except Exception as e:
        print('[MUTE149] mixer non presente:', e); return False
    P = getattr(MX, 'MIDIMixerPanel', None) or getattr(MX, 'MidiMixerPanel', None)
    if P is None:
        print('[MUTE149] classe mixer non trovata'); return False
    if getattr(P, '_mute15_149', False):
        return True

    def _prog(ch):
        for key in ('orig_program', 'program', 'prog'):
            v = ch.get(key)
            if v is not None:
                return v
        return None

    _orig = P.load_midi_file
    def load_midi_file(self, *a, **k):
        r = _orig(self, *a, **k)
        try:
            chs = getattr(self, 'channels', None)
            if chs and len(chs) > 15:
                p14 = _prog(chs[14])   # canale 15 (0-based 14)
                p15 = _prog(chs[15])   # canale 16 (0-based 15)
                # muta il 15 SOLO se e' un doppione del 16 (stesso strumento)
                if p14 is not None and p14 == p15 and not chs[14].get('muted'):
                    self._toggle_mute(14)
                    print('[MUTE149] canale 15 = doppione del 16 -> mutato')
        except Exception as e:
            print('[MUTE149] check ch15:', e)
        return r
    P.load_midi_file = load_midi_file
    P._mute15_149 = True
    print('[MUTE149] muto selettivo canale 15 (solo se doppione)')
    return True


def revert():
    pass


try:
    apply()
except Exception as _e:
    print('patch 149: %s' % _e)
