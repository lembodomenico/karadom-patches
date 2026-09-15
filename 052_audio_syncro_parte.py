# 052 - audio syncro

import moduli.syncro_text as st


class _AudioMPV:
    def __init__(self, mp):
        self._mp = mp
        self._path = None
        self._loaded = False

    def media_new(self, path):
        return path

    def set_media(self, m):
        self._path = m
        self._loaded = False
        if m is None:
            try:
                self._mp.command('stop')
            except Exception:
                pass

    def play(self):
        try:
            if self._path and not self._loaded:
                self._mp.play(self._path)
                self._loaded = True
            else:
                self._mp.pause = False
        except Exception:
            pass
        return 0

    def pause(self):
        try:
            self._mp.pause = True
        except Exception:
            pass

    def stop(self):
        try:
            self._mp.command('stop')
        except Exception:
            try:
                self._mp.pause = True
            except Exception:
                pass
        self._loaded = False

    def get_length(self):
        try:
            d = self._mp.duration
            return int(d * 1000) if d else 0
        except Exception:
            return 0

    def get_time(self):
        try:
            t = self._mp.time_pos
            return int(t * 1000) if t is not None else -1
        except Exception:
            return -1

    def set_time(self, ms):
        try:
            self._mp.time_pos = max(0, ms) / 1000.0
        except Exception:
            pass

    def get_state(self):
        try:
            if self._mp.pause:
                return st.vlc.State.Paused
            if self._mp.time_pos is None:
                return st.vlc.State.Opening
            if getattr(self._mp, 'eof_reached', False):
                return st.vlc.State.Ended
            return st.vlc.State.Playing
        except Exception:
            return st.vlc.State.NothingSpecial


def _init_vlc(self):
    try:
        import mpv
        mp = mpv.MPV(vid=False, volume=100, log_handler=lambda *a: None)
        try:
            mp['audio-pitch-correction'] = 'yes'
        except Exception:
            pass
        self.vlc_instance = _AudioMPV(mp)
        self.vlc_player = self.vlc_instance
        return
    except Exception:
        pass
    if not st.HAS_VLC:
        self.vlc_instance = None
        self.vlc_player = None
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
    if not self.vlc_player:
        self._init_vlc()
    if not self.vlc_player:
        st.messagebox.showerror(st._("Errore"), st._("Motore audio non inizializzato."), parent=self.window)
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
        r = _orig(self)
        try:
            if self.is_syncing:
                self.window.bind('<Return>', lambda e: (self._mark_timestamp(), 'break')[1])
                self.window.bind('<BackSpace>', lambda e: (self._undo_last(), 'break')[1])
                self.window.bind('<Escape>', lambda e: (self._stop_sync(), 'break')[1])
        except Exception:
            pass
        return r
    _start_sync._p052 = True
    return _start_sync


def _mark_timestamp(self):
    if not self.is_syncing or self.current_unit >= len(self.units):
        return
    if hasattr(self, '_sync_perf_start'):
        ct = int(self._sync_vlc_base + (st.time.perf_counter() - self._sync_perf_start) * 1000)
    else:
        ct = self.vlc_player.get_time()
    if ct < 0:
        ct = 0
    if self.current_unit > 0:
        pt = self.units[self.current_unit - 1]['timestamp']
        if pt is not None and ct <= pt:
            ct = pt + 1
    self.units[self.current_unit]['timestamp'] = ct
    self.current_unit += 1
    self._sync_resync_counter = getattr(self, '_sync_resync_counter', 0) + 1
    if self._sync_resync_counter >= 20:
        self._sync_resync_counter = 0
        vt = self.vlc_player.get_time()
        if vt > 0:
            self._sync_vlc_base = vt
            self._sync_perf_start = st.time.perf_counter()
    if self.current_unit >= len(self.units):
        self._finish_sync()
        return
    self._refresh_syllable_colors()
    self._update_detail_panel()
    self._update_counter()


def _create_ui(self):
    tk = st.tk
    ttk = st.ttk
    S = st.S
    F = st.F
    _ = st._
    bg = '#2b2b2b'
    bg_dark = '#1e1e1e'
    fg = '#ffffff'
    accent = '#c8a94e'
    btn_bg = '#3a3a3a'

    def tbtn(parent, text, cmd, base=btn_bg, fgc=fg, font=None, **kw):
        b = tk.Button(parent, text=text, command=cmd, bg=base, fg=fgc,
                      activebackground=accent, activeforeground='#1e1e1e',
                      relief='flat', cursor='hand2', bd=0,
                      font=font or F("Segoe UI", 10, "bold"), **kw)
        b.bind('<Enter>', lambda e, w=b: w.config(bg='#4a4a4a') if w['bg'] == base else None)
        b.bind('<Leave>', lambda e, w=b: w.config(bg=base))
        return b

    toolbar = tk.Frame(self.window, bg=bg_dark, height=S(46))
    toolbar.pack(fill='x')
    toolbar.pack_propagate(False)

    tbtn(toolbar, _("📂 Testo"), self._open_text_file).pack(side='left', padx=(S(6), S(2)), pady=S(7))
    tbtn(toolbar, "🎵 Import", self._import_from_audio).pack(side='left', padx=S(2), pady=S(7))
    self.btn_edit = tbtn(toolbar, _("✏️ Modifica Testo"), self._open_edit_window, base='#555500', fgc='#ffe066')
    self.btn_edit.pack(side='left', padx=S(2), pady=S(7))
    self.btn_edit_inline = tbtn(toolbar, _("📝 Edita Testo"), self._toggle_edit_mode, base='#1f3a5f', fgc='#bfe0ff')
    self.btn_edit_inline.pack(side='left', padx=S(2), pady=S(7))
    self._edit_mode = False
    self.btn_save = tbtn(toolbar, _("💾 Salva MP3"), self._save_sylt_manual, base='#006622', fgc='#ffffff')
    self.btn_save.pack(side='left', padx=S(2), pady=S(7))
    self.btn_reload = tbtn(toolbar, "🔄", self._reload_text, font=F("Segoe UI", 12))
    self.btn_reload.pack(side='left', padx=S(2), pady=S(7))

    tk.Label(toolbar, text="Font", bg=bg_dark, fg='#e8e8e8',
            font=F("Segoe UI", 9)).pack(side='left', padx=(S(14), S(3)))
    self.font_size_var = tk.StringVar(value="18")
    ttk.Combobox(toolbar, textvariable=self.font_size_var,
                 values=["12", "14", "16", "18", "20", "24", "28"],
                 state='readonly', width=3, font=F("Segoe UI", 9)
                 ).pack(side='left', padx=S(2), pady=S(7))
    self.window.after(100, lambda: self.font_size_var.trace_add('write', lambda *a: self._apply_font_size()))

    self.btn_load_audio = tbtn(toolbar, _("🔊 Carica Audio"), self._load_audio, base='#4a4a2a', fgc=accent)
    self.btn_load_audio.pack(side='right', padx=(S(4), S(8)), pady=S(7))
    self.audio_label = tk.Label(toolbar, text=_("Nessun audio"), bg=bg_dark, fg='#e8e8e8', font=F("Segoe UI", 9))
    self.audio_label.pack(side='right', padx=S(6))
    self.pos_label = tk.Label(toolbar, text="00:00 / 00:00", bg=bg_dark, fg=accent, font=F("Consolas", 12, "bold"))
    self.pos_label.pack(side='right', padx=S(10))

    body = tk.Frame(self.window, bg=bg)
    body.pack(fill='both', expand=True, padx=S(6), pady=S(6))

    right = tk.Frame(body, bg=bg, width=S(360))
    right.pack(side='right', fill='y', padx=(S(6), 0))
    right.pack_propagate(False)

    def section(title):
        tk.Frame(right, bg='#3a3a3a', height=S(1)).pack(fill='x', padx=S(6), pady=(S(8), S(3)))
        tk.Label(right, text=title, bg=bg, fg=accent,
                font=F("Segoe UI", 9, "bold")).pack(anchor='w', padx=S(8))

    section(_("RIPRODUZIONE"))
    self.btn_play = tk.Button(right, text="▶  Play / Pausa", font=F("Segoe UI", 12, "bold"),
                             command=self._toggle_play_pause, bg='#00666a', fg='#ffffff',
                             activebackground='#008a90', activeforeground='#fff',
                             cursor='hand2', relief='flat', bd=0, height=2)
    self.btn_play.pack(fill='x', padx=S(6), pady=S(3))
    nav = tk.Frame(right, bg=bg)
    nav.pack(fill='x', padx=S(6), pady=S(2))
    tk.Button(nav, text="◀◀ 5s", font=F("Segoe UI", 11, "bold"),
             command=lambda: self._seek_relative(-5000), bg='#2a4a8a', fg='#fff',
             activebackground='#3a5aaa', relief='flat', bd=0, cursor='hand2'
             ).pack(side='left', expand=True, fill='x', padx=(0, S(2)), ipady=S(4))
    tk.Button(nav, text="5s ▶▶", font=F("Segoe UI", 11, "bold"),
             command=lambda: self._seek_relative(5000), bg='#2a4a8a', fg='#fff',
             activebackground='#3a5aaa', relief='flat', bd=0, cursor='hand2'
             ).pack(side='right', expand=True, fill='x', padx=(S(2), 0), ipady=S(4))

    section(_("SINCRONIZZAZIONE"))
    self.btn_start = tk.Button(right, text=_("▶  INIZIA SYNCRO"), font=F("Segoe UI", 13, "bold"),
                               command=self._start_sync, bg='#00842f', fg='#ffffff',
                               activebackground='#00a83c', activeforeground='#fff',
                               cursor='hand2', relief='flat', bd=0, height=2)
    self.btn_start.pack(fill='x', padx=S(6), pady=(S(3), S(3)))
    self.btn_rec = tk.Button(right, text="●  TAP  [Invio]", font=F("Segoe UI", 12, "bold"),
                            command=self._mark_timestamp, bg='#cc0000', fg='#fff',
                            activebackground='#ee0000', cursor='hand2', relief='flat', bd=0,
                            height=2, state='disabled')
    self.btn_rec.pack(fill='x', padx=S(6), pady=S(2))
    rowbs = tk.Frame(right, bg=bg)
    rowbs.pack(fill='x', padx=S(6), pady=S(2))
    self.btn_back = tk.Button(rowbs, text="↩ Indietro", font=F("Segoe UI", 10, "bold"),
                             command=self._undo_last, bg='#b35900', fg='#fff',
                             activebackground='#d46b00', cursor='hand2', relief='flat', bd=0,
                             state='disabled')
    self.btn_back.pack(side='left', expand=True, fill='x', padx=(0, S(2)), ipady=S(4))
    self.btn_stop = tk.Button(rowbs, text="✖ Stop", font=F("Segoe UI", 10, "bold"),
                             command=self._stop_sync, bg='#7a2a7a', fg='#fff',
                             activebackground='#9a3a9a', cursor='hand2', relief='flat', bd=0,
                             state='disabled')
    self.btn_stop.pack(side='right', expand=True, fill='x', padx=(S(2), 0), ipady=S(4))
    self.btn_fix_ts = tk.Button(right, text="🔧 Correggi tempi", font=F("Segoe UI", 10, "bold"),
                                command=self._fix_timestamps_ui, bg='#444', fg='#fff',
                                activebackground='#555', cursor='hand2', relief='flat', bd=0,
                                state='disabled')
    self.btn_fix_ts.pack(fill='x', padx=S(6), pady=(S(2), S(4)))

    section(_("SILLABA SELEZIONATA"))
    self.detail_syl_label = tk.Label(right, text="---", bg='#1a1a1a', fg=accent,
                                      font=F("Arial", 26, "bold"), relief='flat', bd=0, height=2)
    self.detail_syl_label.pack(fill='x', padx=S(6), pady=S(4))

    ms_f = tk.Frame(right, bg=bg)
    ms_f.pack(fill='x', padx=S(6), pady=S(2))
    tk.Label(ms_f, text="ms:", bg=bg, fg=fg, font=F("Segoe UI", 10, "bold"), width=6, anchor='w').pack(side='left')
    self.detail_ms_entry = tk.Entry(ms_f, bg='#1a1a1a', fg='#66ff66',
                                     font=F("Consolas", 14, "bold"), width=10,
                                     relief='flat', insertbackground='#66ff66', justify='center')
    self.detail_ms_entry.pack(side='left', fill='x', expand=True, ipady=S(3))
    self.detail_ms_entry.bind('<Return>', self._on_ms_edit)

    tf = tk.Frame(right, bg=bg)
    tf.pack(fill='x', padx=S(6), pady=S(2))
    tk.Label(tf, text="tempo:", bg=bg, fg=fg, font=F("Segoe UI", 10, "bold"), width=6, anchor='w').pack(side='left')
    self.detail_time_entry = tk.Entry(tf, bg='#1a1a1a', fg='#66d9ff',
                                       font=F("Consolas", 14, "bold"), width=10,
                                       relief='flat', insertbackground='#66d9ff', justify='center')
    self.detail_time_entry.pack(side='left', fill='x', expand=True, ipady=S(3))
    self.detail_time_entry.bind('<Return>', self._on_time_edit)

    self.counter_label = tk.Label(right, text="", bg=bg, fg=accent, font=F("Consolas", 11, "bold"))
    self.counter_label.pack(pady=S(4))

    self.info_label = tk.Label(right, text=_("Inserisci il testo, carica l'audio,\npoi premi INIZIA SYNCRO"),
                               bg=bg, fg='#ffffff', font=F("Segoe UI", 10), wraplength=S(320), justify='center')
    self.info_label.pack(padx=S(6), pady=S(6))

    left = tk.Frame(body, bg=bg)
    left.pack(side='left', fill='both', expand=True, padx=(0, S(6)))

    self.text_editor = tk.Text(left, wrap='word', font=F("Arial", 18, "bold"),
                               bg='#1a1a1a', fg='#ffffff', insertbackground='#ffffff',
                               selectbackground='#3399ff', relief='flat', bd=0,
                               padx=S(12), pady=S(12), undo=True, spacing1=S(4), spacing3=S(4))
    tsb = tk.Scrollbar(left, command=self.text_editor.yview)
    tsb.pack(side='right', fill='y')
    self.text_editor.config(yscrollcommand=tsb.set)
    self.text_editor.pack(fill='both', expand=True)

    self.text_editor.tag_configure('synced', foreground='#ff3b3b')
    self.text_editor.tag_configure('current', foreground='#1e1e1e', background=accent, underline=True)
    self.text_editor.tag_configure('unsynced', foreground='#ffffff')
    self.text_editor.tag_configure('sep', foreground='#888888')


try:
    st.SyncroText._init_vlc = _init_vlc
    st.SyncroText._load_audio_file = _load_audio_file
    st.SyncroText._create_ui = _create_ui
    st.SyncroText._mark_timestamp = _mark_timestamp
    if not getattr(st.SyncroText._start_sync, '_p052', False):
        st.SyncroText._start_sync = _fai_start_sync(st.SyncroText._start_sync)
except Exception:
    pass
