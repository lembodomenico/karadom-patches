# 221 - rilevazione mixer USB leggera

import threading
import time

_VER = 1


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_221', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def _installa(aw):
    vecchia = getattr(aw, '_usb_pnp_blob_221_orig', None) or aw._usb_pnp_blob
    stato = {'chiave': None, 'blob': '', 't': 0.0, 'errore': False}
    blocco = threading.Lock()

    def _usb_pnp_blob(max_age=15.0):
        try:
            chiave = tuple(aw._waveout_names())
        except Exception:
            chiave = None
        if stato['chiave'] == chiave and stato['t']:
            return stato['blob']
        if not blocco.acquire(blocking=False):
            return stato['blob']
        try:
            aw._pnp_cache['blob'] = None
            blob = vecchia(max_age) or ''
            stato.update(chiave=chiave, blob=blob, t=time.time(), errore=not blob)
            return blob
        finally:
            blocco.release()

    aw._usb_pnp_blob_221_orig = vecchia
    aw._usb_pnp_blob = _usb_pnp_blob
    aw._ver221 = _VER


def apply():
    if _spenta():
        return False
    try:
        import moduli.audio_windows as aw
    except Exception:
        return False
    if not hasattr(aw, '_usb_pnp_blob') or not hasattr(aw, '_waveout_names'):
        return False
    if getattr(aw, '_ver221', None) == _VER:
        return True
    _installa(aw)
    print("[221] mixer USB: PowerShell solo quando cambiano i dispositivi audio")
    return True


def revert():
    return False


try:
    apply()
except Exception:
    pass
