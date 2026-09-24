# 104 - Expander software IN-PROCESS: BASSMIDI dentro KaraDom (niente exe/loopMIDI)
import os
import ctypes

DWORD = ctypes.c_uint32
BASS_SAMPLE_FLOAT = 256
BASS_UNICODE = 0x80000000
BASS_MIDI_EVENTS_RAW = 0x10000
BASS_FX_DX8_CHORUS = 0
BASS_FX_DX8_PARAMEQ = 7
BASS_FX_DX8_REVERB = 8
BASS_CONFIG_MIDI_VOICES = 0x10402
BASS_CONFIG_BUFFER = 0
BASS_CONFIG_UPDATEPERIOD = 1
BASS_CONFIG_UPDATETHREADS = 24


class BASS_MIDI_FONT(ctypes.Structure):
    _fields_ = [("font", DWORD), ("preset", ctypes.c_int), ("bank", ctypes.c_int)]


class DX8_REVERB(ctypes.Structure):
    _fields_ = [("fInGain", ctypes.c_float), ("fReverbMix", ctypes.c_float),
                ("fReverbTime", ctypes.c_float), ("fHighFreqRTRatio", ctypes.c_float)]


class DX8_CHORUS(ctypes.Structure):
    _fields_ = [("fWetDryMix", ctypes.c_float), ("fDepth", ctypes.c_float),
                ("fFeedback", ctypes.c_float), ("fFrequency", ctypes.c_float),
                ("lWaveform", DWORD), ("fDelay", ctypes.c_float), ("lPhase", DWORD)]


class DX8_PARAMEQ(ctypes.Structure):
    _fields_ = [("fCenter", ctypes.c_float), ("fBandwidth", ctypes.c_float), ("fGain", ctypes.c_float)]


OVERLAY_MAP = [(p, 0) for p in range(0, 80)] + [(0, 128)]


def _exp_dir():
    return os.path.join(os.environ.get('LOCALAPPDATA', ''), 'KaraDom', 'dipendenze', 'Expander')


def _banco():
    d = _exp_dir()
    for c in (os.path.join(d, 'banco_toh.sf3'), os.path.join(d, 'banco.sf3'), os.path.join(d, 'banco.sf2')):
        if os.path.isfile(c):
            return c
    import glob
    g = sorted(glob.glob(os.path.join(d, '*.sf3')))
    return g[0] if g else ''


def _overlay():
    p = os.path.join(_exp_dir(), 'overlay.sf2')
    return p if os.path.isfile(p) else ''


def _on():
    try:
        from moduli.database import Database
        return str(Database.get_config('expander_socket', '0')) == '1'
    except Exception:
        return False


class _ExpEngine(object):
    """Motore BASSMIDI in tempo reale DENTRO KaraDom (riusa bass.dll/bassmidi.dll
    gia' caricate). Stream a 16 canali, banco ToH + overlay + DSP (EQ/riverbero/chorus).
    L'ExpanderPlayer gli manda il MIDI grezzo con feed() (BASS_MIDI_EVENTS_RAW)."""

    def __init__(self):
        self.bass = ctypes.WinDLL('bass.dll')
        self.bmid = ctypes.WinDLL('bassmidi.dll')
        self.stream = 0
        self.font = 0
        self.overlays = []

    def init(self, freq=48000):
        # ⛔ NON tocco la config GLOBALE di BASS (voci/buffer/update): cambiarla
        #    sporca l'audio di KaraDom. MA BASS_Init serve: assicura il device audio,
        #    se no BASS_MIDI_StreamCreate fallisce e l'expander non parte. Se KaraDom
        #    l'ha gia' fatto torna 14 (gia' inizializzato) e va bene.
        # ⛔ NIENTE config GLOBALE: BASS e' lo stesso motore degli mp3/basi di KaraDom,
        #    toccarlo li rovinerebbe. Il buffer alto lo metto SOLO sul mio stream (in start).
        b = self.bass
        b.BASS_ErrorGetCode.restype = ctypes.c_int
        b.BASS_Init.argtypes = [ctypes.c_int, DWORD, DWORD, ctypes.c_void_p, ctypes.c_void_p]
        try:
            b.BASS_Init(-1, freq, 0, 0, 0)   # -1 = device di default; 14 se gia' init: ok
        except Exception:
            pass
        return True

    def _font_init(self, path):
        m = self.bmid
        m.BASS_MIDI_FontInit.restype = DWORD
        m.BASS_MIDI_FontInit.argtypes = [ctypes.c_void_p, DWORD]
        return m.BASS_MIDI_FontInit(ctypes.c_wchar_p(path), BASS_UNICODE)

    def load_base(self, path):
        f = self._font_init(path)
        if f:
            self.font = f
            return True
        return False

    def load_overlay(self, path, mapp):
        f = self._font_init(path)
        if f:
            self.overlays.append({'font': f, 'map': list(mapp)})
            return True
        return False

    def _set_font(self, h):
        voci = []
        for ov in self.overlays:
            for pr, bk in ov['map']:
                voci.append((ov['font'], int(pr), int(bk)))
        voci.append((self.font, -1, 0))
        arr = (BASS_MIDI_FONT * len(voci))()
        for i, (fn, pr, bk) in enumerate(voci):
            arr[i].font = fn
            arr[i].preset = pr
            arr[i].bank = bk
        self.bmid.BASS_MIDI_StreamSetFonts.argtypes = [DWORD, ctypes.c_void_p, DWORD]
        self.bmid.BASS_MIDI_StreamSetFonts(h, arr, len(voci))

    def _fx(self, h):
        b = self.bass
        b.BASS_ChannelSetFX.restype = DWORD
        b.BASS_ChannelSetFX.argtypes = [DWORD, DWORD, ctypes.c_int]
        b.BASS_FXSetParameters.argtypes = [DWORD, ctypes.c_void_p]
        try:
            for cen, bw, g in ((4500.0, 12.0, 3.0), (9000.0, 12.0, 4.0)):
                hf = b.BASS_ChannelSetFX(h, BASS_FX_DX8_PARAMEQ, 2)
                if hf:
                    b.BASS_FXSetParameters(hf, ctypes.byref(DX8_PARAMEQ(cen, bw, g)))
        except Exception:
            pass
        try:
            hr = b.BASS_ChannelSetFX(h, BASS_FX_DX8_REVERB, 1)
            if hr:
                b.BASS_FXSetParameters(hr, ctypes.byref(DX8_REVERB(0.0, -9.0, 1400.0, 0.6)))
        except Exception:
            pass
        try:
            hc = b.BASS_ChannelSetFX(h, BASS_FX_DX8_CHORUS, 3)
            if hc:
                b.BASS_FXSetParameters(hc, ctypes.byref(DX8_CHORUS(22.0, 8.0, 0.0, 0.6, 1, 12.0, 4)))
        except Exception:
            pass

    def start(self, freq=48000):
        m = self.bmid
        b = self.bass
        # ⛔ NON tocco NIENTE di globale (mp3/basi intatti): creo lo stream e basta.
        m.BASS_MIDI_StreamCreate.restype = DWORD
        m.BASS_MIDI_StreamCreate.argtypes = [DWORD, DWORD, DWORD]
        self.stream = m.BASS_MIDI_StreamCreate(16, BASS_SAMPLE_FLOAT, freq)
        if not self.stream:
            return False
        # voci alte SOLO su questo stream (attributo per-stream, non tocca il globale)
        try:
            b.BASS_ChannelSetAttribute.argtypes = [DWORD, DWORD, ctypes.c_float]
            b.BASS_ChannelSetAttribute(self.stream, 0x12000, ctypes.c_float(500))  # BASS_ATTRIB_MIDI_VOICES
        except Exception:
            pass
        self._set_font(self.stream)
        # DSP (riverbero/chorus/EQ) DISATTIVATO per ora: prima il suono nudo pulito,
        # il DSP lo rimetto solo quando la base suona bene.
        # self._fx(self.stream)
        b.BASS_ChannelPlay.argtypes = [DWORD, ctypes.c_int]
        b.BASS_ChannelPlay(self.stream, 0)
        return True

    def feed(self, data):
        if not self.stream or not data:
            return
        buf = (ctypes.c_ubyte * len(data)).from_buffer_copy(data)
        self.bmid.BASS_MIDI_StreamEvents.argtypes = [DWORD, DWORD, ctypes.c_void_p, DWORD]
        self.bmid.BASS_MIDI_StreamEvents(self.stream, BASS_MIDI_EVENTS_RAW, buf, len(data))

    def free(self):
        try:
            if self.stream:
                self.bass.BASS_StreamFree.argtypes = [DWORD]
                self.bass.BASS_StreamFree(self.stream)
        except Exception:
            pass
        self.stream = 0


_ENG = None   # UN SOLO motore/stream per tutta la sessione (niente sovrapposizioni)


def _get_engine():
    global _ENG
    if _ENG is not None and _ENG.stream:
        return _ENG
    b = _banco()
    if not b:
        print('Expander in-process: banco non trovato in', _exp_dir())
        return None
    try:
        e = _ExpEngine()
        e.init()
        if not e.load_base(b):
            print('Expander in-process: banco non caricato', b)
            return None
        ov = _overlay()
        if ov:
            e.load_overlay(ov, OVERLAY_MAP)
        if not e.start():
            print('Expander in-process: stream non creato')
            return None
        _ENG = e
        print('Expander in-process: motore pronto (banco %s%s)'
              % (os.path.basename(b), ' + overlay' if ov else ''))
        return _ENG
    except Exception as ex:
        print('Expander in-process errore:', ex)
        return None


class _UscitaBassmidi(object):
    """Stessa interfaccia di _UscitaMIDI (apri/short/sysex/chiudi). Riusa UN unico
    motore BASSMIDI in-process; su chiudi lo SILENZIA (all-notes-off), non libera lo
    stream: cosi' niente stream sovrapposti e, cambiando scelta, l'expander tace subito."""

    def __init__(self, device_id, nome):
        self.device_id = device_id
        self.nome = nome or 'Expander software'
        self.aperta = False
        self._morta = False
        self._stream = None

    def apri(self):
        if _get_engine() is None:
            return False
        self.aperta = True
        return True

    def short(self, status, dato1=0, dato2=0, istante=None):
        if not self.aperta or _ENG is None:
            return
        hi = status & 0xF0
        if hi in (0xC0, 0xD0):
            _ENG.feed(bytes([status & 0xFF, dato1 & 0x7F]))
        else:
            _ENG.feed(bytes([status & 0xFF, dato1 & 0x7F, dato2 & 0x7F]))

    def sysex(self, dati, istante=None):
        if self.aperta and _ENG is not None and dati:
            _ENG.feed(bytes(dati))

    def chiudi(self):
        self.aperta = False
        try:
            if _ENG is not None:
                for ch in range(16):
                    _ENG.feed(bytes([0xB0 | ch, 123, 0]))   # all notes off
                    _ENG.feed(bytes([0xB0 | ch, 120, 0]))   # all sound off
        except Exception:
            pass


def apply():
    import sys
    mod = sys.modules.get('moduli.expander_midi')
    if mod is None:
        try:
            import moduli.expander_midi as mod  # noqa
        except Exception:
            print('patch 104: expander_midi non presente (ok)')
            return False
    if getattr(mod, '_inproc_104', False):
        return True
    orig = getattr(mod, '_UscitaMIDI', None)
    if orig is None:
        return True

    def _fabbrica(device_id, nome):
        # in-process SOLO per la porta finta "Expander software" (id=-1); l'HW resta winmm
        if _on() and (device_id == -1 or 'software' in (nome or '').lower()):
            return _UscitaBassmidi(device_id, nome)
        return orig(device_id, nome)

    mod._UscitaMIDI_orig104 = orig
    mod._UscitaMIDI = _fabbrica
    mod._inproc_104 = True

    # niente porta MIDI: se expander_socket=1, detect_expander da' una porta finta,
    # MA solo se non c'e' un expander HARDWARE (quello ha la precedenza, come prima).
    if not getattr(mod, '_detect_104', False) and hasattr(mod, 'detect_expander'):
        _od = mod.detect_expander

        def _detect(*a, **k):
            real = _od(*a, **k)
            if _on():
                if real:
                    nome = (real.get('nome', '') or '').lower()
                    # HW VERO = non loopMIDI e non il synth software di Windows
                    # (Microsoft GS Wavetable). Quelli NON sono un expander -> in-process.
                    finto = ('loop' in nome or 'wavetable' in nome or 'microsoft' in nome
                             or 'gs ' in nome or nome.strip() == '')
                    if not finto:
                        return real            # expander HARDWARE (X-Light...) -> precedenza
                return {'nome': 'Expander software', 'id': -1, 'punteggio': 50}
            return real

        mod._detect_orig104 = _od
        mod.detect_expander = _detect
        mod._detect_104 = True

    # etichetta mixer: solo "Expander Software"
    try:
        import moduli.mixer as _mx
        P = getattr(_mx, 'MIDIMixerPanel', None)
        if P is not None and hasattr(P, '_update_soundfont_display') and not getattr(P, '_lbl_104', False):
            _osf = P._update_soundfont_display

            def _usd(self, *a, **k):
                r = _osf(self, *a, **k)
                try:
                    lbl = getattr(self, 'sf_label', None)
                    if lbl is not None:
                        t = (lbl.cget('text') or '').lower()
                        if 'expander software' in t or 'loop' in t:
                            lbl.config(text='Expander Software', fg='#c77dff')
                except Exception:
                    pass
                return r

            P._update_soundfont_display = _usd
            P._lbl_104 = True
    except Exception as e:
        print('[EXP] 104 etichetta mixer:', e)

    # "Salva" deve APPLICARE SUBITO al brano in corso: _commuta_a_caldo usa self.system,
    # ma se la finestra non ce l'ha non fa niente. Ripiego sul system globale di KaraDom.
    try:
        import moduli.expander_gui as _eg
        F = getattr(_eg, 'FinestraExpander', None)
        if F is not None and hasattr(F, '_commuta_a_caldo') and not getattr(F, '_hotapply_104', False):
            _oc = F._commuta_a_caldo

            def _cc(self, *a, **k):
                if getattr(self, 'system', None) is None:
                    import sys as _sys
                    self.system = getattr(_sys.modules.get('__main__'), '_app_system', None)
                return _oc(self, *a, **k)

            F._commuta_a_caldo = _cc
            F._hotapply_104 = True
    except Exception as e:
        print('[EXP] 104 hot-apply:', e)

    print('[EXP] patch 104: expander in-process (BASSMIDI) attivo con expander_socket=1')
    return True


def revert():
    try:
        import sys
        mod = sys.modules.get('moduli.expander_midi')
        if mod is not None and getattr(mod, '_inproc_104', False):
            if hasattr(mod, '_UscitaMIDI_orig104'):
                mod._UscitaMIDI = mod._UscitaMIDI_orig104
            if hasattr(mod, '_detect_orig104'):
                mod.detect_expander = mod._detect_orig104
            del mod._inproc_104
    except Exception:
        pass


try:
    apply()
except Exception as _e:
    print('patch 104: %s' % _e)
