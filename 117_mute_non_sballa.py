def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_117', '1')) == '0'
    except Exception:
        return False


def apply():
    if _spenta():
        return False
    import sys
    be = sys.modules.get('moduli.bass_engine')
    if be is None:
        try:
            import moduli.bass_engine as be  # noqa
        except Exception:
            print('[MUTE117] bass_engine non presente (ok)')
            return False
    BE = getattr(be, 'BassEngine', None)
    if BE is None or getattr(BE, '_mute117', False):
        return True

    MIX = getattr(be, 'MIDI_EVENT_MIXLEVEL', 0x10000)
    VOL = getattr(be, 'MIDI_EVENT_VOLUME', 12)
    EXPR = getattr(be, 'MIDI_EVENT_EXPRESSION', 14)
    NOFF = getattr(be, 'MIDI_EVENT_NOTESOFF', 18)

    # 1) mute/unmute via SOLO MIXLEVEL: CC7 (Volume) e CC11 (Expression) del brano
    #    NON vengono piu' toccati -> allo unmute il suono torna com'era.
    def _set_channel_mute(self, channel, muted):
        try:
            self.channel_muted[channel] = muted
        except Exception:
            return
        if not getattr(self, 'is_midi', False) or not getattr(self, '_stream', 0):
            return
        if muted:
            self._midi_event(channel, MIX, 0)
            self._midi_event(channel, NOFF, 0)
            try:
                self.active_notes[channel] = 0
            except Exception:
                pass
        else:
            try:
                vol = self.channel_volumes[channel]
            except Exception:
                vol = 100
            self._midi_event(channel, MIX, self._vol_to_mixlevel(vol))

    # 2) il resto del codice (es. riapplica-mute al play) manda ancora CC7/CC11=0
    #    sui canali mutati: quei due li FILTRO, cosi' non sporcano lo stato del brano.
    #    Il MIXLEVEL=0 e il NOTESOFF passano: il canale resta muto lo stesso.
    _orig_ev = BE._midi_event

    def _midi_event(self, channel, event, param):
        try:
            if event in (VOL, EXPR) and int(param) == 0 \
                    and 0 <= channel < 16 and self.channel_muted[channel]:
                return True
        except Exception:
            pass
        return _orig_ev(self, channel, event, param)

    BE._mute117_ev_orig = _orig_ev
    BE._midi_event = _midi_event
    BE.set_channel_mute = _set_channel_mute
    BE._mute117 = True
    print('[MUTE117] mute via MIXLEVEL: unmute non sballa piu\' il suono (CC7/CC11 intatti)')
    return True


def revert():
    try:
        import sys
        be = sys.modules.get('moduli.bass_engine')
        BE = getattr(be, 'BassEngine', None) if be else None
        if BE is not None and getattr(BE, '_mute117', False):
            if hasattr(BE, '_mute117_ev_orig'):
                BE._midi_event = BE._mute117_ev_orig
            del BE._mute117
    except Exception:
        pass


try:
    apply()
except Exception as _e:
    print('patch 117: %s' % _e)
