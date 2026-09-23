# 098 - Expander: la scelta expander/SoundFont si applica SUBITO, anche a brano in corso
def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_098', '1')) == '0'
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
            print('patch 098: expander_gui non presente (ok)')
            return False
    mx = sys.modules.get('moduli.mixer')
    if mx is None:
        try:
            import moduli.mixer as mx  # noqa
        except Exception:
            mx = None
    F = getattr(eg, 'FinestraExpander', None)
    if F is None:
        print('patch 098: FinestraExpander non trovata (ok)')
        return False
    if getattr(F, '_switch_098', False):
        return True

    ex = eg.ex  # modulo expander_midi

    def _commuta_a_caldo(self):
        import sys as _sys
        sysobj = getattr(self, 'system', None)
        root = None
        if sysobj is None:
            main = _sys.modules.get('__main__')
            sysobj = getattr(main, '_app_system', None)
            root = getattr(main, '_app_root', None)
        try:
            if not (sysobj and getattr(sysobj, 'is_midi', False) and getattr(sysobj, 'is_playing', False)):
                return
            cf = getattr(sysobj, 'current_file', None)
            if not cf:
                return

            def _hot():
                try:
                    ton = getattr(sysobj, 'current_pitch', 0) or 0
                    try:
                        pos = int(sysobj.get_current_position_ms() or 0)
                    except Exception:
                        pos = 0
                    sysobj.stop()
                    try:
                        ok = sysobj.load_file(cf, ton)
                    except TypeError:
                        ok = sysobj.load_file(cf)
                    if ok:
                        sysobj.play()
                        if pos > 500:
                            sysobj.seek_to(pos)
                    print('[EXP] brano commutato a caldo (immediato)')
                except Exception as e:
                    print('[EXP] commuta a caldo:', e)
            if root is not None:
                root.after(0, _hot)
            else:
                _hot()
        except Exception as e:
            print('[EXP] commutazione a caldo fallita:', e)

    # __init__: accetta system e segna quando la finestra e' pronta
    _orig_init = F.__init__

    def __init__(self, parent=None, system=None):
        self.system = system
        self._pronto098 = False
        _orig_init(self, parent)
        self._pronto098 = True

    # _aggiorna_stato: i radio esistenti lo chiamano gia'. Dopo l'aggiornamento
    # dello stato, se la finestra e' pronta (clic dell'utente, non apertura),
    # salva la scelta e commuta a caldo.
    _orig_agg = F._aggiorna_stato

    def _aggiorna_stato(self):
        _orig_agg(self)
        if not getattr(self, '_pronto098', False):
            return
        try:
            ex.set_mode(self.var_modo.get())
            porta = self._porta_selezionata()
            ex._set_cfg(ex.CFG_PORT, porta['nome'] if porta else '')
            ex._set_cfg(ex.CFG_SYSEX, '1' if self.var_sysex.get() else '0')
        except Exception as e:
            print('[EXP] cfg expander:', e)
        try:
            ex.reset_player()
        except Exception:
            pass
        self._commuta_a_caldo()

    F._commuta_a_caldo = _commuta_a_caldo
    F.__init__ = __init__
    F._aggiorna_stato = _aggiorna_stato
    F._switch_098 = True

    # apri_finestra_expander: accetta e inoltra il system
    def apri_finestra_expander(parent=None, system=None):
        try:
            return F(parent, system=system)
        except Exception as e:
            print('patch 098: apertura finestra expander:', e)
            return None
    eg.apri_finestra_expander = apri_finestra_expander

    # mixer: passa il system alla finestra
    if mx is not None:
        P = getattr(mx, 'MIDIMixerPanel', None)
        if P is not None and not getattr(P, '_apri_exp_098', False):
            def _apri_expander(self):
                try:
                    eg.apri_finestra_expander(self.mixer_frame, system=getattr(self, 'system', None))
                    self._update_soundfont_display()
                except Exception as e:
                    try:
                        from tkinter import messagebox
                        from moduli.i18n import _
                        messagebox.showerror(_("Expander MIDI"), str(e), parent=self.mixer_frame)
                    except Exception:
                        pass
            P._apri_expander_orig_098 = P._apri_expander
            P._apri_expander = _apri_expander
            P._apri_exp_098 = True

    print('[EXP] patch 098: scelta expander/SoundFont applicata SUBITO (commutazione a caldo)')
    return True


def revert():
    try:
        import sys
        eg = sys.modules.get('moduli.expander_gui')
        F = getattr(eg, 'FinestraExpander', None) if eg else None
        if F is not None and getattr(F, '_switch_098', False):
            del F._switch_098
        mx = sys.modules.get('moduli.mixer')
        P = getattr(mx, 'MIDIMixerPanel', None) if mx else None
        if P is not None and getattr(P, '_apri_exp_098', False):
            if hasattr(P, '_apri_expander_orig_098'):
                P._apri_expander = P._apri_expander_orig_098
            del P._apri_exp_098
    except Exception:
        pass


try:
    apply()
except Exception as _e:
    print('patch 098: %s' % _e)
