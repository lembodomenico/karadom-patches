def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_129', '1')) == '0'
    except Exception:
        return False


def _get(k, d=''):
    try:
        from moduli.database import Database
        v = Database.get_config(k, d)
        return v if v not in (None, '') else d
    except Exception:
        return d


def _set(k, v):
    try:
        from moduli.database import Database
        Database.set_config(k, str(v))
    except Exception:
        pass


def apply():
    if _spenta():
        return False
    import moduli.expander_midi as ex

    # 1) get_expander_player: se l'utente ha scelto ESPLICITAMENTE una sorgente,
    #    quella VINCE e resta (anche se c'e' l'HW). Senza scelta esplicita ->
    #    comportamento di prima (precedenza HW / default).
    if not getattr(ex, '_scelta129', False):
        _ogp = ex.get_expander_player

        def _get_player(*a, **k):
            scelta = str(_get('sorgente_scelta', '')).lower()
            if scelta == 'sf2':
                # SF2 esplicito: niente expander, nemmeno se il fisico c'e'
                try:
                    if hasattr(ex, 'reset_player') and not (getattr(ex, 'is_active', None) and ex.is_active()):
                        pass
                except Exception:
                    pass
                return None
            if scelta == 'fisico':
                # solo HW: se non c'e', niente ripiego sul software
                try:
                    porta = ex.detect_expander()
                    if not porta or porta.get('id', -1) == -1 \
                            or 'software' in (porta.get('nome', '') or '').lower():
                        return None
                except Exception:
                    return None
                ex._set_cfg('expander_socket', '0'); ex.set_mode('on')
                return _ogp(*a, **k)
            if scelta == 'software':
                # forza software: socket=1, mode auto (l'HW NON deve rubargli il posto)
                ex._set_cfg('expander_socket', '1'); ex.set_mode('auto')
                return _ogp(*a, **k)
            # nessuna scelta esplicita -> come prima (109: HW precedenza, ecc.)
            return _ogp(*a, **k)

        ex._get_player_pre129 = _ogp
        ex.get_expander_player = _get_player
        ex._scelta129 = True

    # 2) finestra Expander: quando l'utente applica una sorgente, SALVO la scelta;
    #    all'apertura la finestra mostra la scelta salvata.
    try:
        import moduli.expander_gui as eg
        F = getattr(eg, 'FinestraExpander', None)
        if F and hasattr(F, '_scegli_sorgente') and not getattr(F, '_scelta129', False):
            _osc = F._scegli_sorgente

            def _scegli(self, _solo_ui=False):
                r = _osc(self, _solo_ui=_solo_ui)
                if not _solo_ui:
                    try:
                        _set('sorgente_scelta', self.var_sorgente.get())
                        print('[SCELTA129] sorgente salvata:', self.var_sorgente.get())
                    except Exception as e:
                        print('[SCELTA129] save:', e)
                return r

            F._scegli_sorgente = _scegli

            # all'apertura: rifletti la scelta salvata nel radio
            if hasattr(F, '_costruisci'):
                _oc = F._costruisci

                def _costr(self):
                    _oc(self)
                    try:
                        sc = str(_get('sorgente_scelta', '')).lower()
                        if sc in ('sf2', 'fisico', 'software') and hasattr(self, 'var_sorgente'):
                            self.var_sorgente.set(sc)
                            if hasattr(self, '_aggiorna_stato'):
                                self._aggiorna_stato()
                    except Exception as e:
                        print('[SCELTA129] init:', e)
                F._costruisci = _costr

            F._scelta129 = True
    except Exception as e:
        print('[SCELTA129] gui:', e)

    print('[SCELTA129] la scelta SF2/Expander fatta dall\'utente resta memorizzata e vince')
    return True


def revert():
    pass


try:
    apply()
except Exception as _e:
    print('patch 129: %s' % _e)
