def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_144', '1')) == '0'
    except Exception:
        return False


def apply():
    if _spenta():
        return False
    try:
        import moduli.libreria as lib
        C = getattr(lib, 'LibreriaSlider', None)
        if C is None or getattr(C, '_ytpitch144', False):
            return True
        _orig = C.play_brano

        def _wrap(self, path, entry_ton=None, cantante="", brano="", tonalita=None, *a, **k):
            r = _orig(self, path, entry_ton, cantante, brano, tonalita, *a, **k)
            try:
                # tonalita' della riga (come la risolve play_brano)
                if tonalita is not None:
                    ton = int(tonalita)
                elif entry_ton is not None:
                    try:
                        ton = int((entry_ton.get() or "0").strip() or "0")
                    except Exception:
                        ton = 0
                else:
                    ton = None  # non specificata: non toccare il pitch corrente
                if ton is not None:
                    # il pitch in basso diventa la tonalita' della riga, ANCHE 0
                    # (col link YouTube il ramo originale lo saltava se 0)
                    if getattr(self, 'pitch_var', None) is not None:
                        self.pitch_var.set(ton)
                    if getattr(self, 'pitch_label_ref', None) and self.pitch_label_ref.get('label'):
                        self.pitch_label_ref['label'].config(text=("0" if ton == 0 else "%+d" % ton))
                    try:
                        self.system.current_pitch = ton
                    except Exception:
                        pass
                    try:
                        self.system.set_pitch(ton)
                    except Exception:
                        pass
            except Exception as e:
                print('[YTPITCH144]', e)
            return r

        C.play_brano = _wrap
        C._ytpitch144 = True
        print('[YTPITCH144] play -> pitch in basso = tonalita della riga (anche YouTube/0)')
    except Exception as e:
        print('[YTPITCH144] hook:', e)
    return True


def revert():
    pass


try:
    apply()
except Exception as _e:
    print('patch 144: %s' % _e)
