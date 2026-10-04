# 192 - stop video sicuro
def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_192', '1')) == '0'
    except Exception:
        return False


import threading

VER = 1
TETTO = 1.0

_GETTER = {
    'is_playing': 0, 'will_play': 0, 'get_time': 0, 'get_length': 0,
    'get_position': 0.0, 'get_media': None, 'audio_get_volume': 0,
    'audio_get_mute': 0, 'get_rate': 1.0, 'video_get_size': (0, 0),
}
_AZIONI = ('play', 'pause', 'set_pause', 'set_time', 'set_position',
           'set_hwnd', 'set_xwindow', 'audio_set_mute', 'audio_set_volume',
           'set_rate')


def installa(vlc_mod):
    MP = getattr(vlc_mod, 'MediaPlayer', None)
    if MP is None:
        return False
    if getattr(MP, '_stop_sicuro_ver', None) == VER:
        return True

    def originale(nome):
        o = getattr(MP, '_ss_o_' + nome, None)
        if o is None:
            o = getattr(MP, nome, None)
            if o is not None:
                setattr(MP, '_ss_o_' + nome, o)
        return o

    o_set_media = originale('set_media')
    o_stop = originale('stop')
    o_release = originale('release')
    if o_set_media is None or o_stop is None or o_release is None:
        return False

    try:
        stato_ferma = vlc_mod.State.Stopped
    except Exception:
        stato_ferma = 5
    try:
        principale = threading.main_thread()
    except Exception:
        principale = None

    def set_media(self, p_md):
        if getattr(self, '_ss_parte', False):
            return None
        try:
            self._ss_mrl = p_md.get_mrl() if p_md is not None else ''
        except Exception:
            self._ss_mrl = ''
        return o_set_media(self, p_md)

    def stop(self):
        if getattr(self, '_ss_parte', False):
            return None
        if threading.current_thread() is not principale or not getattr(self, '_ss_mrl', ''):
            return o_stop(self)
        fatto = threading.Event()

        def _lavora():
            try:
                o_stop(self)
            except Exception:
                pass
            fatto.set()
            if getattr(self, '_ss_parte', False):
                if getattr(self, '_ss_da_rilasciare', False):
                    try:
                        o_release(self)
                    except Exception:
                        pass
                print('[VLC-STOP] video chiuso in disparte')

        threading.Thread(target=_lavora, daemon=True, name='vlc-stop-rete').start()
        if fatto.wait(TETTO):
            return None
        self._ss_parte = True
        print(f'[VLC-STOP] stop appeso oltre {TETTO:.1f}s su {self._ss_mrl[:60]} -> messo da parte')
        return None

    def release(self):
        if getattr(self, '_ss_parte', False):
            self._ss_da_rilasciare = True
            return None
        return o_release(self)

    def _innocuo(nome, valore):
        o = originale(nome)
        if o is None:
            return None

        def f(self, *a, **k):
            if getattr(self, '_ss_parte', False):
                return valore
            return o(self, *a, **k)
        f.__name__ = nome
        return f

    MP.set_media = set_media
    MP.stop = stop
    MP.release = release
    for nome, val in _GETTER.items():
        f = _innocuo(nome, val)
        if f is not None:
            setattr(MP, nome, f)
    for nome in _AZIONI:
        f = _innocuo(nome, 0)
        if f is not None:
            setattr(MP, nome, f)
    f = _innocuo('get_state', stato_ferma)
    if f is not None:
        MP.get_state = f
    MP._stop_sicuro_ver = VER
    return True


def apply():
    if _spenta():
        return False
    import sys
    v = sys.modules.get('moduli.vlc')
    if v is None:
        try:
            from moduli import vlc as v
        except Exception:
            try:
                import vlc as v
            except Exception:
                return False
    return installa(v)
