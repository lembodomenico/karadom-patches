import os
import threading
import ctypes


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_157', '1')) == '0'
    except Exception:
        return False


def _cfgf(k, d):
    try:
        from moduli.database import Database
        return float(Database.get_config(k, str(d)))
    except Exception:
        return d


def _is_software():
    try:
        from moduli.database import Database
        return str(Database.get_config('sorgente_scelta', '')) == 'software'
    except Exception:
        return False


def _analizza_e_applica(eng):
    import numpy as np
    import moduli.bass_engine as BE
    b = BE._lib.bass; m = BE._lib.bassmidi
    if not b or not m:
        return
    font = getattr(eng, '_font', 0); path = getattr(eng, 'current_file', None)
    if not font or not path or not os.path.exists(path):
        return
    SR = 44100
    DWORD = ctypes.c_uint32

    class FONT(ctypes.Structure):
        _fields_ = [("font", DWORD), ("preset", ctypes.c_int), ("bank", ctypes.c_int)]
    m.BASS_MIDI_StreamCreateFile.restype = DWORD
    m.BASS_MIDI_StreamCreateFile.argtypes = [ctypes.c_int, ctypes.c_wchar_p, ctypes.c_uint64, ctypes.c_uint64, DWORD, DWORD]
    m.BASS_MIDI_StreamSetFonts.argtypes = [DWORD, ctypes.c_void_p, DWORD]
    b.BASS_ChannelGetData.restype = ctypes.c_int; b.BASS_ChannelGetData.argtypes = [DWORD, ctypes.c_void_p, DWORD]
    b.BASS_StreamFree.argtypes = [DWORD]
    st = m.BASS_MIDI_StreamCreateFile(0, path, 0, 0, 0x200000 | 0x80000000, SR)  # DECODE|UNICODE
    if not st:
        return
    m.BASS_MIDI_StreamSetFonts(st, ctypes.byref(FONT(font, -1, 0)), 1)
    secs = int(_cfgf('auto_secs', 18))
    buf = (ctypes.c_char * 262144)(); pcm = bytearray(); mx = SR * 4 * secs
    while len(pcm) < mx:
        g = b.BASS_ChannelGetData(st, buf, 262144)
        if g <= 0:
            break
        pcm.extend(buf.raw[:g])
    b.BASS_StreamFree(st)
    if len(pcm) < SR * 4:
        return
    x = np.frombuffer(bytes(pcm[:len(pcm) // 4 * 4]), dtype='<i2').astype(np.float64).reshape(-1, 2).mean(1) / 32768.0
    rms = float(np.sqrt(np.mean(x ** 2))); peak = float(np.max(np.abs(x)))
    if rms < 1e-4:
        return
    NFFT = 4096; win = np.hanning(NFFT); mags = []
    for i in range(0, len(x) - NFFT, NFFT):
        mags.append(np.abs(np.fft.rfft(x[i:i + NFFT] * win)))
    M = np.mean(mags, axis=0); fr = np.fft.rfftfreq(NFFT, 1.0 / SR)
    bd = lambda lo, hi: float(np.sqrt(np.mean(M[(fr >= lo) & (fr < hi)] ** 2)) + 1e-9)
    low, mid, high = bd(20, 250), bd(250, 4000), bd(4000, 16000)
    lm = 20 * np.log10(low / mid); hm = 20 * np.log10(high / mid)

    TGT_RMS = _cfgf('auto_tgt_rms', 0.12)
    TGT_LM = _cfgf('auto_tgt_lowmid', 2.0)
    TGT_HM = _cfgf('auto_tgt_highmid', -3.0)
    MAXDB = _cfgf('auto_max_db', 6.0)
    PEAKCAP = _cfgf('auto_peak_cap', 0.89)

    bass_db = float(np.clip(TGT_LM - lm, -MAXDB, MAXDB))
    bright_db = float(np.clip(TGT_HM - hm, -MAXDB, MAXDB))
    vol_rms = TGT_RMS / rms
    vol_peak = PEAKCAP / (peak * (10 ** (max(0.0, bass_db) / 20.0)) + 1e-9)
    vol_gain = float(np.clip(min(vol_rms, vol_peak), 0.25, 1.0))

    to_knob = lambda db: int(round(min(100, max(0, 50 + db / 15.0 * 50))))
    kv = int(round(vol_gain * 100)); kb = to_knob(bass_db); kbr = to_knob(bright_db)
    print('[AUTOEQ157] %s | picco=%.2f rms=%.3f gravi-medi=%+.1f acuti-medi=%+.1f -> Vol=%d Bassi=%d Brill=%d'
          % (os.path.basename(path), peak, rms, lm, hm, kv, kb, kbr))
    try:
        import moduli.expander_midi as ex
        if hasattr(ex, '_exp_soft_dsp'):
            ex._exp_soft_dsp(kv, kbr, None, kb)   # vol, bright, reverb(inalterato), bass
    except Exception as e:
        print('[AUTOEQ157] applica:', e)


def apply():
    if _spenta():
        return False
    try:
        import moduli.bass_engine as BE
    except Exception as e:
        print('[AUTOEQ157] bass_engine assente:', e); return False
    Eng = getattr(BE, 'BassEngine', None)
    if Eng is None or getattr(Eng, '_autoeq157', False):
        return True
    _orig = Eng.load

    def load(self, file_path):
        ok = _orig(self, file_path)
        try:
            if ok and getattr(self, 'is_midi', False) and _is_software() and not _spenta():
                fp = str(file_path)
                if getattr(self, '_autoeq_last', None) != fp:
                    self._autoeq_last = fp
                    threading.Thread(target=_analizza_e_applica, args=(self,),
                                     name='auto_eq_157', daemon=True).start()
        except Exception as e:
            print('[AUTOEQ157] hook:', e)
        return ok

    Eng.load = load
    Eng._autoeq157 = True

    # maschera -> Auto EQ: nascondo i cursori manuali, senza toccare la 106
    try:
        import moduli.expander_gui as eg
        F = getattr(eg, 'FinestraExpander', None)
        if F and hasattr(F, '_costruisci') and not getattr(F, '_autoeq157ui', False):
            _oc = F._costruisci

            def _c(self):
                _oc(self)
                try:
                    import tkinter as tk
                    ws = []

                    def walk(w):
                        for ch in w.winfo_children():
                            ws.append(ch); walk(ch)
                    walk(self.win)
                    for w in ws:
                        try:
                            if w.winfo_class() == 'Labelframe' and 'regolazioni' in (w.cget('text') or '').lower():
                                for ch in w.winfo_children():
                                    try:
                                        ch.pack_forget()
                                    except Exception:
                                        pass
                                try:
                                    w.config(text=' Auto EQ ')
                                except Exception:
                                    pass
                                try:
                                    tk.Label(w, text="Volume, bassi e acuti regolati\nda soli per ogni brano.",
                                             bg=w.cget('bg'), fg='#9fe89f', justify='center').pack(padx=10, pady=10)
                                except Exception:
                                    pass
                        except Exception:
                            pass
                except Exception as e:
                    print('[AUTOEQ157] ui:', e)

            F._costruisci = _c
            F._autoeq157ui = True
    except Exception as e:
        print('[AUTOEQ157] gui hook:', e)

    print('[AUTOEQ157] auto-EQ + auto-livello attivo sull\'expander (niente manopole)')
    return True


def revert():
    pass


try:
    apply()
except Exception as _e:
    print('patch 157: %s' % _e)
