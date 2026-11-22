# 261 - video tono vlc muto
_VER = 3


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_261', '1')) == '0'
    except Exception:
        return False


def apply():
    if _spenta():
        return False
    try:
        from moduli import vlc
    except Exception:
        import vlc
    try:
        from moduli import system as S
    except Exception:
        import moduli.system as S
    C = S.KaraokeMonitorSystem
    MP = vlc.MediaPlayer
    if getattr(MP, '_tono261', None) == _VER:
        return True
    if not hasattr(MP, '_tono261_o_mute'):
        MP._tono261_o_mute = MP.audio_set_mute
    if not hasattr(MP, '_tono261_o_toggle'):
        MP._tono261_o_toggle = MP.audio_toggle_mute
    import threading, time
    stato = {'sys': None}

    if not hasattr(C, '_tono261_o_init'):
        C._tono261_o_init = C.__init__

    def __init__(self, *a, **k):
        C._tono261_o_init(self, *a, **k)
        stato['sys'] = self
    C.__init__ = __init__

    def _sistema():
        s = stato['sys']
        if s is None and time.time() - stato.get('cerca', 0) > 5:
            stato['cerca'] = time.time()
            import gc
            for o in gc.get_objects():
                try:
                    if isinstance(o, C):
                        s = stato['sys'] = o
                        break
                except Exception:
                    pass
        return s

    def _altro_motore(player):
        s = _sistema()
        if s is None or getattr(getattr(s, 'engine', None), 'vlc_player', None) is not player:
            return False
        try:
            if getattr(s, 'is_bass_audio', False) and s.bass_engine is not None \
                    and s.bass_engine._get_channel_active() in (1, 2, 3):
                return True
        except Exception:
            pass
        return bool(getattr(s, 'is_mpv_audio', False) and getattr(s, '_video_pitch_active', False))

    def audio_set_mute(self, status):
        if not status and _altro_motore(self):
            return MP._tono261_o_mute(self, True)
        return MP._tono261_o_mute(self, status)

    def audio_toggle_mute(self):
        if _altro_motore(self):
            return MP._tono261_o_mute(self, True)
        return MP._tono261_o_toggle(self)

    MP.audio_set_mute = audio_set_mute
    MP.audio_toggle_mute = audio_toggle_mute
    MP._tono261 = _VER

    def _guardia():
        while getattr(MP, '_tono261', None) == _VER:
            time.sleep(0.2)
            try:
                s = _sistema()
                v = getattr(getattr(s, 'engine', None), 'vlc_player', None) if s is not None else None
                if v is None or not _altro_motore(v):
                    continue
                m = v.audio_get_mute()
                if m != 1:
                    MP._tono261_o_mute(v, True)
                if m == 0:
                    print('[TONO261] %s' % getattr(s, 'current_pitch', '?'))
            except Exception:
                pass
    if not getattr(MP, '_tono261_thread', False):
        MP._tono261_thread = True
        threading.Thread(target=_guardia, name='tono261', daemon=True).start()
    return True


def revert():
    pass


try:
    apply()
except Exception:
    pass
