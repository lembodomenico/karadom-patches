import os, ctypes, hashlib, threading

DWORD = ctypes.c_uint32
QWORD = ctypes.c_uint64
_SECRET = b"KaraDomLive::banco::v1::9f3a-not-a-plain-sf2"
_BLK = 65536


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_125', '1')) == '0'
    except Exception:
        return False


def _keystream():
    out = bytearray(); i = 0
    while len(out) < _BLK:
        out += hashlib.sha256(_SECRET + i.to_bytes(4, 'big')).digest(); i += 1
    return bytes(out[:_BLK])


_KS = _keystream()


def _xor(data, off):
    s = off % _BLK
    reps = (s + len(data) + _BLK - 1) // _BLK
    tile = (_KS * (reps + 1))[s:s + len(data)]
    n = len(data)
    return (int.from_bytes(data, 'big') ^ int.from_bytes(tile, 'big')).to_bytes(n, 'big')


def _decifra_in_ram(path, chunk=_BLK * 32):
    # DECIFRA TUTTO IN RAM una volta sola (sul thread chiamante): nessuno XOR e
    # nessun file girano poi nel thread interno di BASS (era quello a crashare).
    parti = []; off = 0
    with open(path, 'rb') as fi:
        while True:
            d = fi.read(chunk)
            if not d:
                break
            parti.append(_xor(d, off)); off += len(d)
    return b"".join(parti)


CLOSEPROC = ctypes.WINFUNCTYPE(None, ctypes.c_void_p)
LENPROC = ctypes.WINFUNCTYPE(QWORD, ctypes.c_void_p)
READPROC = ctypes.WINFUNCTYPE(DWORD, ctypes.c_void_p, DWORD, ctypes.c_void_p)
SEEKPROC = ctypes.WINFUNCTYPE(ctypes.c_int, QWORD, ctypes.c_void_p)


class _FP(ctypes.Structure):
    _fields_ = [("close", CLOSEPROC), ("length", LENPROC),
                ("read", READPROC), ("seek", SEEKPROC)]


_ALIVE = {}   # tiene vivi buffer+callback finche' il font esiste


def _mkprocs_ram(dec):
    # dec = SF2 in chiaro (bytes immutabili in RAM). I callback fanno SOLO memmove.
    size = len(dec)
    lk = threading.Lock()
    st = {"pos": 0}

    def _c(u):
        return

    def _l(u):
        return size

    def _r(buf, length, u):
        try:
            with lk:
                p = st["pos"]
                if p >= size:
                    return 0
                end = p + length
                if end > size:
                    end = size
                n = end - p
                ctypes.memmove(buf, dec[p:end], n)
                st["pos"] = end
                return n
        except Exception:
            return 0

    def _s(off, u):
        try:
            with lk:
                if 0 <= off <= size:
                    st["pos"] = off
                    return 1
                return 0
        except Exception:
            return 0
    return _FP(CLOSEPROC(_c), LENPROC(_l), READPROC(_r), SEEKPROC(_s))


def _banco_path():
    # banco cifrato KaraDomLive, tra le dipendenze
    return os.path.join(os.environ.get('LOCALAPPDATA', ''), 'KaraDom',
                        'dipendenze', 'rt', 'core.kdl')


def _e_cifrato(p):
    try:
        return (p.lower().endswith('.kdl')
                or os.path.normcase(os.path.abspath(p)) == os.path.normcase(os.path.abspath(_banco_path())))
    except Exception:
        return p.lower().endswith('.kdl')


def apply():
    if _spenta():
        return False
    kdl = _banco_path()

    # 1) l'expander software carica SOLO questo banco
    try:
        from moduli.database import Database
        if os.path.isfile(kdl):
            Database.set_config('exp_banco_path', kdl)
    except Exception as e:
        print('[KDL125] cfg:', e)

    # 2) i file .kdl si caricano DECIFRANDO IN RAM (BASS_MIDI_FontInitUser da buffer)
    try:
        import moduli.bass_engine as be
        BE = getattr(be, 'BassEngine', None)
        if BE and not getattr(BE, '_kdl125', False):
            _orig = BE._load_soundfont

            def _load_sf(self, sf_path):
                p = str(sf_path)
                if _e_cifrato(p) and os.path.exists(p):
                    m = getattr(be, '_lib', None)
                    m = getattr(m, 'bassmidi', None) if m else None
                    if not m:
                        return False
                    try:
                        dec = _decifra_in_ram(p)
                    except Exception as e:
                        print('[KDL125] decifra fallita:', e); return False
                    procs = _mkprocs_ram(dec)
                    m.BASS_MIDI_FontInitUser.restype = DWORD
                    m.BASS_MIDI_FontInitUser.argtypes = [ctypes.c_void_p, ctypes.c_void_p, DWORD]
                    font = m.BASS_MIDI_FontInitUser(ctypes.byref(procs), None, 0)
                    if not font:
                        print('[KDL125] FontInitUser fallito'); return False
                    _ALIVE[font] = (procs, dec)
                    self._font = font
                    self._soundfont_path = p
                    print('[KDL125] banco cifrato caricato in RAM (font=%s)' % font)
                    return True
                return _orig(self, sf_path)

            BE._load_soundfont = _load_sf
            BE._kdl125 = True
    except Exception as e:
        print('[KDL125] hook load:', e)

    # 3) nascondi la scelta del banco nella finestra Expander (106)
    try:
        import moduli.expander_gui as eg
        F = getattr(eg, 'FinestraExpander', None)
        if F and hasattr(F, '_costruisci') and not getattr(F, '_kdl125', False):
            _oc = F._costruisci

            def _c(self):
                _oc(self)
                try:
                    ws = []
                    def walk(w):
                        for ch in w.winfo_children():
                            ws.append(ch); walk(ch)
                    walk(self.win)
                    for w in ws:
                        try:
                            cls = w.winfo_class()
                            txt = (w.cget('text') or '').lower() if cls in ('Button', 'Label') else ''
                        except Exception:
                            continue
                        if cls in ('Button', 'Label') and 'banco' in txt:
                            try: w.pack_forget()
                            except Exception: pass
                except Exception as e:
                    print('[KDL125] ui:', e)

            F._costruisci = _c
            F._kdl125 = True
    except Exception as e:
        print('[KDL125] gui:', e)

    print('[KDL125] expander: solo core.kdl (cifrato, decifrato in RAM); scelta nascosta')
    return True


def revert():
    pass


try:
    apply()
except Exception as _e:
    print('patch 125: %s' % _e)
