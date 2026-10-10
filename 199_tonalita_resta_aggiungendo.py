# 199 - aggiungendo un brano alla serata la tonalita' del brano in riproduzione resta

import tkinter as tk

_VER = 1


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_199', '1')) == '0'
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
        sy = getattr(self, 'system', None)
        if sy is not None and (getattr(sy, 'is_playing', False) or getattr(sy, 'is_paused', False)):
            return
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
        if C is None:
            return True
        if getattr(C, '_tonresta199', None) != _VER:
            C._azzera_ton = _azzera_ton
            C._tonresta199 = _VER
            print('[TONRESTA199] aggiungi con brano in riproduzione -> tonalita invariata')
    except Exception as e:
        print('[TONRESTA199] hook:', e)
    return True


def revert():
    pass


try:
    apply()
except Exception as _e:
    print('patch 199: %s' % _e)
