import os
import json
import threading
import ctypes

DWORD = ctypes.c_uint32
T_LM = 16.6
T_HM = -17.0
T_LOUD = -16.0
CAP = 0.85
VMAX = 2.0
G_ATTESA = 1.0   # parte a volume NORMALE (non 0.7): niente "parte piano poi alza"


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_159', '1')) == '0'
    except Exception:
        return False


def _cfgf(k, d):
    try:
        from moduli.database import Database
        return float(Database.get_config(k, str(d)))
    except Exception:
        return d


class _VOLP(ctypes.Structure):
    _fields_ = [("fTarget", ctypes.c_float), ("fCurrent", ctypes.c_float),
                ("fTime", ctypes.c_float), ("lCurve", DWORD)]


def _cache_path():
    return os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 'KaraDom', 'autoeq159.json')


def _cache_load():
    try:
        return json.load(open(_cache_path(), 'r', encoding='utf-8'))
    except Exception:
        return {}


def _cache_save(c):
    try:
        json.dump(c, open(_cache_path(), 'w', encoding='utf-8'))
    except Exception:
        pass


def _chiave(eng, path):
    try:
        st = os.stat(path)
        banco = str(getattr(eng, '_soundfont_path', '') or getattr(eng, 'soundfont_path', '') or '')
        return '%s|%d|%d|%s' % (os.path.normcase(path), st.st_size, int(st.st_mtime), os.path.basename(banco))
    except Exception:
        return None


def _gain(eng, g, secs):
    try:
        import moduli.bass_engine as BE
        b = BE._lib.bass
        st = getattr(eng, '_stream', 0)
        if not b or not st:
            return
        b.BASS_ChannelSetFX.restype = DWORD
        b.BASS_ChannelSetFX.argtypes = [DWORD, DWORD, ctypes.c_int]
        b.BASS_FXSetParameters.argtypes = [DWORD, ctypes.c_void_p]
        h = getattr(eng, '_fx_vol159', 0)
        if not h or getattr(eng, '_fx_vol159_st', 0) != st:
            h = b.BASS_ChannelSetFX(st, 9, 100)
            eng._fx_vol159 = h
            eng._fx_vol159_st = st
        if h:
            # ISTANTANEO: applico subito il volume giusto (fCurrent=fTarget=g, tempo=0).
            # Niente rampa: prima "partiva piano e saliva man mano" -> brutto.
            b.BASS_FXSetParameters(h, ctypes.byref(_VOLP(float(g), float(g), 0.0, 0)))
    except Exception as e:
        print('[AUTOEQ159] gain:', e)


def _biquad_ir(f0, g_db, tipo, sr, n=8192):
    import numpy as np
    if abs(g_db) < 1e-3:
        h = np.zeros(n); h[0] = 1.0
        return h
    A = 10 ** (g_db / 40.0); w0 = 2 * np.pi * f0 / sr; cw, sw = np.cos(w0), np.sin(w0)
    al = sw / 2 * np.sqrt(2); k = 2 * np.sqrt(A) * al
    if tipo == 'low':
        b = [A * ((A + 1) - (A - 1) * cw + k), 2 * A * ((A - 1) - (A + 1) * cw), A * ((A + 1) - (A - 1) * cw - k)]
        a = [(A + 1) + (A - 1) * cw + k, -2 * ((A - 1) + (A + 1) * cw), (A + 1) + (A - 1) * cw - k]
    else:
        b = [A * ((A + 1) + (A - 1) * cw + k), -2 * A * ((A - 1) + (A + 1) * cw), A * ((A + 1) + (A - 1) * cw - k)]
        a = [(A + 1) - (A - 1) * cw + k, 2 * ((A - 1) - (A + 1) * cw), (A + 1) - (A - 1) * cw - k]
    b = [v / a[0] for v in b]; a = [v / a[0] for v in a]
    h = [0.0] * n; x1 = x2 = y1 = y2 = 0.0
    for i in range(n):
        x0 = 1.0 if i == 0 else 0.0
        y0 = b[0] * x0 + b[1] * x1 + b[2] * x2 - a[1] * y1 - a[2] * y2
        h[i] = y0; x2, x1 = x1, x0; y2, y1 = y1, y0
    return np.array(h)


def _filtra(x, h):
    import numpy as np
    n = len(h); B = 1 << 16; N = 1 << (int(np.ceil(np.log2(B + n))))
    H = np.fft.rfft(h, N); y = np.zeros(len(x) + n)
    for i in range(0, len(x), B):
        seg = x[i:i + B]
        y[i:i + len(seg) + n - 1] += np.fft.irfft(np.fft.rfft(seg, N) * H, N)[:len(seg) + n - 1]
    return y[:len(x)]


def _misura(eng, path):
    import numpy as np
    import moduli.bass_engine as BE
    b = BE._lib.bass; m = BE._lib.bassmidi
    font = getattr(eng, '_font', 0)
    if not b or not m or not font:
        return None
    SR = 44100

    class FONT(ctypes.Structure):
        _fields_ = [("font", DWORD), ("preset", ctypes.c_int), ("bank", ctypes.c_int)]
    m.BASS_MIDI_StreamCreateFile.restype = DWORD
    m.BASS_MIDI_StreamCreateFile.argtypes = [ctypes.c_int, ctypes.c_wchar_p, ctypes.c_uint64, ctypes.c_uint64, DWORD, DWORD]
    m.BASS_MIDI_StreamSetFonts.argtypes = [DWORD, ctypes.c_void_p, DWORD]
    b.BASS_ChannelGetData.restype = ctypes.c_int
    b.BASS_ChannelGetData.argtypes = [DWORD, ctypes.c_void_p, DWORD]
    b.BASS_StreamFree.argtypes = [DWORD]
    st = m.BASS_MIDI_StreamCreateFile(0, path, 0, 0, 0x200000 | 0x100 | 0x80000000, SR)
    if not st:
        return None
    m.BASS_MIDI_StreamSetFonts(st, ctypes.byref(FONT(font, -1, 0)), 1)
    mx = SR * 8 * int(_cfgf('auto_secs159', 420))
    buf = (ctypes.c_char * 1048576)(); pcm = bytearray()
    while len(pcm) < mx:
        g = b.BASS_ChannelGetData(st, buf, 1048576)
        if g <= 0:
            break
        pcm.extend(buf.raw[:g])
    b.BASS_StreamFree(st)
    if len(pcm) < SR * 8 * 5:
        return None
    x = np.frombuffer(bytes(pcm[:len(pcm) // 8 * 8]), dtype='<f4').astype(np.float64).reshape(-1, 2)
    mono = x.mean(1)
    if float(np.sqrt(np.mean(mono ** 2))) < 1e-5:
        return None
    NFFT = 4096; win = np.hanning(NFFT)
    M = np.mean([np.abs(np.fft.rfft(mono[i:i + NFFT] * win)) for i in range(0, len(mono) - NFFT, NFFT)], axis=0)
    fr = np.fft.rfftfreq(NFFT, 1.0 / SR)
    def _bil(sig):
        Ms = np.mean([np.abs(np.fft.rfft(sig[i:i + NFFT] * win)) for i in range(0, len(sig) - NFFT, NFFT)], axis=0)
        bd = lambda lo, hi: float(np.sqrt(np.mean(Ms[(fr >= lo) & (fr < hi)] ** 2)) + 1e-12)
        return 20 * np.log10(bd(20, 250) / bd(250, 4000)), 20 * np.log10(bd(4000, 16000) / bd(250, 4000))
    lm, hm = _bil(mono)
    TL, TH = _cfgf('auto_tgt_lm159', T_LM), _cfgf('auto_tgt_hm159', T_HM)
    MX = _cfgf('auto_max_db159', 9.0)
    bass_db = float(np.clip(TL - lm, -MX, MX)); bright_db = float(np.clip(TH - hm, -MX, MX))
    for _ in range(int(_cfgf('auto_giri159', 3))):
        kb = int(round(min(100, max(0, 50 + bass_db / 15.0 * 50))))
        kbr = int(round(min(100, max(0, 50 + bright_db / 12.0 * 50))))
        gb = (kb - 50) / 50.0 * 15.0; gt = (kbr - 50) / 50.0 * 12.0
        hh = np.convolve(_biquad_ir(220.0, gb, 'low', SR), _biquad_ir(4000.0, gt, 'high', SR))[:8192]
        l2, h2 = _bil(_filtra(mono, hh))
        bass_db = float(np.clip(bass_db + (TL - l2), -MX, MX)); bright_db = float(np.clip(bright_db + (TH - h2), -MX, MX))
    kb = int(round(min(100, max(0, 50 + bass_db / 15.0 * 50))))
    kbr = int(round(min(100, max(0, 50 + bright_db / 12.0 * 50))))
    gb = (kb - 50) / 50.0 * 15.0; gt = (kbr - 50) / 50.0 * 12.0
    room = max(0.0, (kb - 50) / 50.0) * 0.12
    h = np.convolve(_biquad_ir(220.0, gb, 'low', SR), _biquad_ir(4000.0, gt, 'high', SR))[:8192]
    y = np.stack([_filtra(x[:, 0], h), _filtra(x[:, 1], h)], 1) * (1 - room)
    pk = float(np.max(np.abs(y))) + 1e-9
    ym = y.mean(1); w = int(0.4 * SR); n = len(ym) // w
    r = np.sqrt((ym[:n * w].reshape(n, w) ** 2).mean(1)) + 1e-12
    loud = float(20 * np.log10(np.sqrt(np.mean(r[r >= np.median(r)] ** 2))))
    g = min(10 ** ((_cfgf('auto_tgt_loud159', T_LOUD) - loud) / 20.0), _cfgf('auto_cap159', CAP) / pk, VMAX)
    g = float(max(0.25, g))
    return dict(kb=kb, kbr=kbr, g=g, lm=round(lm, 1), hm=round(hm, 1), picco=round(pk, 3), loud=round(loud, 1))


def _applica(eng, r, secs):
    try:
        import moduli.expander_midi as ex
        if hasattr(ex, '_exp_soft_dsp'):
            ex._exp_soft_dsp(100, r['kbr'], None, r['kb'])
    except Exception as e:
        print('[AUTOEQ159] dsp:', e)
    _gain(eng, r['g'], secs)


def _lavora(eng, path):
    try:
        k = _chiave(eng, path)
        c = _cache_load()
        if k and k in c:
            _applica(eng, c[k], 0)
            print('[AUTOEQ159] %s (memoria) -> %s' % (os.path.basename(path), c[k]))
            return
        _gain(eng, G_ATTESA, 0)
        r = _misura(eng, path)
        if r is None:
            return
        if getattr(eng, 'current_file', None) != path:
            return
        _applica(eng, r, 1.5)
        if k:
            c[k] = r
            if len(c) > 5000:
                for kk in list(c.keys())[:1000]:
                    c.pop(kk, None)
            _cache_save(c)
        print('[AUTOEQ159] %s -> %s' % (os.path.basename(path), r))
    except Exception as e:
        print('[AUTOEQ159] errore:', e)


def _trova_globals157(fn, visti=None):
    visti = visti or set()
    if fn is None or id(fn) in visti:
        return None
    visti.add(id(fn))
    g = getattr(fn, '__globals__', None)
    if g is not None and '_analizza_e_applica' in g and 'karadom_patch_157' in str(g.get('__name__', '')):
        return g
    for cell in (getattr(fn, '__closure__', None) or ()):
        try:
            v = cell.cell_contents
        except Exception:
            continue
        if callable(v):
            r = _trova_globals157(v, visti)
            if r is not None:
                return r
    return None


def apply():
    if _spenta():
        return False
    try:
        import moduli.bass_engine as BE
    except Exception as e:
        print('[AUTOEQ159] bass_engine assente:', e)
        return False
    Eng = getattr(BE, 'BassEngine', None)
    if Eng is None or getattr(Eng, '_autoeq159', False):
        return True
    g157 = _trova_globals157(Eng.load)
    if g157 is not None:
        g157['_analizza_e_applica'] = lambda eng: _lavora(eng, getattr(eng, 'current_file', None))
        _o = Eng.load

        def load(self, file_path):
            self._autoeq_last = None
            return _o(self, file_path)
        Eng.load = load
        print('[AUTOEQ159] analisi della 157 sostituita (maschera Auto EQ invariata)')
    else:
        _orig = Eng.load

        def load(self, file_path):
            ok = _orig(self, file_path)
            try:
                from moduli.database import Database
                sw = str(Database.get_config('sorgente_scelta', '')) == 'software'
                if ok and sw and getattr(self, 'is_midi', False):
                    threading.Thread(target=_lavora, args=(self, str(file_path)), name='auto_eq_159', daemon=True).start()
            except Exception as e:
                print('[AUTOEQ159] hook:', e)
            return ok
        Eng.load = load
        print('[AUTOEQ159] 157 non trovata: aggancio diretto')
    Eng._autoeq159 = True
    return True


def revert():
    pass


try:
    apply()
except Exception as _e:
    print('patch 159: %s' % _e)
