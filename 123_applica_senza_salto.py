import os


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_123', '1')) == '0'
    except Exception:
        return False


def _cfg(k, d=''):
    try:
        from moduli.database import Database
        v = Database.get_config(k, d)
        return v if v not in (None, '') else d
    except Exception:
        return d


def _nc(p):
    try:
        return os.path.normcase(os.path.abspath(str(p or '')))
    except Exception:
        return str(p or '')


def apply():
    if _spenta():
        return False
    import sys
    eg = sys.modules.get('moduli.expander_gui')
    if eg is None:
        try:
            import moduli.expander_gui as eg  # noqa
        except Exception:
            print('[NOSALTO123] expander_gui non presente (ok)')
            return False
    F = getattr(eg, 'FinestraExpander', None)
    if F is None or getattr(F, '_no_salto_123', False):
        return True
    _orig = getattr(F, '_scegli_sorgente', None)
    if _orig is None:
        # finestra unica (106) non presente: niente da fare
        return True

    import moduli.expander_midi as ex

    def _sig_scelta(self):
        # firma di cosa VUOLE l'utente adesso (radio + porta/banco/sf2)
        s = self.var_sorgente.get()
        if s == 'sf2':
            return ('sf2', _nc(_cfg('soundfont_path', '')))
        if s == 'fisico':
            p = self._porta_selezionata()
            return ('fisico', str((p or {}).get('nome', '')).strip().lower())
        return ('software', _nc(_cfg('exp_banco_path', '')))

    def _sig_attuale(self):
        # firma del motore che sta suonando ORA (da config)
        socket = str(_cfg('expander_socket', '0'))
        try:
            mode = str(ex.get_mode())
        except Exception:
            mode = str(_cfg('expander_mode', 'auto'))
        if socket == '1':
            return ('software', _nc(_cfg('exp_banco_path', '')))
        if mode == 'on':
            return ('fisico', str(_cfg(getattr(ex, 'CFG_PORT', 'expander_port'), '')).strip().lower())
        return ('sf2', _nc(_cfg('soundfont_path', '')))

    def _scegli_sorgente_123(self, _solo_ui=False):
        if _solo_ui:
            return _orig(self, _solo_ui=True)
        try:
            cambia = _sig_scelta(self) != _sig_attuale(self)
        except Exception:
            cambia = True   # nel dubbio, comportamento vecchio
        if cambia:
            # il motore/banco/porta cambia davvero: ricarica a caldo (necessaria)
            return _orig(self)
        # ---- STESSO motore: solo correzioni (Bassi/Brillantezza/Vol/Riverbero) ----
        # niente stop+reload+seek -> niente salto nel brano. Persisto la config e
        # riapplico gli FX sullo stream VIVO.
        try:
            s = self.var_sorgente.get()
            if s == 'sf2':
                ex._set_cfg('expander_socket', '0'); ex.set_mode('off')
            elif s == 'fisico':
                ex._set_cfg('expander_socket', '0')
                p = self._porta_selezionata()
                if p:
                    ex._set_cfg(getattr(ex, 'CFG_PORT', 'expander_port'), p['nome'])
                    ex.set_mode('on')
                else:
                    ex.set_mode('auto')
            else:
                ex._set_cfg('expander_socket', '1'); ex.set_mode('auto')
            try:
                self.var_modo.set(ex.get_mode())
            except Exception:
                pass
        except Exception as e:
            print('[NOSALTO123] persist:', e)
        # riapplico le correzioni sullo stream in corso (nessuna ricarica)
        try:
            self._dsp()
        except Exception as e:
            print('[NOSALTO123] dsp:', e)
        try:
            self._aggiorna_stato()
        except Exception:
            pass
        print('[NOSALTO123] Applica: stesso motore -> solo correzioni, niente reload (no salto)')

    F._scegli_sorgente = _scegli_sorgente_123
    F._no_salto_123 = True
    print('[NOSALTO123] Applica senza salto: reload solo se cambia sorgente/porta/banco')
    return True


def revert():
    pass


try:
    apply()
except Exception as _e:
    print('patch 123: %s' % _e)
