import threading


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_180', '1')) == '0'
    except Exception:
        return False


def apply():
    if _spenta():
        return False
    try:
        import moduli.system as SYS
    except Exception as e:
        print('[FADE180] import:', e)
        return False
    Sys = getattr(SYS, 'KaraokeMonitorSystem', None)
    if Sys is None or getattr(Sys, '_autorelease180', False):
        return True
    _fade = getattr(Sys, 'fade_out', None)
    if _fade is None:
        return True

    def fade_out(self, duration_ms=3000):
        r = _fade(self, duration_ms)
        try:
            d = duration_ms
            if duration_ms == 3000:
                try:
                    from moduli.database import Database
                    d = int(float(Database.get_config('fade_ms', '5000')))
                except Exception:
                    pass

            def _libera():
                # il blocco dei rialzi (156) serve SOLO durante la dissolvenza.
                # Finita quella, lo tolgo: se no restava armato fino al cambio brano
                # e ogni risalita di volume (anche premendo un bottone) veniva
                # ignorata -> il volume si abbassava e non tornava piu' su.
                for nm in ('fs', 'bass_engine'):
                    e = getattr(self, nm, None)
                    if e is not None:
                        try:
                            e._fade_lock = False
                        except Exception:
                            pass
            t = threading.Timer(max(0.5, d / 1000.0 + 0.5), _libera)
            t.daemon = True
            t.start()
        except Exception as ex:
            print('[FADE180]', ex)
        return r

    Sys.fade_out = fade_out
    Sys._autorelease180 = True
    print('[FADE180] il blocco volume si libera da solo a fine dissolvenza')
    return True


try:
    apply()
except Exception as _e:
    print('patch 180: %s' % _e)
