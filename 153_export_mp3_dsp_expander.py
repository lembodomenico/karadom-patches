import os
def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_153', '1')) == '0'
    except Exception:
        return False


def _norm(p):
    try:
        return os.path.normcase(os.path.abspath(str(p)))
    except Exception:
        return str(p or '')


def apply():
    if _spenta():
        return False
    try:
        import moduli.midi_mp3_exporter as M
    except Exception as e:
        print('[MP3DSP153] exporter assente:', e); return False
    Exp = getattr(M, 'MidiMp3Exporter', None)
    if Exp is None or getattr(Exp, '_dsp153', False):
        return True
    _orig = Exp.__init__

    def __init__(self, *a, **k):
        _orig(self, *a, **k)
        # se il render usa il BANCO DELL'EXPANDER, applica la DSP dell'expander sw
        # (volume/bassi/brillantezza/riverbero) come quando suona dal vivo.
        try:
            from moduli.database import Database
            eb = Database.get_config('exp_banco_path', '') or ''
            sf = _norm(getattr(self, 'soundfont_path', ''))
            base = os.path.basename(sf).lower()
            is_exp = (eb and sf == _norm(eb)) or ('kdl hd' in base) or ('kdl pieno' in base) or base.endswith('.kdl')
            if is_exp:
                self._soft_fx = True
                print('[MP3DSP153] banco expander rilevato -> applico Bassi/Brillantezza/Riverbero al render')
        except Exception as e:
            print('[MP3DSP153] init:', e)

    Exp.__init__ = __init__
    Exp._dsp153 = True
    print('[MP3DSP153] export MP3: DSP expander automatica col banco expander')
    return True


def revert():
    pass


try:
    apply()
except Exception as _e:
    print('patch 153: %s' % _e)
