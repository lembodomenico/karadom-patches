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


try:
    st.SyncroText._init_vlc = _init_vlc
    st.SyncroText._load_audio_file = _load_audio_file
except Exception:
    pass
