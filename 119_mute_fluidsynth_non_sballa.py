def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_119', '1')) == '0'
    except Exception:
        return False


def apply():
    if _spenta():
        return False
    import sys
    fp = sys.modules.get('moduli.fluidsynth_player')
    if fp is None:
        try:
            import moduli.fluidsynth_player as fp  # noqa
        except Exception:
            print('[MUTE119] fluidsynth_player non presente (ok)')
            return False
    FP = getattr(fp, 'FluidSynthPlayer', None)
    if FP is None or getattr(FP, '_mute119', False):
        return True

    def set_channel_mute(self, channel, muted):
        self.channel_muted[channel] = muted
        if not getattr(self, 'synth', None):
            return
        if not hasattr(self, '_mute_snapshot'):
            self._mute_snapshot = {}
        if muted:
            # RILEGGO i valori VERI correnti dal synth (channel_volumes puo' essere vecchio)
            try:
                vol = int(self.synth.get_cc(channel, 7))
                expr = int(self.synth.get_cc(channel, 11))
            except Exception:
                vol = self.channel_volumes[channel]
                expr = self.channel_expression[channel]
            self._mute_snapshot[channel] = (vol, expr)
            self.synth.cc(channel, 7, 0)
            self.synth.cc(channel, 11, 0)
            self.synth.cc(channel, 123, 0)
            self.synth.cc(channel, 64, 0)
            print('[MUTE119] CH%d mute (fotografo vol=%d expr=%d)' % (channel + 1, vol, expr))
        else:
            vol, expr = self._mute_snapshot.get(
                channel, (self.channel_volumes[channel], self.channel_expression[channel]))
            self.synth.cc(channel, 7, vol)
            self.synth.cc(channel, 11, expr)
            self.synth.cc(channel, 64, self.channel_sustain[channel])
            print('[MUTE119] CH%d unmute (rimetto vol=%d expr=%d)' % (channel + 1, vol, expr))

    FP.set_channel_mute = set_channel_mute
    FP._mute119 = True
    print('[MUTE119] FluidSynth: unmute rimette il volume del mute (niente 88->100)')
    return True


def revert():
    pass


try:
    apply()
except Exception as _e:
    print('patch 119: %s' % _e)
