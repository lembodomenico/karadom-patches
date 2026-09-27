import tkinter as tk


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_143', '1')) == '0'
    except Exception:
        return False


def _azzera_ton(self):
    try:
        self.entry_ton.delete(0, tk.END)
        self.entry_ton.insert(0, "0")
        self.entry_ton.config(fg='white')
    except Exception:
        pass
    try:
        if getattr(self, 'pitch_var', None) is not None:
            self.pitch_var.set(0)
        if getattr(self, 'pitch_label_ref', None) and self.pitch_label_ref.get('label'):
            self.pitch_label_ref['label'].config(text="0")
        if hasattr(self, 'system') and hasattr(self.system, 'set_pitch'):
            self.system.set_pitch(0)
    except Exception:
        pass


def apply():
    if _spenta():
        return False
    try:
        import moduli.libreria as lib
        C = getattr(lib, 'LibreriaSlider', None)
        if C is None or getattr(C, '_azzeratp143', False):
            return True
        C._azzera_ton = _azzera_ton
        _orig = C.crea_riga

        def _wrap(self, cantante, brano, tonalita, path, from_playlist=False, salta_dedup=False):
            r = _orig(self, cantante, brano, tonalita, path, from_playlist, salta_dedup)
            try:
                # brano eseguito/aggiunto dal campo ricerca/filtro: la tonalita'
                # passata e' quella del campo ton -> mando quella al brano e azzero
                # sia il ton del filtro sia il pitch in basso. La playlist e' esclusa.
                if not from_playlist:
                    cur = str(self.entry_ton.get()).strip()
                    if cur == str(tonalita).strip():
                        self._azzera_ton()
            except Exception:
                pass
            return r

        C.crea_riga = _wrap
        C._azzeratp143 = True
        print('[AZZERATP143] esegui da ricerca -> azzera ton + pitch in basso')
    except Exception as e:
        print('[AZZERATP143] hook:', e)
    return True


def revert():
    pass


try:
    apply()
except Exception as _e:
    print('patch 143: %s' % _e)
