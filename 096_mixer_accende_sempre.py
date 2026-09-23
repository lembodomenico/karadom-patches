# 096 - Mixer: gli strumenti si accendono sempre, sia col suono interno sia con l'expander
def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_096', '1')) == '0'
    except Exception:
        return False


def apply():
    if _spenta():
        return False
    import sys
    mod = sys.modules.get('moduli.mixer')
    if mod is None:
        try:
            import moduli.mixer as mod  # noqa
        except Exception:
            print('patch 096: modulo mixer non presente (ok)')
            return False
    Panel = getattr(mod, 'MIDIMixerPanel', None)
    if Panel is None:
        print('patch 096: MIDIMixerPanel non trovato (ok)')
        return False
    if getattr(Panel, '_poll_096', False):
        return True

    def _poll_activity(self):
        if not self.visible:
            try:
                self.mixer_frame.after(500, self._poll_activity)
            except Exception:
                pass
            return
        try:
            # NIENTE filtro is_playing: con l'expander fluidsynth.is_playing puo'
            # essere False mentre il loop sta gia' segnando i canali. I dirty si
            # settano solo su nota vera e si azzerano a ogni giro: leggerli sempre
            # e' sicuro e accende i LED sia col SoundFont interno sia con l'expander.
            combined = [False] * 16
            _players = []
            # l'EXPANDER e' un player a se' (istanza separata dal singleton
            # FluidSynth): e' lui a segnare i canali quando suona l'expander.
            try:
                from moduli.expander_midi import get_active_player as _get_exp
                _ep = _get_exp()
                if _ep:
                    _players.append(_ep)
            except Exception:
                pass
            try:
                from moduli.fluidsynth_player import get_fluidsynth_player
                _fs = get_fluidsynth_player()
                if _fs:
                    _players.append(_fs)
            except Exception:
                pass
            try:
                from moduli.bass_engine import get_bass_engine
                _be = get_bass_engine()
                if _be:
                    _players.append(_be)
            except Exception:
                pass
            for p in _players:
                d = getattr(p, '_channel_dirty', None)
                if not d:
                    continue
                for i in range(16):
                    if d[i]:
                        combined[i] = True
                        d[i] = False
            for ch_idx in range(min(16, len(self.channels))):
                if combined[ch_idx]:
                    ch = self.channels[ch_idx]
                    if not ch['muted']:
                        ch['num_label'].config(bg='#00ff00', fg='black')
                        if ch_idx in self._blink_after_ids:
                            try:
                                self.mixer_frame.after_cancel(self._blink_after_ids[ch_idx])
                            except Exception:
                                pass
                        self._blink_after_ids[ch_idx] = self.mixer_frame.after(
                            100, lambda c=ch_idx: self._reset_blink(c))
        except Exception:
            pass
        try:
            self.mixer_frame.after(250, self._poll_activity)
        except Exception:
            pass

    Panel._poll_activity_orig_096 = Panel._poll_activity
    Panel._poll_activity = _poll_activity
    Panel._poll_096 = True
    print('[MIX] patch 096: il mixer legge i due player (interno + expander), si accende sempre')
    return True


def revert():
    try:
        import sys
        mod = sys.modules.get('moduli.mixer')
        Panel = getattr(mod, 'MIDIMixerPanel', None) if mod else None
        if Panel is not None and getattr(Panel, '_poll_096', False):
            if hasattr(Panel, '_poll_activity_orig_096'):
                Panel._poll_activity = Panel._poll_activity_orig_096
            del Panel._poll_096
    except Exception:
        pass


try:
    apply()
except Exception as _e:
    print('patch 096: %s' % _e)
