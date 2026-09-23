# 097 - Expander: lo spegnimento note allo stop/cambio brano non blocca il programma se la porta MIDI e' intasata
def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_097', '1')) == '0'
    except Exception:
        return False


def apply():
    if _spenta():
        return False
    import sys, threading
    mod = sys.modules.get('moduli.fluidsynth_player')
    if mod is None:
        try:
            import moduli.fluidsynth_player as mod  # noqa
        except Exception:
            print('patch 097: modulo fluidsynth_player non presente (ok)')
            return False
    Cls = getattr(mod, 'FluidSynthPlayer', None)
    if Cls is None:
        print('patch 097: FluidSynthPlayer non trovato (ok)')
        return False
    if getattr(Cls, '_ano_097', False):
        return True

    _TIMEOUT = 2.0

    def _all_notes_off(self):
        # 1) svuota lo stream (gia' protetto dalla 095)
        try:
            uscita = getattr(self, "out", None)
            st = getattr(uscita, "_stream", None) if uscita is not None else None
            if st is not None:
                st.svuota()
            if getattr(self, "synth", None) is not None:
                self.synth.istante = None
        except Exception:
            pass
        # 2) All Notes Off DIRETTI col tetto di tempo: se la porta e' intasata
        #    (loopMIDI/expander), NON si aspetta e NON si blocca la UI.
        synth = getattr(self, "synth", None)
        if synth is None:
            return

        def _spegni():
            for ch in range(16):
                try:
                    synth.cc(ch, 123, 0)   # All Notes Off
                    synth.cc(ch, 120, 0)   # All Sound Off
                    synth.cc(ch, 64, 0)    # Sustain off
                except Exception:
                    pass
                try:
                    self.active_notes[ch] = 0
                except Exception:
                    pass

        t = threading.Thread(target=_spegni, name='allnotesoff_097', daemon=True)
        t.start()
        t.join(_TIMEOUT)
        if t.is_alive():
            # porta intasata: marco l'uscita come "morta" (gli invii diretti
            # successivi la saltano) e vado avanti. Alla prossima riproduzione
            # l'uscita viene ricreata.
            try:
                uscita = getattr(self, "out", None)
                if uscita is not None:
                    setattr(uscita, "_morta", True)
            except Exception:
                pass
            print("[EXP] patch 097: spegnimento note non risponde (>%.0fs, porta intasata): "
                  "abbandono e vado avanti (niente blocco)" % _TIMEOUT)

    Cls._all_notes_off_orig_097 = Cls._all_notes_off
    Cls._all_notes_off = _all_notes_off
    Cls._ano_097 = True
    print('[EXP] patch 097: All Notes Off col timeout (%.0fs), la UI non si blocca allo stop' % _TIMEOUT)
    return True


def revert():
    try:
        import sys
        mod = sys.modules.get('moduli.fluidsynth_player')
        Cls = getattr(mod, 'FluidSynthPlayer', None) if mod else None
        if Cls is not None and getattr(Cls, '_ano_097', False):
            if hasattr(Cls, '_all_notes_off_orig_097'):
                Cls._all_notes_off = Cls._all_notes_off_orig_097
            del Cls._ano_097
    except Exception:
        pass


try:
    apply()
except Exception as _e:
    print('patch 097: %s' % _e)
