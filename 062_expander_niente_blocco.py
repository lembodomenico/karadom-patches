# 062 - Expander: le porte MIDI si cercano UNA volta sola (non a ogni brano) e senza bloccare il programma
def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_062', '1')) == '0'
    except Exception:
        return False


def apply():
    if _spenta():
        return False
    import sys
    mod = sys.modules.get('moduli.expander_midi')
    if mod is None:
        try:
            import moduli.expander_midi as mod  # noqa
        except Exception:
            print('patch 062: modulo expander non presente (ok)')
            return False
    if getattr(mod, '_backend_list_062', False):
        return True
    import threading

    _orig = getattr(mod, '_backend_list', None)
    if _orig is None:
        return False

    _cache = {'done': False, 'val': []}
    _TIMEOUT = 3.0   # tetto sull'UNICA scansione: oltre, ripiega sul SoundFont interno

    def _safe_backend_list():
        # gia' rilevate in questa sessione: restituisco la cache, NIENTE riscansione
        if _cache['done']:
            return _cache['val']
        box = {'v': None, 'ok': False}

        def _worker():
            try:
                box['v'] = _orig()
            except Exception:
                box['v'] = []
            box['ok'] = True

        t = threading.Thread(target=_worker, name='exp_ports_062', daemon=True)
        t.start()
        t.join(_TIMEOUT)
        if box['ok']:
            _cache['val'] = box['v'] if box['v'] is not None else []
            _cache['done'] = True
        else:
            # enumerazione MIDI impiantata (driver che non risponde): NON aspetto e
            # NON blocco l'UI. Uso il SoundFont interno; il thread e' daemon.
            print('[EXP] porte MIDI non rispondono (>%.0fs): uso il SoundFont interno' % _TIMEOUT)
            _cache['val'] = []
            _cache['done'] = True   # non ritento a ogni brano: si rileva una volta sola
        return _cache['val']

    def _rileva_porte_forza():
        # per un eventuale bottone "rileva expander": azzera la cache e riscansiona una volta
        _cache['done'] = False
        return _safe_backend_list()

    _safe_backend_list._orig_062 = _orig
    mod._backend_list = _safe_backend_list
    mod.rileva_porte_forza = _rileva_porte_forza
    mod._backend_list_062 = True
    print('[EXP] patch 062: porte MIDI cercate UNA volta (timeout %.0fs), niente riscansione a ogni brano' % _TIMEOUT)
    return True


def revert():
    try:
        import sys
        mod = sys.modules.get('moduli.expander_midi')
        if mod is not None:
            o = getattr(getattr(mod, '_backend_list', None), '_orig_062', None)
            if o is not None:
                mod._backend_list = o
            if hasattr(mod, '_backend_list_062'):
                del mod._backend_list_062
    except Exception:
        pass


try:
    apply()
except Exception as _e:
    print('patch 062: %s' % _e)
