def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_116', '1')) == '0'
    except Exception:
        return False


def apply():
    if _spenta():
        return False
    import sys
    eg = sys.modules.get('moduli.expander_gui')
    if eg is None:
        try:
            import moduli.expander_gui as eg  # noqa
        except Exception:
            print('[SORG116] expander_gui non presente (ok)')
            return False
    F = getattr(eg, 'FinestraExpander', None)
    if F is None or getattr(F, '_ok_chiude_116', False):
        return True
    if not hasattr(F, '_costruisci') or not hasattr(F, '_scegli_sorgente'):
        # la finestra unica (106) non c'e': niente da riadattare
        return True

    _orig_costr = F._costruisci

    def _solo_scritta(self):
        # cambio radio o porta: NON applica niente, aggiorna SOLO la scritta, subito
        try:
            self.combo.config(state='readonly' if self.var_sorgente.get() == 'fisico' else 'disabled')
        except Exception:
            pass
        try:
            self._aggiorna_stato()      # usa var_sorgente: mostra la scelta corrente
        except Exception as e:
            print('[SORG116] scritta:', e)

    def _aggiorna_mixer(self):
        # rinfresca SUBITO la scritta sorgente nella finestra del Mixer
        try:
            import moduli.mixer as _mx
            inst = _mx.MIDIMixerPanel.get_instance()
            if inst is not None and hasattr(inst, '_update_soundfont_display'):
                inst._update_soundfont_display()
        except Exception as e:
            print('[SORG116] refresh mixer:', e)

    def _ok_chiude(self):
        # Applica DAVVERO la sorgente scelta (socket/mode + commuta a caldo), poi chiude
        try:
            self._scegli_sorgente()
        except Exception as e:
            print('[SORG116] applica:', e)
        self._aggiorna_mixer()
        try:
            self.win.destroy()
        except Exception:
            pass

    def _tutti(w, out):
        for c in w.winfo_children():
            out.append(c)
            _tutti(c, out)

    def _costruisci116(self):
        _orig_costr(self)               # 106 costruisce tutto (non applica in costruzione)
        try:
            widgets = []
            _tutti(self.win, widgets)
            for w in widgets:
                try:
                    cls = w.winfo_class()
                except Exception:
                    continue
                if cls == 'Radiobutton':
                    try:
                        w.config(command=lambda s=self: s._solo_scritta())
                    except Exception:
                        pass
                elif cls == 'Button':
                    try:
                        t = (w.cget('text') or '').lower()
                    except Exception:
                        t = ''
                    if 'chiudi' in t:
                        try:
                            w.pack_forget()          # via il bottone Chiudi
                        except Exception:
                            pass
                    elif 'applica' in t or ' ok' in (' ' + t):
                        try:
                            w.config(text='✅ Applica',
                                     command=lambda s=self: s._ok_chiude())
                        except Exception:
                            pass
            # cambio porta nella combo = solo scritta (applica su OK)
            try:
                self.combo.bind('<<ComboboxSelected>>', lambda ev, s=self: s._solo_scritta())
            except Exception:
                pass
        except Exception as e:
            print('[SORG116] post-costruzione:', e)

    F._solo_scritta = _solo_scritta
    F._aggiorna_mixer = _aggiorna_mixer
    F._ok_chiude = _ok_chiude
    F._costruisci = _costruisci116
    F._ok_chiude_116 = True
    print('[SORG116] cambio = solo scritta; Applica/OK applica e chiude; niente Chiudi')
    return True


def revert():
    pass


try:
    apply()
except Exception as _e:
    print('patch 116: %s' % _e)
