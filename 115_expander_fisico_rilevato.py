def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_115', '1')) == '0'
    except Exception:
        return False


def apply():
    if _spenta():
        return False
    import sys, threading, time
    mod = sys.modules.get('moduli.expander_midi')
    if mod is None:
        try:
            import moduli.expander_midi as mod  # noqa
        except Exception:
            print('patch 115: expander non presente (ok)')
            return False
    if getattr(mod, '_backend_list_115', False):
        return True

    cur = getattr(mod, '_backend_list', None)
    if cur is None:
        return False
    # vero backend winmm: se la 062 ha gia' avvolto, prendo l'originale sotto
    orig = getattr(cur, '_orig_062', None) or cur

    def _porta_hw(nome):
        # e' un expander HARDWARE? (non il synth software di Windows, non loopMIDI)
        try:
            return mod._punteggio(nome) > 0
        except Exception:
            n = (nome or '').lower()
            return not ('wavetable' in n or 'microsoft' in n or 'loop' in n or n.strip() == '')

    def _ha_hw(val):
        return any(_porta_hw(nome) for _idx, nome in (val or []))

    _st = {'val': [], 'ts': 0.0, 'stabile': False}
    _TIMEOUT = 3.0
    _MIN_INTERVALLO = 4.0   # tra due riscansioni: winmm normale = ms, non martello

    def _scan_una_volta():
        box = {'v': None, 'ok': False}

        def _w():
            try:
                box['v'] = orig()
            except Exception:
                box['v'] = []
            box['ok'] = True

        t = threading.Thread(target=_w, name='exp_ports_115', daemon=True)
        t.start()
        t.join(_TIMEOUT)
        if box['ok']:
            return box['v'] if box['v'] is not None else []
        print('[EXP] porte MIDI non rispondono (>%.0fs): riprovo piu\' tardi' % _TIMEOUT)
        return None

    def _smart_backend_list():
        # trovato una volta un expander HW: elenco stabile, niente altre scansioni
        if _st['stabile']:
            return _st['val']
        now = time.monotonic()
        if _st['ts'] and (now - _st['ts']) < _MIN_INTERVALLO:
            return _st['val']       # appena scansionato: non ri-martello winmm
        val = _scan_una_volta()
        _st['ts'] = time.monotonic()
        if val is not None:
            _st['val'] = val
            if _ha_hw(val):
                _st['stabile'] = True
                nomi = ', '.join(n for _i, n in val if _porta_hw(n))
                print('[EXP] 115: expander HARDWARE rilevato -> %s (elenco bloccato)' % nomi)
        return _st['val']

    def _rileva_porte_forza():
        _st['stabile'] = False
        _st['ts'] = 0.0
        return _smart_backend_list()

    _smart_backend_list._orig_062 = orig
    mod._backend_list = _smart_backend_list
    mod.rileva_porte_forza = _rileva_porte_forza
    mod._backend_list_115 = True
    print('[EXP] patch 115: l\'expander fisico viene ricercato anche dopo l\'avvio '
          '(riscansione ogni %.0fs finche\' non compare, poi stop)' % _MIN_INTERVALLO)
    return True


def revert():
    try:
        import sys
        mod = sys.modules.get('moduli.expander_midi')
        if mod is not None and getattr(mod, '_backend_list_115', False):
            o = getattr(getattr(mod, '_backend_list', None), '_orig_062', None)
            if o is not None:
                mod._backend_list = o
            del mod._backend_list_115
    except Exception:
        pass


try:
    apply()
except Exception as _e:
    print('patch 115: %s' % _e)
