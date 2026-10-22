# 236 - video monitor pubblico senza salti

_VER = 1
_SOGLIA_MS = 600


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_236', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def _titolare():
    try:
        from moduli.licensing import load_license
        d = load_license() or {}
        return (str(d.get('nome', '')).strip().lower(),
                str(d.get('cognome', '')).strip().lower()) == ('domenico', 'lembo')
    except Exception:
        return False


def _filtra(engine):
    p = getattr(engine, 'vlc_player_pubblico', None)
    if p is None or getattr(p, '_ver236', None) == _VER:
        return
    vero = type(p).set_time

    def set_time(t):
        if getattr(engine, '_offset236', False):
            engine._offset236 = False
            return vero(p, t)
        try:
            cur = p.get_time()
            gira = p.is_playing()
        except Exception:
            cur, gira = -1, False
        if gira and cur > 0 and abs(int(t) - cur) <= _SOGLIA_MS:
            return 0
        return vero(p, t)

    p.set_time = set_time
    p._ver236 = _VER


def apply():
    if _spenta():
        return False
    if not _titolare():
        return True
    try:
        import moduli.engine as me
        import moduli.system as ms
        E = me.KaraokeTextEngine
        S = ms.KaraokeMonitorSystem
        if getattr(E, '_ver236', None) == _VER:
            return True
        setup0 = getattr(E, '_o236_setup', None) or E.setup_public_video_player
        E._o236_setup = setup0
        offset0 = getattr(S, '_o236_offset', None) or S.set_public_video_offset
        S._o236_offset = offset0

        def setup_public_video_player(self, *a, **k):
            ok = setup0(self, *a, **k)
            if ok:
                try:
                    _filtra(self)
                except Exception as e:
                    print('[236] %s' % e)
            return ok

        def set_public_video_offset(self, offset_ms):
            r = offset0(self, offset_ms)
            try:
                self.engine._offset236 = True
            except Exception:
                pass
            return r

        E.setup_public_video_player = setup_public_video_player
        S.set_public_video_offset = set_public_video_offset
        E._ver236 = _VER
        print('[236] monitor pubblico: riallineo solo oltre %d ms' % _SOGLIA_MS)
        return True
    except Exception as e:
        print('[236] %s' % e)
        return False
