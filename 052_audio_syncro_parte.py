# 052 - audio syncro

import moduli.syncro_text as st


def _init_vlc(self):
    if not st.HAS_VLC:
        return
    try:
        self.vlc_instance = st.vlc.Instance(
            '--audio-resampler=soxr', '--no-video-title-show', '--quiet',
            '--audio-time-stretch', '--no-metadata-network-access', '--no-lua')
        self.vlc_player = self.vlc_instance.media_player_new()
    except Exception:
        self.vlc_instance = None
        self.vlc_player = None


def _load_audio_file(self, fp):
    if not st.HAS_VLC:
        st.messagebox.showerror(st._("Errore"), st._("VLC non disponibile."), parent=self.window)
        return
    if not self.vlc_player:
        self._init_vlc()
    if not self.vlc_player:
        st.messagebox.showerror(st._("Errore"), st._("Motore audio VLC non inizializzato."), parent=self.window)
        return
    try:
        media = self.vlc_instance.media_new(fp.replace('\\', '/'))
        self.vlc_player.set_media(media)
        self.audio_file = st.os.path.normpath(fp)
        self.vlc_player.play()
        st.time.sleep(0.5)
        self.vlc_player.pause()
        dur = 0
        for _u_i in range(20):
            dur = self.vlc_player.get_length()
            if dur > 0:
                break
            st.time.sleep(0.1)
        self.audio_duration_ms = dur if dur > 0 else 0
        self.vlc_player.set_time(0)
        nm = st.os.path.basename(fp)
        ds = self.audio_duration_ms // 1000
        self.audio_label.config(text="\U0001F50A %s (%d:%02d)" % (nm, ds // 60, ds % 60))
        self._start_pos_update()
        if fp.lower().endswith('.mp3'):
            self._try_load_existing_sylt(fp)
    except Exception as e:
        st.messagebox.showerror(st._("Errore"), "%s" % e, parent=self.window)


def _riconcilia_testo(self):
    import re as _re
    vis = self._strip_syllabic_dashes(self.text_editor.get('1.0', 'end-1c')).strip()
    if not vis:
        return
    _n = lambda s: _re.sub(r'\s+', ' ', s or '').strip()
    plain_units = self._strip_syllabic_dashes(self._units_to_plain_text()) if self.units else ''
    if _n(vis) != _n(plain_units):
        self.text_editor.config(state='normal')
        self.units = st._parse_syllables(vis)
        self.current_unit = 0


def _fai_start_sync(_orig):
    def _start_sync(self):
        try:
            _riconcilia_testo(self)
        except Exception:
            pass
        return _orig(self)
    _start_sync._p052 = True
    return _start_sync


try:
    st.SyncroText._init_vlc = _init_vlc
    st.SyncroText._load_audio_file = _load_audio_file
    if not getattr(st.SyncroText._start_sync, '_p052', False):
        st.SyncroText._start_sync = _fai_start_sync(st.SyncroText._start_sync)
except Exception:
    pass
