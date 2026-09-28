def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_148', '1')) == '0'
    except Exception:
        return False


def _hook_mixer():
    import moduli.mixer as MX
    P = getattr(MX, 'MIDIMixerPanel', None) or getattr(MX, 'MidiMixerPanel', None)
    if P is None:
        return None, None
    if not getattr(P, '_refresh148', False):
        def refresh_soundfont(self):
            try:
                self._update_soundfont_display()
            except Exception:
                pass
            try:
                import os
                mf = getattr(self, 'current_midi_file', None)
                if mf and os.path.exists(mf):
                    self.load_midi_file(mf, melody_muted=False)
            except Exception as e:
                print('[REFRESH148] ripopolo nomi fallito:', e)
        P.refresh_soundfont = refresh_soundfont

        _oi = P.__init__
        def __init__(self, *a, **k):
            _oi(self, *a, **k)
            try:
                MX._last_mixer = self
            except Exception:
                pass
        P.__init__ = __init__
        P._refresh148 = True
    return MX, P


def apply():
    if _spenta():
        return False
    try:
        MX, P = _hook_mixer()
    except Exception as e:
        print('[REFRESH148] mixer non presente:', e); return False
    if P is None:
        print('[REFRESH148] classe mixer non trovata'); return False

    # aggancio il pulsante Applica dell'expander (_applica_ora)
    try:
        import moduli.expander_gui as EG
        for _n in dir(EG):
            cls = getattr(EG, _n)
            if isinstance(cls, type) and hasattr(cls, '_applica_ora') and not getattr(cls, '_refresh148', False):
                _oa = cls._applica_ora
                def _aa(self, _oa=_oa, _MX=MX):
                    r = _oa(self)
                    try:
                        m = getattr(_MX, '_last_mixer', None)
                        if m is not None:
                            m.refresh_soundfont()
                    except Exception as e:
                        print('[REFRESH148] refresh su Applica fallito:', e)
                    return r
                cls._applica_ora = _aa
                cls._refresh148 = True
                print('[REFRESH148] agganciato Applica ->', _n)
    except Exception as e:
        print('[REFRESH148] hook expander_gui fallito:', e)

    # anche alla chiusura della finestra expander (fallback)
    _oe = getattr(P, '_apri_expander', None)
    if callable(_oe) and not getattr(P, '_refresh148b', False):
        def _apri(self, _oe=_oe):
            r = _oe(self)
            try:
                self.refresh_soundfont()
            except Exception:
                pass
            return r
        P._apri_expander = _apri
        P._refresh148b = True

    print('[REFRESH148] refresh mixer su Applica attivo')
    return True


def revert():
    pass


try:
    apply()
except Exception as _e:
    print('patch 148: %s' % _e)
