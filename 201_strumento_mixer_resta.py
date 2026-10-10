# 201 - lo strumento cambiato dal mixer resta anche quando il brano lo ricambia (X-Light, SoundFont)

import sys
import types

_VER = 1
_SORGENTE = '# -*- coding: utf-8 -*-\n"""Strumenti scelti dal Mixer che RESTANO anche col motore BASS.\n\nCol motore BASS (SoundFont e expander software, banco X-Light compreso) il Mixer\ncambiava lo strumento con un solo evento: al primo cambio di strumento scritto nel\nfile (le basi M-Live lo rimandano spesso, a ogni sezione) BASSMIDI rimetteva il suo,\ne dopo un salto nel brano pure. La rimappa permanente col BASS non c\'era proprio\n(esiste solo in FluidSynthPlayer).\n\nQui:\n  * il canale cambiato dal Mixer resta bloccato su quello strumento per tutto il brano;\n  * la rimappa salvata (Si\' = permanente) vale anche col BASS, su ogni brano;\n  * ogni cambio di strumento del file passa da un sync BASS (solo sugli eventi\n    PROGRAM, pochi per brano) che rimette subito quello scelto;\n  * dopo play/seek si riapplica tutto, perche\' il salto rimette lo stato del file.\n"""\nimport ctypes\n\n_VER = 1\n_SYNC_MIDI_EVENT = 0x10004\n_SYNC_MIXTIME = 0x40000000\n_EV_PROGRAM = 2\n_EV_BANK = 10\n_SYNCPROC = ctypes.WINFUNCTYPE(None, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p) \\\n    if hasattr(ctypes, \'WINFUNCTYPE\') else \\\n    ctypes.CFUNCTYPE(None, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p)\n\n\ndef _bersaglio(e, ch, prog, bank):\n    """(prog, bank) da mettere al posto di quello del file, o None."""\n    blocchi = getattr(e, \'_strum_blocchi\', None) or {}\n    if ch in blocchi:\n        return blocchi[ch]\n    m = getattr(e, \'instrument_map\', None) or {}\n    if m:\n        r = m.get((ch == 9, prog, 128 if ch == 9 else bank))\n        if r is not None:\n            return r[0], r[1]\n    return None\n\n\ndef _applica(e, ch, prog=None):\n    try:\n        if prog is None:\n            prog = e._midi_get_event(ch, _EV_PROGRAM)\n        bank = e._midi_get_event(ch, _EV_BANK)\n        t = _bersaglio(e, ch, prog, bank)\n        if t is None or (t[0] == prog and (ch == 9 or t[1] == bank)):\n            return\n        e._midi_event(ch, _EV_BANK, t[1])\n        e._midi_event(ch, _EV_PROGRAM, t[0])\n    except Exception as ex:\n        print(\'[STRUM] %s\' % ex)\n\n\ndef riapplica(e):\n    if not getattr(e, \'is_midi\', False) or not getattr(e, \'_stream\', 0):\n        return\n    if not (getattr(e, \'_strum_blocchi\', None) or getattr(e, \'instrument_map\', None)):\n        return\n    for ch in range(16):\n        _applica(e, ch)\n\n\ndef _aggancia_sync(e):\n    """Sync sugli eventi PROGRAM del file dello stream MIDI appena creato."""\n    try:\n        from moduli.bass_engine import _lib\n    except Exception:\n        from moduli.bass_engine import _lib\n    b = _lib.bass\n    if not b or not getattr(e, \'_stream\', 0):\n        return\n\n    def _cb(handle, channel, data, user):\n        try:\n            _applica(e, (data >> 16) & 0xFFFF, data & 0xFFFF)\n        except Exception:\n            pass\n\n    e._strum_cb = _SYNCPROC(_cb)            # tenuto vivo: se il GC lo libera BASS va in crash\n    b.BASS_ChannelSetSync.restype = ctypes.c_uint32\n    b.BASS_ChannelSetSync.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint64, _SYNCPROC, ctypes.c_void_p]\n    h = b.BASS_ChannelSetSync(e._stream, _SYNC_MIDI_EVENT | _SYNC_MIXTIME, ctypes.c_uint64(_EV_PROGRAM), e._strum_cb, None)\n    if not h:\n        print(\'[STRUM] sync non messo (err %s)\' % e._get_error())\n\n\ndef _carica_rimappa(e):\n    try:\n        try:\n            from .fluidsynth_player import FluidSynthPlayer\n        except Exception:\n            from moduli.fluidsynth_player import FluidSynthPlayer\n        e.instrument_map = dict(FluidSynthPlayer.load_instrument_remap() or {})\n    except Exception as ex:\n        print(\'[STRUM] rimappa: %s\' % ex)\n        e.instrument_map = {}\n\n\ndef installa(BE, MIXER=None):\n    """Aggancia BassEngine (e il pannello Mixer, se dato) una volta per versione."""\n    if BE is not None and getattr(BE, \'_strum_ver\', None) != _VER:\n        o = {n: getattr(BE, \'_strum_o_\' + n, None) or getattr(BE, n)\n             for n in (\'_load_midi\', \'play\', \'seek\', \'seek_ms\')}\n        for n, f in o.items():\n            setattr(BE, \'_strum_o_\' + n, f)\n\n        def _load_midi(self, file_path):\n            self._strum_blocchi = {}             # brano nuovo: i blocchi "solo per questo brano" si azzerano\n            r = o[\'_load_midi\'](self, file_path)\n            if r:\n                _carica_rimappa(self)\n                _aggancia_sync(self)\n                riapplica(self)\n            return r\n\n        def play(self, *a, **k):\n            r = o[\'play\'](self, *a, **k)\n            riapplica(self)\n            return r\n\n        def seek(self, *a, **k):\n            r = o[\'seek\'](self, *a, **k)\n            riapplica(self)\n            return r\n\n        def seek_ms(self, *a, **k):\n            r = o[\'seek_ms\'](self, *a, **k)\n            riapplica(self)\n            return r\n\n        def set_instrument_map(self, mapping):\n            self.instrument_map = dict(mapping or {})\n            riapplica(self)\n\n        BE._load_midi, BE.play, BE.seek, BE.seek_ms = _load_midi, play, seek, seek_ms\n        BE.set_instrument_map = set_instrument_map\n        BE._strum_ver = _VER\n\n    if MIXER is not None and getattr(MIXER, \'_strum_ver\', None) != _VER:\n        o_cambio = getattr(MIXER, \'_strum_o_change\', None) or MIXER._on_instrument_change\n        MIXER._strum_o_change = o_cambio\n\n        def _on_instrument_change(self, channel):\n            r = o_cambio(self, channel)\n            try:\n                pl = self._get_midi_player()\n                if pl is not None and BE is not None and isinstance(pl, BE):\n                    ch = self.channels[channel]\n                    bl = pl.__dict__.setdefault(\'_strum_blocchi\', {})\n                    is_drum = channel == 9\n                    if ch[\'program\'] == ch[\'orig_program\'] and (is_drum or ch[\'bank\'] == ch[\'orig_bank\']):\n                        bl.pop(channel, None)\n                    else:\n                        bl[channel] = (ch[\'program\'], ch[\'bank\'])\n                    print(\'[STRUM] canale %d: %s\' % (channel + 1, bl.get(channel, \'originale\')))\n            except Exception as ex:\n                print(\'[STRUM] mixer: %s\' % ex)\n            return r\n\n        MIXER._on_instrument_change = _on_instrument_change\n        MIXER._strum_ver = _VER\n'


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_201', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def _modulo():
    try:
        import importlib
        vero = importlib.import_module('moduli.bass_strumenti')
        if getattr(vero, '__file__', '') != '<patch201>' and hasattr(vero, 'installa'):
            return vero
    except Exception:
        pass
    m = sys.modules.get('moduli.bass_strumenti')
    if m is not None and getattr(m, '_ver201', None) == _VER:
        return m
    m = types.ModuleType('moduli.bass_strumenti')
    m.__file__ = '<patch201>'
    exec(compile(_SORGENTE, 'bass_strumenti_201', 'exec'), m.__dict__)
    m._ver201 = _VER
    sys.modules['moduli.bass_strumenti'] = m
    try:
        import moduli
        moduli.bass_strumenti = m
    except Exception:
        pass
    return m


def apply():
    if _spenta():
        return False
    try:
        m = _modulo()
        import moduli.bass_engine as be
        try:
            import moduli.mixer as mx
            pan = getattr(mx, 'MIDIMixerPanel', None)
        except Exception as e:
            print('[STRUM201] mixer:', e)
            pan = None
        m.installa(getattr(be, 'BassEngine', None), pan)
        print('[STRUM201] strumenti del mixer bloccati anche col BASS')
    except Exception as e:
        print('[STRUM201] hook:', e)
    return True


def revert():
    pass


try:
    apply()
except Exception as _e:
    print('patch 201: %s' % _e)
