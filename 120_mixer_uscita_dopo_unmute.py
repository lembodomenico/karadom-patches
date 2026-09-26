def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_120', '1')) == '0'
    except Exception:
        return False


def apply():
    if _spenta():
        return False
    import sys
    mx = sys.modules.get('moduli.mixer')
    if mx is None:
        try:
            import moduli.mixer as mx  # noqa
        except Exception:
            print('[MIX120] mixer non presente (ok)')
            return False
    P = getattr(mx, 'MIDIMixerPanel', None)
    if P is None or getattr(P, '_uscita120b', False):
        return True
    if not hasattr(P, '_toggle_mute'):
        return True

    _orig = getattr(P, '_toggle_mute_orig120', None) or P._toggle_mute

    def _toggle_mute(self, channel):
        ch = self.channels[channel]
        # se sta per diventare MUTO, fotografo ADESSO la scritta uscita (pre-mute)
        about_to_mute = not ch.get('muted')
        if about_to_mute:
            try:
                ch['_out_snap'] = (ch['out_label'].cget('text'), ch['out_label'].cget('bg'))
            except Exception:
                ch['_out_snap'] = None
        _orig(self, channel)
        # se ora e' TORNATO acceso, rimetto la scritta ESATTAMENTE com'era prima del mute
        try:
            if not ch.get('muted'):
                snap = ch.get('_out_snap')
                if snap:
                    ch['out_label'].config(text=snap[0], bg=snap[1])
        except Exception as e:
            print('[MIX120] ripristino uscita:', e)

    P._toggle_mute_orig120 = _orig
    P._toggle_mute = _toggle_mute
    P._uscita120b = True
    print('[MIX120] unmute: la scritta uscita torna identica a prima del mute')
    return True


def revert():
    pass


try:
    apply()
except Exception as _e:
    print('patch 120: %s' % _e)
