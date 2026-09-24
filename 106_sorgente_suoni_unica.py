import os


def _cfg_get(chiave, default=''):
    try:
        from moduli.database import Database
        v = Database.get_config(chiave, default)
        return v if v not in (None, '') else default
    except Exception:
        return default


def _int(v, d):
    try:
        return int(float(v))
    except Exception:
        return d


def _sf2_nome():
    sf = _cfg_get('soundfont_path', '')
    if sf and os.path.exists(sf):
        n = os.path.basename(sf)
        return (n[:28] + '…') if len(n) > 31 else n
    return 'nessuno'


def _banco_nome():
    p = _cfg_get('exp_banco_path', '')
    if p and os.path.exists(p):
        n = os.path.basename(p)
        return (n[:24] + '…') if len(n) > 27 else n
    return 'banco incluso'


def _sorgente_attuale():
    # 1) un expander FISICO collegato ha SEMPRE la precedenza (default su di lui)
    try:
        from moduli import expander_midi as _ex
        for p in _ex.list_ports():
            if p.get('tipo') == 'expander' and p.get('punteggio', 0) > 0:
                return 'fisico'
    except Exception:
        pass
    # 2) altrimenti il default e' l'Expander Software (socket assente = '1')
    if str(_cfg_get('expander_socket', '1')) == '1':
        return 'software'
    # 3) SF2 solo se scelto esplicitamente (socket=0 + mode=off)
    if str(_cfg_get('expander_mode', 'auto')).lower() == 'off':
        return 'sf2'
    return 'fisico'


def apply():
    import sys
    eg = sys.modules.get('moduli.expander_gui')
    if eg is None:
        try:
            import moduli.expander_gui as eg  # noqa
        except Exception:
            print('[SORG106] expander_gui non presente (ok)')
            return False
    F = getattr(eg, 'FinestraExpander', None)
    if F is None or getattr(F, '_sorgente_106', False):
        return True

    import tkinter as tk
    from tkinter import ttk, filedialog
    ex = eg.ex
    S = eg.S
    Ff = eg.F
    BG = eg.BG
    BG_BOX = eg.BG_BOX
    VERDE = eg.VERDE
    GRIGIO = eg.GRIGIO

    def _porte_hw():
        # SOLO expander hardware VERO: il synth software di Windows (GS Wavetable),
        # le porte virtuali e i mixer NON sono expander e non vanno elencati qui.
        return [p for p in ex.list_ports()
                if p.get('tipo') == 'expander' and p.get('punteggio', 0) > 0]

    def _costruisci(self):
        try:
            self.win.resizable(True, True)
        except Exception:
            pass

        tk.Label(self.win, text="🎛 EXPANDER MIDI", bg=BG, fg=VERDE,
                 font=Ff('Arial', 12, 'bold')).pack(pady=(S(8), S(2)))

        box = tk.Frame(self.win, bg=BG_BOX)
        box.pack(fill='x', padx=S(12), pady=S(2))
        self.lbl_stato = tk.Label(box, text="", bg=BG_BOX, fg='white',
                                  font=Ff('Arial', 9, 'bold'), justify='left', anchor='w')
        self.lbl_stato.pack(fill='x', padx=S(8), pady=S(5))

        self.var_sorgente = tk.StringVar(value=_sorgente_attuale())

        cornice = tk.LabelFrame(self.win, text=" Suona con ", bg=BG, fg=VERDE,
                                font=Ff('Arial', 9, 'bold'), bd=1)
        cornice.pack(fill='x', padx=S(12), pady=S(3))

        riga_sf = tk.Frame(cornice, bg=BG)
        riga_sf.pack(fill='x', padx=S(6), pady=S(1))
        tk.Radiobutton(riga_sf, text="SoundFont (SF2)", value='sf2',
                       variable=self.var_sorgente, command=self._scegli_sorgente,
                       bg=BG, fg='white', selectcolor='#333333', activebackground=BG,
                       activeforeground=VERDE, font=Ff('Arial', 9), anchor='w').pack(side='left')
        self.lbl_sf = tk.Label(riga_sf, text=_sf2_nome(), bg=BG, fg='white',
                               font=Ff('Arial', 8))
        self.lbl_sf.pack(side='left', padx=S(4))
        tk.Button(riga_sf, text="📂 Scegli…", command=self._scegli_sf2,
                  bg='#28a745', fg='white', font=Ff('Arial', 8, 'bold'), relief='flat',
                  bd=0, cursor='hand2', padx=S(6), pady=S(1)).pack(side='right')

        self.rb_fisico = tk.Radiobutton(cornice, text="Expander fisico (USB/MIDI)", value='fisico',
                       variable=self.var_sorgente, command=self._scegli_sorgente,
                       bg=BG, fg='white', selectcolor='#333333', activebackground=BG,
                       activeforeground=VERDE, font=Ff('Arial', 9), anchor='w')
        self.rb_fisico.pack(fill='x', padx=S(6))
        riga = tk.Frame(cornice, bg=BG)
        riga.pack(fill='x', padx=S(22), pady=S(1))
        tk.Label(riga, text="Porta:", bg=BG, fg='white', font=Ff('Arial', 9)).pack(side='left')
        self.combo = ttk.Combobox(riga, textvariable=self.var_porta, state='readonly',
                                  width=30, font=Ff('Arial', 9))
        self.combo.pack(side='left', padx=S(4))
        self.combo.bind('<<ComboboxSelected>>', lambda ev: self._scegli_sorgente())

        riga_sw = tk.Frame(cornice, bg=BG)
        riga_sw.pack(fill='x', padx=S(6), pady=S(1))
        tk.Radiobutton(riga_sw, text="Expander Software", value='software',
                       variable=self.var_sorgente, command=self._scegli_sorgente,
                       bg=BG, fg='white', selectcolor='#333333', activebackground=BG,
                       activeforeground=VERDE, font=Ff('Arial', 9), anchor='w').pack(side='left')
        self.lbl_banco = tk.Label(riga_sw, text=_banco_nome(), bg=BG, fg='white', font=Ff('Arial', 8))
        self.lbl_banco.pack(side='left', padx=S(4))
        tk.Button(riga_sw, text="📂 Banco…", command=self._scegli_banco,
                  bg='#6f42c1', fg='white', font=Ff('Arial', 8, 'bold'), relief='flat',
                  bd=0, cursor='hand2', padx=S(6), pady=S(1)).pack(side='right')

        reg = tk.LabelFrame(self.win, text=" Regolazioni Expander Software ", bg=BG,
                            fg=VERDE, font=Ff('Arial', 9, 'bold'), bd=1)
        reg.pack(fill='x', padx=S(12), pady=S(3))
        self.var_vol = tk.IntVar(value=_int(_cfg_get('exp_sw_vol', '100'), 100))
        self.var_bri = tk.IntVar(value=_int(_cfg_get('exp_sw_bright', '50'), 50))
        self.var_rev = tk.IntVar(value=_int(_cfg_get('exp_sw_reverb', '20'), 20))

        def _slider(testo, var):
            r = tk.Frame(reg, bg=BG)
            r.pack(fill='x', padx=S(8), pady=0)
            tk.Label(r, text=testo, bg=BG, fg='white', font=Ff('Arial', 9),
                     width=11, anchor='w').pack(side='left')
            tk.Scale(r, from_=0, to=100, orient='horizontal', variable=var,
                     command=self._dsp, bg=BG, fg='white', troughcolor='#333333',
                     highlightthickness=0, sliderrelief='flat', length=S(170),
                     font=Ff('Arial', 8)).pack(side='left', fill='x', expand=True)

        _slider("Volume", self.var_vol)
        _slider("Brillantezza", self.var_bri)
        _slider("Riverbero", self.var_rev)

        # ----- PULSANTI (impacchettati per ULTIMI ma ancorati IN BASSO, così non
        #       finiscono mai fuori se la finestra si accorcia) -----
        pulsanti = tk.Frame(self.win, bg=BG)
        pulsanti.pack(side='bottom', fill='x', padx=S(12), pady=S(8))
        tk.Button(pulsanti, text="💾 OK / Applica", command=self._salva, bg='#28a745', fg='white',
                  font=Ff('Arial', 10, 'bold'), relief='flat', bd=0, cursor='hand2',
                  padx=S(14), pady=S(5)).pack(side='left')
        tk.Button(pulsanti, text="Chiudi", command=self.win.destroy, bg='#6c757d', fg='white',
                  font=Ff('Arial', 9, 'bold'), relief='flat', bd=0, cursor='hand2',
                  padx=S(10), pady=S(5)).pack(side='right')
        tk.Button(pulsanti, text="🔄 Rileva", command=self._rileva, bg='#444444', fg='white',
                  font=Ff('Arial', 9, 'bold'), relief='flat', bd=0, cursor='hand2',
                  padx=S(8), pady=S(5)).pack(side='right', padx=S(6))
        tk.Button(pulsanti, text="🔊 Prova", command=self._prova, bg='#0d6efd', fg='white',
                  font=Ff('Arial', 9, 'bold'), relief='flat', bd=0, cursor='hand2',
                  padx=S(8), pady=S(5)).pack(side='right')

        self._scegli_sorgente(_solo_ui=True)

        def _centra106():
            try:
                self.win.update_idletasks()
                w = self.win.winfo_width(); h = self.win.winfo_height()
                sw = self.win.winfo_screenwidth(); sh = self.win.winfo_screenheight()
                # se troppo alta per lo schermo, la limito così i pulsanti entrano
                if h > sh - S(60):
                    h = sh - S(60)
                    self.win.geometry("%dx%d" % (w, h))
                x = max(0, (sw - w) // 2)
                y = max(S(10), (sh - h) // 2 - S(20))
                self.win.geometry("+%d+%d" % (x, y))
            except Exception:
                pass
        try:
            self.win.after(40, _centra106)
        except Exception:
            pass

    def _aggiorna_stato(self):
        # combo porte: SOLO hardware vero
        self.porte = _porte_hw()
        etich = ["[%s] %s" % (p['id'], p['nome']) for p in self.porte]
        try:
            self.combo['values'] = etich
        except Exception:
            pass
        s = self.var_sorgente.get() if hasattr(self, 'var_sorgente') else _sorgente_attuale()
        try:
            self.combo.config(state='readonly' if s == 'fisico' else 'disabled')
        except Exception:
            pass
        # sulla voce "Expander fisico" mostro il MODELLO riconosciuto, se collegato
        try:
            if self.porte:
                self.rb_fisico.config(text="Expander fisico: %s" % self.porte[0]['nome'])
            else:
                self.rb_fisico.config(text="Expander fisico (nessuno collegato)")
        except Exception:
            pass
        if not self.var_porta.get() and etich:
            self.var_porta.set(etich[0])
        if s == 'software':
            testo = "● Expander Software in uso\n   Suoni interni tipo expander."
            col = VERDE
        elif s == 'sf2':
            testo = "● SoundFont: %s" % _sf2_nome()
            col = VERDE
        else:
            if self.porte:
                testo = "● Expander fisico: %s" % self.porte[0]['nome']
                col = VERDE
            else:
                testo = ("○ Nessun expander fisico collegato\n"
                         "   (il synth di Windows NON è un expander)")
                col = GRIGIO
        try:
            self.lbl_stato.config(text=testo, fg=col)
        except Exception:
            pass

    def _dsp(self, *a):
        v = int(self.var_vol.get()); br = int(self.var_bri.get()); rv = int(self.var_rev.get())
        ex._set_cfg('exp_sw_vol', str(v))
        ex._set_cfg('exp_sw_bright', str(br))
        ex._set_cfg('exp_sw_reverb', str(rv))
        fn = getattr(ex, '_exp_soft_dsp', None)
        if fn:
            try:
                fn(v, br, rv)
            except Exception as e:
                print('[SORG106] dsp:', e)

    def _scegli_sf2(self):
        try:
            from moduli.database import Database
            cur = Database.get_config('soundfont_path', '')
            fp = filedialog.askopenfilename(
                title="Seleziona SoundFont (.sf2)",
                filetypes=[("SoundFont", "*.sf2 *.sf3"), ("Tutti i file", "*.*")],
                initialdir=os.path.dirname(cur) if cur else "")
            if fp:
                Database.set_config('soundfont_path', fp)
                self.lbl_sf.config(text=_sf2_nome())
                self.var_sorgente.set('sf2')
                self._scegli_sorgente()
        except Exception as e:
            print('[SORG106] scegli sf2:', e)

    def _scegli_banco(self):
        # sceglie il BANCO dell'Expander Software (sf2/sf3), lo salva in config e
        # passa a "Expander Software": il motore file-based lo carica al volo.
        try:
            from moduli.database import Database
            cur = Database.get_config('exp_banco_path', '')
            fp = filedialog.askopenfilename(
                title="Banco Expander (.sf2 / .sf3)",
                filetypes=[("SoundFont", "*.sf2 *.sf3"), ("Tutti i file", "*.*")],
                initialdir=os.path.dirname(cur) if cur else "")
            if fp:
                Database.set_config('exp_banco_path', fp)
                self.lbl_banco.config(text=_banco_nome())
                self.var_sorgente.set('software')
                self._scegli_sorgente()
        except Exception as e:
            print('[SORG106] scegli banco:', e)

    def _scegli_sorgente(self, _solo_ui=False):
        s = self.var_sorgente.get()
        try:
            self.combo.config(state='readonly' if s == 'fisico' else 'disabled')
        except Exception:
            pass
        if _solo_ui:
            return
        try:
            if s == 'sf2':
                ex._set_cfg('expander_socket', '0')
                ex.set_mode('off')
                try:
                    from moduli.bass_engine import get_bass_engine
                    be = get_bass_engine()
                    sf = _cfg_get('soundfont_path', '')
                    if getattr(be, 'initialized', False) and sf and os.path.exists(sf):
                        be.synth.sfload(sf)
                except Exception as e:
                    print('[SORG106] sfload:', e)
            elif s == 'fisico':
                ex._set_cfg('expander_socket', '0')
                p = self._porta_selezionata()
                if p:
                    ex._set_cfg(ex.CFG_PORT, p['nome'])
                    ex.set_mode('on')
                else:
                    ex.set_mode('auto')
            else:
                # ⛔ Software: mode='auto', NON 'off'. Con 'off' get_expander_player()
                #    esce subito (return None) e resta l'SF2. socket=1 + auto = software
                #    (il GS Wavetable resta escluso perche' ha punteggio 0).
                ex._set_cfg('expander_socket', '1')
                ex.set_mode('auto')
            self.var_modo.set(ex.get_mode())
            ex.reset_player()
            self._commuta_a_caldo()
            # costruisco SUBITO il player della sorgente scelta, cosi' la scelta
            # vale ORA (is_active vero) e la scritta nel mixer cambia all'istante,
            # anche senza una base in riproduzione.
            try:
                ex.get_expander_player()
            except Exception:
                pass
            self._aggiorna_stato()
        except Exception as e:
            print('[SORG106] applica sorgente:', e)

    F._costruisci = _costruisci
    F._aggiorna_stato = _aggiorna_stato
    F._dsp = _dsp
    F._scegli_sf2 = _scegli_sf2
    F._scegli_banco = _scegli_banco
    F._scegli_sorgente = _scegli_sorgente
    F._sorgente_106 = True

    # DEFAULT = Expander Software (se c'e' un fisico, la precedenza e' sua, in
    # automatico via detect). Solo se l'utente sceglie SF2 resta socket=0/mode=off.
    try:
        soc = _cfg_get('expander_socket', '')
        if soc in ('', None):
            ex._set_cfg('expander_socket', '1')
            ex._set_cfg('expander_mode', 'auto')
            print('[SORG106] default impostato: Expander Software (fisico se presente)')
        elif str(soc) == '1' and str(_cfg_get('expander_mode', 'auto')).lower() == 'off':
            # software richiesto ma mode=off lo disattivava: lo rimetto ad auto
            ex._set_cfg('expander_mode', 'auto')
            print('[SORG106] corretto expander_mode off->auto')
    except Exception as e:
        print('[SORG106] default/autocorrezione:', e)

    # tolgo il bottone "CARICA SF2" dal mixer (ora si sceglie da qui)
    try:
        import moduli.mixer as mx
        P = getattr(mx, 'MIDIMixerPanel', None)
        if P is not None and hasattr(P, '_update_soundfont_display') and not getattr(P, '_nosf2_106', False):
            _osf = P._update_soundfont_display

            def _usd(self, *a, **k):
                r = _osf(self, *a, **k)
                try:
                    lbl = getattr(self, 'sf_label', None)
                    if lbl is not None and not getattr(self, '_sf2_tolto_106', False):
                        for w in lbl.master.winfo_children():
                            try:
                                if isinstance(w, tk.Button) and 'SF2' in (w.cget('text') or '').upper():
                                    w.pack_forget()
                            except Exception:
                                pass
                        self._sf2_tolto_106 = True
                except Exception:
                    pass
                return r

            P._update_soundfont_display = _usd
            P._nosf2_106 = True
    except Exception as e:
        print('[SORG106] tolgo CARICA SF2:', e)

    print('[SORG106] finestra unica compatta + regolazioni + pulsanti in basso')
    return True


def revert():
    pass


try:
    apply()
except Exception as _e:
    print('patch 106: %s' % _e)
