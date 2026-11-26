import sys

_VER = 3
_METODI = "def _riparti_orologio(self, t):\n    self._diff_storia.clear()\n    self.base_media = t\n    self.base_muro = time.perf_counter() if not self.in_pausa else None\n\n\ndef _spingi_audio(self, af, t):\n    n = af.samples\n    if n <= 0:\n        return\n    src = self.sorgente or self.canale\n    ptr = af.planes[0].buffer_ptr\n    quando = self.adesso() + self._in_coda_audio()\n    diff = t - quando\n    salta = 0\n    if self.base_muro is not None:\n        if abs(diff) > 0.4:\n            self._diff_storia.clear()\n            if diff > 0:\n                sil = int(diff * _Bass.RATE)\n                if sil > 0:\n                    z = (ctypes.c_float * (sil * 2))()\n                    _bass.b.BASS_StreamPutData(src, z, sil * 8)\n            else:\n                salta = min(n, int(-diff * _Bass.RATE))\n        else:\n            self._diff_storia.append(diff)\n            if len(self._diff_storia) >= 30:\n                med = sorted(self._diff_storia)[len(self._diff_storia) // 2]\n                if abs(med) > 0.06:\n                    with self.lock:\n                        if self.base_muro is not None and (not self.in_pausa):\n                            self.base_muro -= med / max(self.rate, 0.05)\n                    self._diff_storia.clear()\n    if salta < n:\n        _bass.b.BASS_StreamPutData(src, ctypes.c_void_p(ptr + salta * 8), (n - salta) * 8)\n    self.t_fine_audio = t + n / float(_Bass.RATE)\n\n\ndef _leggi(self, cont):\n    import av\n    vs = None\n    if not self.lp._no_video_media:\n        for s in cont.streams.video:\n            try:\n                if s.disposition & av.stream.Disposition.attached_pic:\n                    continue\n            except Exception:\n                pass\n            vs = s\n            break\n    aus = cont.streams.audio[0] if cont.streams.audio else None\n    if not self.audio_on:\n        aus = None\n    self.ha_video, self.ha_audio = (vs is not None, aus is not None)\n    if cont.duration:\n        self.durata_ms = int(cont.duration / 1000)\n    t0 = (cont.start_time or 0) / 1000000.0 if cont.start_time not in (None,) else 0.0\n    dec = None\n    if vs is not None:\n        vs.thread_type = 'AUTO'\n        self.dim = (vs.codec_context.width, vs.codec_context.height)\n        self._candidati_hw = _candidati_hw(vs)\n        dec = self._prossimo_hw(vs)\n        try:\n            self.fps = float(vs.average_rate or vs.guessed_rate or 0)\n        except Exception:\n            self.fps = 0.0\n    if aus is not None:\n        if not self._apri_audio():\n            aus = None\n            self.ha_audio = False\n    res = av.AudioResampler(format='flt', layout='stereo', rate=_Bass.RATE) if aus else None\n    flussi = [s for s in (vs, aus) if s is not None]\n    if not flussi:\n        self.errore = 'niente da riprodurre'\n        self.lp._cambia_stato(State.Error)\n        return\n    self.lp._lunghezza_nota(self.durata_ms)\n    passo = 1.0 / self.fps if self.fps > 0 else 0.04\n    gen_vista = self.salto_gen\n    if self.base_media > 0.05:\n        self.salto = self.base_media\n        self.salto_gen += 1\n    while not self.fine.is_set():\n        bersaglio = None\n        with self.lock:\n            if self.salto is not None and self.salto_gen != gen_vista:\n                bersaglio, gen_vista = (self.salto, self.salto_gen)\n        if bersaglio is not None:\n            self.video.clear()\n            self.primo_pronto.clear()\n            self.letto_tutto = False\n            rif = vs or aus\n            try:\n                cont.seek(int((bersaglio + t0) / rif.time_base), stream=rif, backward=True, any_frame=False)\n            except Exception as e:\n                _log('salto: %s' % e)\n            for s in flussi:\n                try:\n                    s.codec_context.flush_buffers()\n                except Exception:\n                    pass\n            if dec is not None:\n                try:\n                    dec.flush_buffers()\n                except Exception:\n                    pass\n            if res is not None:\n                res = av.AudioResampler(format='flt', layout='stereo', rate=_Bass.RATE)\n            self._t_audio_dopo = None\n            self._riordino = []\n            self._t_video_messo = None\n            self._svuota_audio()\n        try:\n            pkt = next(self._demux_iter(cont, flussi, bersaglio is not None))\n        except StopIteration:\n            self._svuota_riordino(gen_vista)\n            self.letto_tutto = True\n            self._fine_lettura()\n            if self.fine.is_set():\n                break\n            continue\n        if pkt.stream is vs:\n            try:\n                if dec is not None:\n                    pkt_tb = pkt.time_base\n                    fotos = dec.decode(pkt)\n                else:\n                    fotos = pkt.decode()\n            except Exception as e:\n                if dec is None:\n                    raise\n                _log('decodifica con %s fallita (%s): cambio' % (self.decoder, e))\n                dec = self._prossimo_hw(vs)\n                self.salta(max(0.0, self.adesso()))\n                continue\n            for fr in fotos:\n                if dec is not None and fr.time is None and (fr.pts is not None):\n                    fr.time_base = pkt_tb\n                t = fr.time - t0 if fr.time is not None else self.ultima_t + passo\n                if self.salto is not None and t < self.salto - passo * 0.5:\n                    continue\n                self._metti_in_ordine(_Foto(fr, t), gen_vista)\n        elif aus is not None and pkt.stream is aus:\n            if self.lp._muto and self.primo_pronto.is_set():\n                continue\n            t_pkt = float(pkt.pts * pkt.time_base) if pkt.pts is not None else None\n            for fr in pkt.decode():\n                if fr.time is not None:\n                    t = fr.time - t0\n                elif self._t_audio_dopo is not None:\n                    t = self._t_audio_dopo\n                else:\n                    t = (t_pkt if t_pkt is not None else 0.0) - t0\n                self._t_audio_dopo = t + fr.samples / float(fr.sample_rate or 1)\n                if self.salto is not None and t + fr.samples / float(fr.sample_rate or 1) < self.salto:\n                    continue\n                for o in res.resample(fr):\n                    self._spingi_audio(o, t)\n                    t += o.samples / float(_Bass.RATE)\n            if vs is None:\n                self._primo(self.salto if self.salto is not None else self.base_media)\n                while not self.fine.is_set() and self.salto_gen == gen_vista and self.canale and (self._in_coda_audio() > 1.0):\n                    time.sleep(0.02)\n\n\ndef _metti_in_ordine(self, foto, gen):\n    if not self._disordine:\n        if self._t_video_messo is not None and foto.t < self._t_video_messo - 1e-06:\n            self._disordine = True\n            _log('fotogrammi fuori ordine nel file: li rimetto in fila')\n            return\n        self._t_video_messo = foto.t\n        self._metti_video(foto, gen)\n        return\n    self._riordino.append(foto)\n    self._riordino.sort(key=lambda f: f.t)\n    while len(self._riordino) > 3:\n        self._esci_dal_riordino(gen)\n\n\ndef _esci_dal_riordino(self, gen):\n    f = self._riordino.pop(0)\n    if self._t_video_messo is None or f.t >= self._t_video_messo - 1e-06:\n        self._t_video_messo = f.t\n        self._metti_video(f, gen)\n\n\ndef _svuota_riordino(self, gen):\n    while self._riordino:\n        self._esci_dal_riordino(gen)\n\n\ndef _coda_max(self):\n    n = self.__dict__.get('_coda_max_n')\n    if n is None:\n        w, h = self.dim if self.dim and self.dim[0] else (1920, 1080)\n        per_foto = max(1, int(w * h * 1.5))\n        n = max(self.CODA_VIDEO * 4, min(int(3.0 * (self.fps or 30.0)), 300 * 2 ** 20 // per_foto))\n        self.__dict__['_coda_max_n'] = n\n    return n\n\n\ndef _metti_video(self, foto, gen):\n    while len(self.video) >= self.CODA_VIDEO and (not self.fine.is_set()):\n        if self.salto_gen != gen:\n            return\n        if self.canale and self.primo_pronto.is_set() and (not self.in_pausa) and (len(self.video) < self._coda_max()) and (self._in_coda_audio() < 0.5):\n            break\n        time.sleep(0.004)\n    self.video.append(foto)\n    self.ultima_t = foto.t\n    if not self.primo_pronto.is_set():\n        self._primo(foto.t)\n    if _schermo is not None:\n        _schermo.sveglia.set()\n"


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
    if R is None:
        return False
    if getattr(R, '_buchi265', None) == _VER:
        return True
    ns = {}
    exec(compile(_METODI, 'karadom_engine_265', 'exec'), eng.__dict__, ns)
    for nome in ('_riparti_orologio', '_spingi_audio', '_leggi', '_metti_in_ordine', '_esci_dal_riordino', '_svuota_riordino', '_coda_max', '_metti_video'):
        setattr(R, nome, ns[nome])
    leggi = ns['_leggi']

    def _leggi(self, cont):
        import collections
        d = self.__dict__
        d.setdefault('_diff_storia', collections.deque(maxlen=40))
        d.setdefault('_t_audio_dopo', None)
        d.setdefault('_riordino', [])
        d.setdefault('_disordine', False)
        d.setdefault('_t_video_messo', None)
        return leggi(self, cont)

    def _riparti_orologio(self, t):
        import collections
        self.__dict__.setdefault('_diff_storia', collections.deque(maxlen=40))
        return ns['_riparti_orologio'](self, t)

    R._leggi = _leggi
    R._riparti_orologio = _riparti_orologio
    R._buchi265 = _VER
    print('patch 265: KaraDom Engine v%d (buchi, WMV, copertine, fotogrammi in ordine)' % _VER)
    return True


try:
    apply()
except Exception as _e:
    print('patch 265: %s' % _e)
