def apply():
    import sys
    mx = sys.modules.get('moduli.mixer')
    if mx is None:
        try:
            import moduli.mixer as mx  # noqa
        except Exception:
            print('[SRC107] mixer non presente (ok)')
            return False
    P = getattr(mx, 'MIDIMixerPanel', None)
    if P is None or getattr(P, '_lblrefresh_107', False):
        return True
    if not hasattr(P, '_poll_activity') or not hasattr(P, '_update_soundfont_display'):
        return True

    _orig = P._poll_activity

    def _poll(self, *a, **k):
        # aggiorna la SCRITTA del SoundFont/Expander quando la sorgente attiva
        # cambia (es. l'expander software si accende a base gia' partita).
        try:
            from moduli.expander_midi import get_active_player
            ap = get_active_player()
            sig = (getattr(ap, 'nome_porta', None) or 'exp') if ap else '__sf__'
            if sig != getattr(self, '_last_src_sig_107', None):
                self._last_src_sig_107 = sig
                try:
                    self._update_soundfont_display()
                except Exception:
                    pass
        except Exception:
            pass
        return _orig(self, *a, **k)

    P._poll_activity = _poll
    P._lblrefresh_107 = True
    print('[SRC107] la scritta sorgente nel mixer si aggiorna quando cambia')
    return True


def revert():
    try:
        import sys
        mx = sys.modules.get('moduli.mixer')
        P = getattr(mx, 'MIDIMixerPanel', None) if mx else None
        if P is not None and getattr(P, '_lblrefresh_107', False):
            del P._lblrefresh_107
    except Exception:
        pass


try:
    apply()
except Exception as _e:
    print('patch 107: %s' % _e)
