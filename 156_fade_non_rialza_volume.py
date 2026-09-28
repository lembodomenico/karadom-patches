import ctypes


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_156', '1')) == '0'
    except Exception:
        return False


def apply():
    if _spenta():
        return False
    try:
        import moduli.bass_engine as BE
        import moduli.system as SYS
    except Exception as e:
        print('[FADE156] import:', e); return False

    Eng = getattr(BE, 'BassEngine', None)
    Sys = getattr(SYS, 'KaraokeMonitorSystem', None)
    if Eng is None or Sys is None:
        return False

    # --- motore: durante il fade blocca i RIALZI di volume; nuova base sblocca ---
    if not getattr(Eng, '_fadelock156', False):
        _smg = Eng.set_master_gain

        def set_master_gain(self, gain):
            try:
                if getattr(self, '_fade_lock', False):
                    if float(gain) > float(getattr(self, '_master_gain', 1.0)) + 1e-4:
                        return  # botta a volume pieno dopo il fade: IGNORATA
            except Exception:
                pass
            return _smg(self, gain)

        Eng.set_master_gain = set_master_gain

        _load = Eng.load

        def load(self, *a, **k):
            try:
                self._fade_lock = False   # nuova base: sblocca
            except Exception:
                pass
            return _load(self, *a, **k)

        Eng.load = load
        Eng._fadelock156 = True

    # --- system: all'avvio del fade arma il lock sui motori attivi ---
    if not getattr(Sys, '_fadelock156', False):
        _fade = Sys.fade_out

        def fade_out(self, duration_ms=3000):
            try:
                if duration_ms == 3000:   # durata di default del pulsante -> regolabile
                    from moduli.database import Database
                    duration_ms = int(float(Database.get_config('fade_ms', '5000')))
            except Exception:
                pass
            for nm in ('fs', 'bass_engine'):
                e = getattr(self, nm, None)
                if e is not None:
                    try:
                        e._fade_lock = True
                    except Exception:
                        pass
            return _fade(self, duration_ms)

        Sys.fade_out = fade_out
        Sys._fadelock156 = True

    print('[FADE156] fade-out non rialza piu\' il volume a fine dissolvenza')
    return True


def revert():
    pass


try:
    apply()
except Exception as _e:
    print('patch 156: %s' % _e)
