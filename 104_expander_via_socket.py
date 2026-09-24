# 104 - Expander software via SOCKET (niente loopMIDI): manda il MIDI a 127.0.0.1:8799
import socket
import threading


def _porta():
    try:
        from moduli.database import Database
        v = str(Database.get_config('expander_socket_port', '') or '').strip()
        return int(v) if v else 8799
    except Exception:
        return 8799


def _socket_on():
    try:
        from moduli.database import Database
        return str(Database.get_config('expander_socket', '0')) == '1'
    except Exception:
        return False


class _UscitaSocket(object):
    """Stessa interfaccia di _UscitaMIDI (apri/short/sysex/chiudi) ma manda i byte
    MIDI a un socket locale: l'expander li suona con BASSMIDI. Niente driver/porta."""

    def __init__(self, device_id, nome):
        self.device_id = device_id
        self.nome = nome or 'Expander software'
        self.aperta = False
        self._morta = False
        self._stream = None
        self._sock = None
        self._lock = threading.Lock()

    def apri(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2.0)
            s.connect(('127.0.0.1', _porta()))
            s.settimeout(None)
            self._sock = s
            self.aperta = True
            print('Expander socket: collegato a 127.0.0.1:%d' % _porta())
            return True
        except Exception as e:
            print('Expander socket: connessione fallita:', e)
            self.aperta = False
            return False

    def _send(self, payload):
        if not self.aperta or self._sock is None:
            return
        try:
            with self._lock:
                self._sock.sendall(payload)
        except Exception as e:
            self._morta = True
            self.aperta = False
            print('Expander socket: invio fallito:', e)

    def short(self, status, dato1=0, dato2=0, istante=None):
        hi = status & 0xF0
        if hi in (0xC0, 0xD0):            # program change / channel pressure = 2 byte
            self._send(bytes([status & 0xFF, dato1 & 0x7F]))
        else:                            # note/cc/pitch/aftertouch = 3 byte
            self._send(bytes([status & 0xFF, dato1 & 0x7F, dato2 & 0x7F]))

    def sysex(self, dati, istante=None):
        if dati:
            self._send(bytes(dati))

    def chiudi(self):
        self.aperta = False
        try:
            if self._sock:
                self._sock.close()
        except Exception:
            pass
        self._sock = None


def apply():
    import sys
    mod = sys.modules.get('moduli.expander_midi')
    if mod is None:
        try:
            import moduli.expander_midi as mod  # noqa
        except Exception:
            print('patch 104: expander_midi non presente (ok)')
            return False
    if getattr(mod, '_socket_out_104', False):
        return True
    orig = getattr(mod, '_UscitaMIDI', None)
    if orig is None:
        return True

    def _fabbrica(device_id, nome):
        # socket SOLO per la porta finta "Expander software" (id=-1). Un expander
        # HARDWARE (device_id vero) resta su winmm, esattamente come prima.
        if _socket_on() and (device_id == -1 or 'software' in (nome or '').lower()):
            return _UscitaSocket(device_id, nome)
        return orig(device_id, nome)

    mod._UscitaMIDI_orig104 = orig
    mod._UscitaMIDI = _fabbrica
    mod._socket_out_104 = True

    # col socket la PORTA MIDI non serve: se expander_socket=1, detect_expander
    # restituisce una porta finta cosi' il player si crea anche senza loopMIDI.
    if not getattr(mod, '_detect_socket_104', False) and hasattr(mod, 'detect_expander'):
        _od = mod.detect_expander

        def _detect(*a, **k):
            real = _od(*a, **k)
            if _socket_on():
                # ⭐ HARDWARE collegato -> precedenza (come prima): se il rilevamento
                #    trova un expander VERO (non loopMIDI), usa quello. Altrimenti socket.
                if real:
                    nome = (real.get('nome', '') or '').lower()
                    if 'loop' not in nome:
                        return real
                return {'nome': 'Expander software', 'id': -1, 'punteggio': 50}
            return real

        mod._detect_orig104 = _od
        mod.detect_expander = _detect
        mod._detect_socket_104 = True

    # etichetta mixer: mostra solo "Expander Software" (non "EXPANDER: Expander software").
    # Sta qui (numero nuovo, .prova non sovrascritto) e non nella 102 (pubblicata,
    # che il manifest riscarica vecchia a ogni riavvio).
    try:
        import moduli.mixer as _mx
        P = getattr(_mx, 'MIDIMixerPanel', None)
        if P is not None and hasattr(P, '_update_soundfont_display') and not getattr(P, '_lbl_socket_104', False):
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
            P._lbl_socket_104 = True
    except Exception as e:
        print('[EXP] 104 etichetta mixer:', e)

    print('[EXP] patch 104: uscita expander via socket disponibile (expander_socket=1)')
    return True


def revert():
    try:
        import sys
        mod = sys.modules.get('moduli.expander_midi')
        if mod is not None and getattr(mod, '_socket_out_104', False):
            if hasattr(mod, '_UscitaMIDI_orig104'):
                mod._UscitaMIDI = mod._UscitaMIDI_orig104
            del mod._socket_out_104
    except Exception:
        pass


try:
    apply()
except Exception as _e:
    print('patch 104: %s' % _e)
