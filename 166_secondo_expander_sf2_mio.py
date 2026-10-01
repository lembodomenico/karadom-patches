import os


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_166', '1')) == '0'
    except Exception:
        return False


def _cfg(k, d=''):
    try:
        from moduli.database import Database
        v = Database.get_config(k, d)
        return v if v not in (None, '') else d
    except Exception:
        return d


def _set(k, v):
    try:
        from moduli.database import Database
        Database.set_config(k, v)
    except Exception:
        pass


def _nome(p):
    if p and os.path.isfile(p):
        n = os.path.basename(p)
        return (n[:24] + '…') if len(n) > 27 else n
    return 'nessuno'


def apply():
    if _spenta():
        return False
    import sys
    eg = sys.modules.get('moduli.expander_gui')
    if eg is None:
        try:
            import moduli.expander_gui as eg  # noqa
        except Exception:
            return False
    F = getattr(eg, 'FinestraExpander', None)
    if F is None or not hasattr(F, '_costruisci') or not hasattr(F, '_scegli_sorgente'):
        return False

    # banco PREDEFINITO (quello che usano tutti): fotografato una volta.
    if not _cfg('exp_banco_default', ''):
        cur = _cfg('exp_banco_path', '')
        if cur:
            _set('exp_banco_default', cur)
    # banco MIO: default su kdl4.sf2 se c'e', cosi' funziona subito senza dialog.
    if not _cfg('exp_banco_mio', ''):
        for _cand in (r'D:\Claude\SoundFont\kdl4.sf2', r'D:\Claude\SoundFont\kdl4_full.sf2'):
            if os.path.isfile(_cand):
                _set('exp_banco_mio', _cand)
                break

    # ---- etichetta del MIXER: mostra il nome del MIO sf2 quando lo slot e' 'mio' ----
    try:
        import moduli.mixer as MX
        P = getattr(MX, 'MIDIMixerPanel', None)
        if P is not None and not getattr(P, '_slot_mio_lbl', False):
            _ousd = P._update_soundfont_display

            def _usd(self):
                try:
                    # STESSO metodo con cui "Expander Software" funziona (patch 109):
                    # si basa su _exp_soft_active del bass engine, NON su
                    # get_active_player(). Quando il software e' attivo e lo slot e'
                    # 'mio', cambio solo il testo in "SF2 mio".
                    from moduli.bass_engine import get_bass_engine
                    soft = bool(getattr(get_bass_engine(), '_exp_soft_active', False))
                    scelta = str(_cfg('sorgente_scelta', '')).lower()
                    # ⛔ col FISICO non mostrare "SF2 mio" (il flag software puo'
                    # restare True passando software->fisico): la scelta salvata dice
                    # la verita'. Fisico -> lascia l'originale (etichetta del fisico).
                    if soft and scelta != 'fisico' and str(_cfg('exp_slot', 'default')) == 'mio':
                        self.sf_label.config(
                            text="Expander (SF2 mio): %s" % _nome(_cfg('exp_banco_mio', '')),
                            fg='#FFD700')
                        return
                except Exception:
                    pass
                return _ousd(self)
            P._update_soundfont_display = _usd
            P._slot_mio_lbl = True
    except Exception:
        pass

    if getattr(F, '_slot_mio_patch', False):
        return True

    import tkinter as tk
    from tkinter import filedialog, messagebox

    def _trova_cornice(self):
        try:
            stack = list(self.win.winfo_children())
            while stack:
                w = stack.pop()
                try:
                    if isinstance(w, tk.Radiobutton) and str(w.cget('value')) == 'software':
                        return w.master.master  # riga_sw -> cornice
                except Exception:
                    pass
                stack.extend(w.winfo_children())
        except Exception:
            pass
        return None

    def _refresh_mixer():
        try:
            import moduli.mixer as _MX
            _MX.MIDIMixerPanel.get_instance()._update_soundfont_display()
        except Exception:
            pass

    def _scegli_file_mio(self):
        # SOLO dal pulsante (il dialog e' modale: sul click esplicito e' ok).
        try:
            cur = _cfg('exp_banco_mio', '')
            fp = filedialog.askopenfilename(
                title="Scegli il TUO SoundFont per il 2° Expander",
                initialfile=os.path.basename(cur) if cur else '',
                filetypes=[("SoundFont", "*.sf2 *.sf3"), ("Tutti i file", "*.*")])
            if fp:
                _set('exp_banco_mio', fp)
                if hasattr(self, '_lbl_mio'):
                    self._lbl_mio.config(text=_nome(fp))
                self.var_sorgente.set('software_mio')
                self._scegli_sorgente()
        except Exception as e:
            print('[EXP166] scegli mio:', e)

    _orig_scegli = F._scegli_sorgente

    def _scegli_sorgente(self, _solo_ui=False):
        try:
            v = self.var_sorgente.get()
            if v == 'software_mio':
                mio = _cfg('exp_banco_mio', '')
                if not mio or not os.path.isfile(mio):
                    if not _solo_ui:
                        messagebox.showinfo("2° Expander",
                                            "Scegli prima il tuo SF2 col pulsante «🎛 Scegli SF2 mio…».")
                    return
                try:
                    self.combo.config(state='disabled')
                except Exception:
                    pass
                if _solo_ui:
                    return   # init UI: non toccare lo slot salvato
                # applico DIRETTAMENTE il ramo 'software' (senza flippare var: cosi'
                # la scritta resta 'SF2 mio'), ma col banco MIO gia' impostato.
                _set('exp_banco_path', mio)
                _set('exp_slot', 'mio')
                try:
                    import moduli.expander_midi as ex
                    ex._set_cfg('expander_socket', '1')
                    ex.set_mode('auto')
                    try:
                        self.var_modo.set(ex.get_mode())
                    except Exception:
                        pass
                    try:
                        ex.reset_player()
                    except Exception:
                        pass
                    try:
                        self._commuta_a_caldo()
                    except Exception:
                        pass
                    try:
                        ex.get_expander_player()
                    except Exception:
                        pass
                except Exception as e:
                    print('[EXP166] applica mio:', e)
                self._aggiorna_stato()
                _refresh_mixer()
                return
            elif v == 'software' and not _solo_ui:
                _set('exp_banco_path', _cfg('exp_banco_default', ''))
                _set('exp_slot', 'default')
        except Exception as e:
            print('[EXP166] scegli sorgente:', e)
        r = _orig_scegli(self, _solo_ui)
        if not _solo_ui:
            _refresh_mixer()
        return r

    F._scegli_sorgente = _scegli_sorgente

    # scritta di stato corretta per lo slot 'SF2 mio' (l'originale non lo conosce)
    _orig_agg = F._aggiorna_stato

    def _aggiorna_stato(self):
        try:
            if self.var_sorgente.get() == 'software_mio':
                _orig_agg(self)   # housekeeping combo/porte
                try:
                    self.lbl_stato.config(
                        text="● Expander Software — SF2 mio in uso\n   Banco: %s"
                             % _nome(_cfg('exp_banco_mio', '')), fg='#39FF14')
                except Exception:
                    pass
                return
        except Exception:
            pass
        return _orig_agg(self)

    F._aggiorna_stato = _aggiorna_stato

    _orig_costr = F._costruisci

    def _costruisci(self):
        _orig_costr(self)
        try:
            cornice = _trova_cornice(self)
            if cornice is None:
                print('[EXP166] cornice non trovata')
                return
            BG = cornice.cget('bg')
            try:
                from moduli.ui_scale import S, F as Ff
            except Exception:
                def S(x): return x
                def Ff(f, s, *a): return (f, s) + a
            riga = tk.Frame(cornice, bg=BG)
            riga.pack(fill='x', padx=S(6), pady=S(4))
            tk.Radiobutton(riga, text="Expander Software — SF2 mio", value='software_mio',
                           variable=self.var_sorgente, command=self._scegli_sorgente,
                           bg=BG, fg='#FFD700', selectcolor=BG,
                           activebackground=BG, activeforeground='#FFD700',
                           font=Ff('Arial', 10, 'bold')).pack(side='left', padx=(0, S(6)))
            tk.Button(riga, text="🎛 Scegli SF2 mio…",
                      command=lambda s=self: _scegli_file_mio(s),
                      bg='#333333', fg='white', relief='flat',
                      font=Ff('Arial', 9)).pack(side='left')
            self._lbl_mio = tk.Label(riga, text=_nome(_cfg('exp_banco_mio', '')),
                                     bg=BG, fg='white', font=Ff('Arial', 8))
            self._lbl_mio.pack(side='left', padx=S(6))
            if _cfg('exp_slot', 'default') == 'mio' and self.var_sorgente.get() == 'software':
                self.var_sorgente.set('software_mio')
                try:
                    self._aggiorna_stato()   # scritta in alto = 'SF2 mio' gia' all'apertura
                except Exception:
                    pass
            if hasattr(self, '_ricentra116'):
                self.win.after(140, lambda s=self: s._ricentra116())
        except Exception as e:
            print('[EXP166] costruisci:', e)

    F._costruisci = _costruisci
    F._slot_mio_patch = True
    print('[EXP166] 2° expander (SF2 mio) — default %s' % _cfg('exp_banco_mio', 'nessuno'))
    return True


try:
    apply()
except Exception as _e:
    print('patch 166: %s' % _e)
