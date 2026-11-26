_VER = 2


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_265', '1')) == '0'
    except Exception:
        return False


def _versione_ok():
    try:
        from moduli.versione import APP_VERSION
    except Exception:
        try:
            from versione import APP_VERSION
        except Exception:
            return False
    try:
        return tuple(int(x) for x in str(APP_VERSION).strip().split('.')[:3]) >= (5, 3, 12)
    except Exception:
        return False


def apply():
    if _spenta() or not _versione_ok():
        return False
    try:
        from moduli import karadom_engine as eng
    except Exception:
        return False
    R = getattr(eng, '_Riproduzione', None)
    if R is None or getattr(R, '_buchi265', None) == _VER:
        return R is not None
    import collections, ctypes, time

    def _storia(self):
        d = self.__dict__.get('_diff_storia')
        if d is None:
            d = self.__dict__['_diff_storia'] = collections.deque(maxlen=40)
        return d

    def _riparti_orologio(self, t):
        _storia(self).clear()
        self.base_media = t
        self.base_muro = time.perf_counter() if not self.in_pausa else None

    def _spingi_audio(self, af, t):
        n = af.samples
        if n <= 0:
            return
        B = eng._Bass
        b = eng._bass.b
        src = self.sorgente or self.canale
        ptr = af.planes[0].buffer_ptr
        quando = self.adesso() + self._in_coda_audio()
        diff = t - quando
        salta = 0
        if self.base_muro is not None:
            st = _storia(self)
            if abs(diff) > 0.4:
                st.clear()
                if diff > 0:
                    sil = int(diff * B.RATE)
                    if sil > 0:
                        z = (ctypes.c_float * (sil * 2))()
                        b.BASS_StreamPutData(src, z, sil * 8)
                else:
                    salta = min(n, int(-diff * B.RATE))
            else:
                st.append(diff)
                if len(st) >= 30:
                    med = sorted(st)[len(st) // 2]
                    if abs(med) > 0.06:
                        with self.lock:
                            if self.base_muro is not None and not self.in_pausa:
                                self.base_muro -= med / max(self.rate, 0.05)
                        st.clear()
        if salta < n:
            b.BASS_StreamPutData(src, ctypes.c_void_p(ptr + salta * 8), (n - salta) * 8)
        self.t_fine_audio = t + n / float(B.RATE)

    def _coda_max(self):
        n = self.__dict__.get('_coda_max_n')
        if n is None:
            w, h = self.dim if self.dim and self.dim[0] else (1920, 1080)
            per_foto = max(1, int(w * h * 1.5))
            n = max(self.CODA_VIDEO * 4, min(int(3.0 * (self.fps or 30.0)), 300 * 2 ** 20 // per_foto))
            self.__dict__['_coda_max_n'] = n
        return n

    def _metti_video(self, foto, gen):
        while len(self.video) >= self.CODA_VIDEO and not self.fine.is_set():
            if self.salto_gen != gen:
                return
            if self.canale and self.primo_pronto.is_set() and not self.in_pausa \
                    and len(self.video) < _coda_max(self) and self._in_coda_audio() < 0.5:
                break
            time.sleep(0.004)
        self.video.append(foto)
        self.ultima_t = foto.t
        if not self.primo_pronto.is_set():
            self._primo(foto.t)
        if eng._schermo is not None:
            eng._schermo.sveglia.set()

    R._riparti_orologio = _riparti_orologio
    R._spingi_audio = _spingi_audio
    R._metti_video = _metti_video
    R._buchi265 = _VER
    print('patch 265: KaraDom Engine senza micro buchi (v%d)' % _VER)
    return True


try:
    apply()
except Exception as _e:
    print('patch 265: %s' % _e)
