import sys, os


def apply():
    fp = sys.modules.get('moduli.fluidsynth_player')
    if fp is None:
        try:
            import moduli.fluidsynth_player as fp  # noqa
        except Exception:
            print('[RR161] fluidsynth_player non presente (ok)')
            return False
    C = getattr(fp, 'FluidSynthPlayer', None)
    if C is None:
        return True

    def _scope():
        """Ambito della rimappa: 'exp' se l'expander pilota l'audio, altrimenti
        il nome del file SF2 corrente. Così ogni SF2 ha la SUA rimappa e
        l'expander la sua, senza travaso."""
        try:
            from moduli.expander_midi import is_active as _exp_active
            if _exp_active():
                return "exp"
        except Exception:
            pass
        try:
            from moduli.database import Database
            sf = Database.get_config('soundfont_path', '') or ''
        except Exception:
            sf = ''
        base = os.path.basename(sf).strip()
        return base if base else "default"

    def _key():
        return "mixer_instr_remap::" + _scope()

    @staticmethod
    def load_instrument_remap():
        try:
            from moduli.database import Database
            import json
            raw = Database.get_config(_key(), '')
            if not raw:
                return {}
            data = json.loads(raw)
            out = {}
            for k, v in data.items():
                pre, p, b = k.split(':')
                out[(pre == 'd', int(p), int(b))] = (int(v[0]), int(v[1]))
            return out
        except Exception:
            return {}

    @staticmethod
    def save_instrument_remap(mapping):
        try:
            from moduli.database import Database
            import json
            data = {}
            for (is_drum, p, b), nv in (mapping or {}).items():
                data["%s:%d:%d" % ('d' if is_drum else 'm', int(p), int(b))] = [int(nv[0]), int(nv[1])]
            Database.set_config(_key(), json.dumps(data))
            return True
        except Exception as e:
            print("[RR161] save_instrument_remap: %s" % e)
            return False

    C.load_instrument_remap = load_instrument_remap
    C.save_instrument_remap = save_instrument_remap
    print('[RR161] rimappa strumenti mixer PER-BANCO SF2 + expander separato')
    return True


try:
    apply()
except Exception as _e:
    print('patch 161: %s' % _e)
