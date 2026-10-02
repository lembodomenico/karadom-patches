def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_181', '1')) == '0'
    except Exception:
        return False


def apply():
    if _spenta():
        return False
    try:
        import moduli.system as SYS
    except Exception as e:
        print('[EXT181] import:', e)
        return False
    S = getattr(SYS, 'KaraokeMonitorSystem', None)
    if S is None or not hasattr(S, 'load_file') or getattr(S, '_extmute181', False):
        return True
    _orig = S.load_file

    def load_file(self, *a, **k):
        # Aprendo un file da FUORI (doppio clic da Esplora risorse) con lancio
        # fresco, load_file gira PRIMA che il mixer sia agganciato (mixer_ref=None):
        # cosi' load_midi_file (nomi strumenti + mute CH4) viene saltata e la
        # melodia resta non mutata, nomi "---". Se il mixer NON c'era, appena
        # compare gli faccio applicare il brano una volta (nomi + mute CH4).
        had = bool(getattr(self, 'mixer_ref', None))
        r = _orig(self, *a, **k)
        try:
            if r and getattr(self, 'is_midi', False) and not had:
                fp = a[0] if a else k.get('file_path')
                self._ext181_n = 0

                def _applica():
                    try:
                        mx = getattr(self, 'mixer_ref', None)
                        cf = getattr(self, 'current_file', None) or fp
                        # solo se e' ancora lo stesso brano e il mixer e' pronto
                        if mx is not None and getattr(self, 'is_midi', False) \
                                and cf and cf == getattr(self, 'current_file', None):
                            mx.load_midi_file(cf, melody_muted=True)
                            print('[EXT181] apertura esterna: nomi + mute CH4 applicati')
                            return
                    except Exception as e:
                        print('[EXT181] applica:', e)
                    self._ext181_n += 1
                    if self._ext181_n < 40:   # riprova fino a ~10 s, poi molla
                        try:
                            self.master.after(250, _applica)
                        except Exception:
                            pass
                try:
                    self.master.after(250, _applica)
                except Exception:
                    pass
        except Exception as e:
            print('[EXT181]', e)
        return r

    S.load_file = load_file
    S._extmute181 = True
    print('[EXT181] apertura esterna: muta CH4 appena il mixer e\' pronto')
    return True


try:
    apply()
except Exception as _e:
    print('patch 181: %s' % _e)
