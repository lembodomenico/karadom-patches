# 095 - Expander: fermare, cambiare brano o rilevare la porta non blocca piu' il programma se il driver MIDI non risponde
def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_095', '1')) == '0'
    except Exception:
        return False


def apply():
    if _spenta():
        return False
    import sys, threading, ctypes
    mod = sys.modules.get('moduli.midi_stream')
    if mod is None:
        try:
            import moduli.midi_stream as mod  # noqa
        except Exception:
            print('patch 095: modulo midi_stream non presente (ok)')
            return False
    Us = getattr(mod, 'UscitaStream', None)
    if Us is None:
        print('patch 095: UscitaStream non trovata (ok)')
        return False
    if getattr(Us, '_stop_095', False):
        return True

    _attesa = float(getattr(mod, 'ATTESA_DRIVER', 3.0))

    def _pulisci_driver(self):
        # TUTTE le chiamate al driver (stop + libera gli header) in UN filo a parte
        # col tetto di tempo: se il driver (loopMIDI/expander) e' incastrato,
        # midiStreamStop O midiOutUnprepareHeader restano appesi -> qui NON aspettiamo.
        mm, h = getattr(self, '_mm', None), getattr(self, '_h', None)
        if mm is None or h is None:
            return True

        def _lavora():
            try:
                mm.midiStreamStop(h)
            except Exception:
                pass
            try:
                with self._lock:
                    for hdr, _c in list(getattr(self, '_blocchi', [])):
                        try:
                            mm.midiOutUnprepareHeader(h, ctypes.byref(hdr), ctypes.sizeof(hdr))
                        except Exception:
                            pass
                    self._blocchi = []
            except Exception:
                pass

        t = threading.Thread(target=_lavora, name='exp_stop_095', daemon=True)
        t.start()
        t.join(_attesa)
        if t.is_alive():
            # driver piantato: ABBANDONO l'handle (non lo tocco piu') e vado avanti.
            # Meglio una porta lasciata aperta che un programma che si blocca.
            print("[EXP] patch 095: il driver MIDI non risponde da %.0fs: abbandono la "
                  "porta e vado avanti (niente blocco)" % _attesa)
            try:
                self._blocchi = []
            except Exception:
                pass
            self.aperta = False
            return False
        return True

    _svuota_orig = Us.svuota
    _ferma_orig = Us.ferma

    def svuota(self):
        if not getattr(self, 'aperta', False):
            return
        _pulisci_driver(self)
        self._quando_ms = None
        self._riparti = True

    def ferma(self):
        if not getattr(self, 'aperta', False):
            return
        _pulisci_driver(self)

    Us.svuota = svuota
    Us.ferma = ferma
    Us._svuota_orig_095 = _svuota_orig
    Us._ferma_orig_095 = _ferma_orig
    Us._stop_095 = True
    print('[EXP] patch 095: stop/svuota/rileva col timeout (%.0fs) su TUTTA la pulizia, la UI non si blocca' % _attesa)
    return True


def revert():
    try:
        import sys
        mod = sys.modules.get('moduli.midi_stream')
        Us = getattr(mod, 'UscitaStream', None) if mod else None
        if Us is not None and getattr(Us, '_stop_095', False):
            if hasattr(Us, '_svuota_orig_095'):
                Us.svuota = Us._svuota_orig_095
            if hasattr(Us, '_ferma_orig_095'):
                Us.ferma = Us._ferma_orig_095
            del Us._stop_095
    except Exception:
        pass


try:
    apply()
except Exception as _e:
    print('patch 095: %s' % _e)
