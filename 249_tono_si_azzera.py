# 249 - tono si azzera

import threading

_VER = 1

# [25-10-2026] Utente: "quando un brano finisce o viene stoppato o con fade out la tonalita' deve resettarsi".
# Prima il campo "Ton:" restava com'era e il brano dopo partiva con lo stesso tono (pitch_var letto al play).
# Ora alla fine naturale, allo STOP e al FADE OUT: tono di KaraDom a 0 e campo "Ton:" a "0".
# Non quando e' KaraDom stesso a fermare il brano per caricarne un altro (stop quick dentro load_file):
# li' il tono del brano nuovo e' gia' scelto e si imposta subito dopo.


def _titolare():
    try:
        from moduli.licensing import load_license
        d = load_license() or {}
        return (str(d.get('nome', '')).strip().lower(),
                str(d.get('cognome', '')).strip().lower()) == ('domenico', 'lembo')
    except Exception:
        return False


def _log(msg):
    try:
        print('[249] %s' % msg)
    except Exception:
        pass


_dentro_load = threading.local()


def _azzera(sistema, perche):
    try:
        if getattr(_dentro_load, 'si', False):
            return
        sistema.current_pitch = 0
    except Exception:
        return

    def ui():
        try:
            lib = getattr(sistema, 'libreria', None)
            pv = getattr(lib, 'pitch_var', None)
            if pv is not None and pv.get() != 0:
                pv.set(0)
                _log('tono azzerato (%s)' % perche)
            ref = getattr(lib, 'pitch_label_ref', None)
            if ref and ref.get('label'):
                ref['label'].config(text="0")
        except Exception as e:
            _log('campo Ton non azzerato: %s' % e)
    root = getattr(sistema, 'root', None) or getattr(sistema, '_root', None)
    try:
        if root is not None:
            root.after(0, ui)          # i bottoni si toccano solo dal filo della grafica
    except Exception:
        pass


def apply():
    if not _titolare():
        return False
    try:
        from moduli.database import Database
        if str(Database.get_config('patch_249', '1')).strip() in ('0', 'no', 'off'):
            return False
    except Exception:
        pass
    try:
        import moduli.system as ms
    except Exception as e:
        _log('system non trovato: %s' % e)
        return False
    S = ms.KaraokeMonitorSystem
    if getattr(S, '_ver249', None) == _VER:
        return True

    load0 = getattr(S, '_o249_load', None) or S.load_file
    stop0 = getattr(S, '_o249_stop', None) or S.stop
    fade0 = getattr(S, '_o249_fade', None) or S.fade_out
    fine0 = getattr(S, '_o249_fine', None) or getattr(S, '_voce_fine_brano', None)
    S._o249_load, S._o249_stop, S._o249_fade, S._o249_fine = load0, stop0, fade0, fine0

    def load_file(self, *a, **k):
        _dentro_load.si = True
        try:
            return load0(self, *a, **k)
        finally:
            _dentro_load.si = False

    def stop(self, *a, **k):
        r = stop0(self, *a, **k)
        _azzera(self, 'stop')
        return r

    def fade_out(self, *a, **k):
        r = fade0(self, *a, **k)
        _azzera(self, 'fade out')
        return r

    def fine_brano(self, *a, **k):
        r = fine0(self, *a, **k)
        _azzera(self, 'fine brano')
        return r

    S.load_file = load_file
    S.stop = stop
    S.fade_out = fade_out
    if fine0 is not None:
        S._voce_fine_brano = fine_brano
    S._ver249 = _VER
    _log('tono a 0 a fine brano, stop e fade out')
    return True


def revert():
    return False
