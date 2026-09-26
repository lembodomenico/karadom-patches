import ctypes
import threading

DWORD = ctypes.c_uint32
BASS_ATTRIB_VOL = 2
BASS_FX_BFX_BQF = 0x10013
BQF_LOWSHELF = 7
BASS_BFX_CHANALL = -1


class BASS_BFX_BQF(ctypes.Structure):
    _fields_ = [("lFilter", ctypes.c_int), ("fCenter", ctypes.c_float),
                ("fGain", ctypes.c_float), ("fBandwidth", ctypes.c_float),
                ("fQ", ctypes.c_float), ("fS", ctypes.c_float),
                ("lChannel", ctypes.c_int)]


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_122', '1')) == '0'
    except Exception:
        return False


def _cfg(k, d):
    try:
        from moduli.database import Database
        v = Database.get_config(k, d)
        return v if v not in (None, '') else d
    except Exception:
        return d


def _int(v, d):
    try:
        return int(float(v))
    except Exception:
        return d


def _applica_bassi(eng):
    try:
        import moduli.bass_engine as be
        b = getattr(getattr(be, '_lib', None), 'bass', None)
    except Exception:
        return
    st = getattr(eng, '_stream', 0)
    if not b or not st:
        return
    if not getattr(eng, '_exp_soft_active', False):
        return
    bas = _int(_cfg('exp_sw_bass', '75'), 75)
    gb = (max(0, min(100, bas)) - 50) / 50.0 * 15.0     # -15..+15 dB
    try:
        b.BASS_ChannelSetFX.restype = DWORD
        b.BASS_ChannelSetFX.argtypes = [DWORD, DWORD, ctypes.c_int]
        b.BASS_FXSetParameters.argtypes = [DWORD, ctypes.c_void_p]
        b.BASS_ChannelSetAttribute.argtypes = [DWORD, DWORD, ctypes.c_float]
    except Exception:
        pass
    # low-shelf a 220 Hz
    try:
        hb = getattr(eng, '_fx_bass122', 0)
        if not hb:
            hb = b.BASS_ChannelSetFX(st, BASS_FX_BFX_BQF, 5)
            eng._fx_bass122 = hb
        if hb:
            p = BASS_BFX_BQF(BQF_LOWSHELF, 220.0, gb, 0.0, 0.0, 1.0, BASS_BFX_CHANALL)
            r = b.BASS_FXSetParameters(hb, ctypes.byref(p))
            print('[BASSI122] low-shelf 220Hz gain=%.1f dB set=%s (fx=%s)' % (gb, r, hb))
        else:
            try:
                b.BASS_ErrorGetCode.restype = ctypes.c_int
                ec = b.BASS_ErrorGetCode()
            except Exception:
                ec = '?'
            print('[BASSI122] BQF non creato (err=%s) - costante sbagliata?' % ec)
    except Exception as e:
        print('[BASSI122] errore BQF:', e)
    # high-shelf ACUTI (Brillantezza) — BQF, che QUI funziona (il DX8 della 109 no):
    # per schiarire un banco cupo (es. Tyroland/Biccio) senza cambiare banco.
    try:
        bri = _int(_cfg('exp_sw_bright', '50'), 50)
        gt = (max(0, min(100, bri)) - 50) / 50.0 * 12.0   # -12..+12 dB
        BQF_HIGHSHELF = 8
        ht = getattr(eng, '_fx_treble122', 0)
        if not ht:
            ht = b.BASS_ChannelSetFX(st, BASS_FX_BFX_BQF, 6)
            eng._fx_treble122 = ht
        if ht:
            pt = BASS_BFX_BQF(BQF_HIGHSHELF, 4000.0, gt, 0.0, 0.0, 1.0, BASS_BFX_CHANALL)
            rt = b.BASS_FXSetParameters(ht, ctypes.byref(pt))
            print('[BASSI122] high-shelf 4kHz (brillantezza) gain=%.1f dB set=%s (fx=%s)' % (gt, rt, ht))
        else:
            try:
                b.BASS_ErrorGetCode.restype = ctypes.c_int
                ect = b.BASS_ErrorGetCode()
            except Exception:
                ect = '?'
            print('[BASSI122] high-shelf NON creato (BASS_ChannelSetFX=0, err=%s)' % ect)
    except Exception as e:
        print('[BASSI122] errore treble:', e)
    # HEADROOM: alzando i bassi tolgo un filo di volume generale -> niente clipping
    try:
        vol = _int(_cfg('exp_sw_vol', '100'), 100)
        room = max(0.0, (max(0, min(100, bas)) - 50) / 50.0) * 0.12
        vol_eff = (max(0, min(100, vol)) / 100.0) * (1.0 - room)
        b.BASS_ChannelSetAttribute(st, BASS_ATTRIB_VOL, ctypes.c_float(vol_eff))
    except Exception:
        pass


def apply():
    if _spenta():
        return False
    import sys
    be = sys.modules.get('moduli.bass_engine')
    if be is None:
        try:
            import moduli.bass_engine as be  # noqa
        except Exception:
            print('[BASSI122] bass_engine non presente (ok)')
            return False
    BE = getattr(be, 'BassEngine', None)
    if BE is None or getattr(BE, '_bassi122', False):
        return True

    # aggancio il cursore Bassi: quando l'utente lo muove (ex._exp_soft_dsp) riapplico
    try:
        import moduli.expander_midi as ex
        _odsp = getattr(ex, '_exp_soft_dsp', None)

        def _dsp(vol=None, bright=None, reverb=None, bass=None):
            if _odsp:
                try:
                    _odsp(vol, bright, reverb, bass)
                except TypeError:
                    _odsp(vol, bright, reverb)
            try:
                from moduli.bass_engine import get_bass_engine
                _applica_bassi(get_bass_engine())
            except Exception as e:
                print('[BASSI122] dsp:', e)
        ex._exp_soft_dsp = _dsp
    except Exception as e:
        print('[BASSI122] hook dsp:', e)

    # a ogni brano (dopo il load della 109) applico i bassi buoni
    _oload = BE.load

    def _riapplica_tutto(se):
        # ri-applica TUTTO il DSP (acuti+riverbero della 109 + bassi 122): al PRIMO
        # play gli FX non prendono, e senza questo restava CUPO finche' non ri-Applicavi.
        try:
            import moduli.expander_midi as _ex
            fn = getattr(_ex, '_exp_soft_dsp', None)
            if fn:
                fn()
            else:
                _applica_bassi(se)
        except Exception as e:
            print('[BASSI122] riapplica:', e)

    def _load(self, *a, **k):
        r = _oload(self, *a, **k)
        try:
            if r and getattr(self, 'is_midi', False):
                self._fx_bass122 = 0
                self._fx_treble122 = 0
                _applica_bassi(self)
                # più refresh nei primi secondi: lo stream si stabilizza DOPO il load,
                # e finora il DSP non attaccava fino alla ri-Applica manuale.
                for _t in (0.3, 1.0, 2.0, 3.5):
                    threading.Timer(_t, lambda: _riapplica_tutto(self)).start()
        except Exception as e:
            print('[BASSI122] post-load:', e)
        return r

    BE.load = _load
    BE._bassi122 = True
    print('[BASSI122] bassi low-shelf BQF + headroom attivi (patch nuova, non sovrascritta dal manifest)')
    return True


def revert():
    pass


try:
    apply()
except Exception as _e:
    print('patch 122: %s' % _e)
