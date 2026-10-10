# 203 - expander X-Light: lo strumento cambiato dal mixer resta anche quando il brano lo ricambia

_VER = 1


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_203', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def set_instrument_map(self, mapping):
    cur = getattr(self, 'instrument_map', None)
    if isinstance(cur, dict):
        nuovo = dict(mapping or {})
        cur.clear()
        cur.update(nuovo)
    else:
        self.instrument_map = dict(mapping or {})
    self._instrmap_loaded = True
    try:
        print('[STRUM203] sostituzioni attive: %d' % len(self.instrument_map))
    except Exception:
        pass


def apply():
    if _spenta():
        return False
    try:
        import moduli.fluidsynth_player as fp
        C = getattr(fp, 'FluidSynthPlayer', None)
        if C is None:
            return True
        if getattr(C, '_strum203', None) != _VER:
            C.set_instrument_map = set_instrument_map
            C._strum203 = _VER
        # la classe dell'expander fisico e' figlia di FluidSynthPlayer: se e' gia' nata e ha il suo, si allinea
        try:
            import moduli.expander_midi as em
            for v in list(vars(em).values()):
                if isinstance(v, type) and issubclass(v, C) and v is not C and 'set_instrument_map' in vars(v):
                    v.set_instrument_map = set_instrument_map
        except Exception:
            pass
        print('[STRUM203] mixer: lo strumento scelto resta anche sull expander')
    except Exception as e:
        print('[STRUM203] hook:', e)
    return True


def revert():
    pass


try:
    apply()
except Exception as _e:
    print('patch 203: %s' % _e)
