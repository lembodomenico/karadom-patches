def _spia(msg):
    try:
        import os, time
        p = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'KaraDom', 'names150.log')
        with open(p, 'a', encoding='utf-8') as f:
            f.write(time.strftime('%H:%M:%S ') + str(msg) + '\n')
    except Exception:
        pass
    print('[NAMES150]', msg)


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_150', '1')) == '0'
    except Exception:
        return False


def _cfg(k, d=''):
    try:
        from moduli.database import Database
        v = Database.get_config(k, d)
        return v if v not in (None, '') else d
    except Exception:
        return d


def _set(k, v):
    try:
        from moduli.database import Database
        Database.set_config(k, str(v))
    except Exception:
        pass


def _forza_banco():
    """Carica il banco in BASS ORA (come fa il play). Diagnostica su log."""
    try:
        import moduli.expander_midi as EM
    except Exception as e:
        _spia('force banco: expander_midi assente: %s' % e); return
    _spia('config: sorgente=%r socket=%r banco=%r' % (
        _cfg('sorgente_scelta'), _cfg('expander_socket'), _cfg('exp_banco_path')))
    try:
        if hasattr(EM, 'get_expander_player'):
            pl = EM.get_expander_player()
            _spia('get_expander_player -> %s' % ('OK (banco in BASS)' if pl is not None else 'None (banco NON caricato)'))
    except Exception as e:
        _spia('get_expander_player errore: %s' % e)
    try:
        from moduli.bass_engine import get_bass_engine
        eng = get_bass_engine()
        _spia('motore: soundfont_path=%r exp_soft_active=%r' % (
            getattr(eng, 'soundfont_path', None), getattr(eng, '_exp_soft_active', None)))
    except Exception as e:
        _spia('stato motore: %s' % e)


def apply():
    if _spenta():
        return False
    try:
        import moduli.expander_gui as EG
    except Exception as e:
        _spia('expander_gui non pronto: %s' % e); return False

    F = getattr(EG, 'FinestraExpander', None)

    # 1) FIX RADICE del "due volte": salva sorgente_scelta PRIMA che
    #    _scegli_sorgente costruisca il player, cosi' get_expander_player (riga 396
    #    della 106) legge gia' la scelta NUOVA e carica il banco al primo colpo.
    if F is not None and hasattr(F, '_scegli_sorgente') and not getattr(F, '_presave150', False):
        _osc = F._scegli_sorgente

        def _scegli(self, *a, **k):
            try:
                solo_ui = k.get('_solo_ui', a[0] if a else False)
                if not solo_ui and hasattr(self, 'var_sorgente'):
                    _set('sorgente_scelta', self.var_sorgente.get())
            except Exception as e:
                _spia('presave scelta: %s' % e)
            return _osc(self, *a, **k)

        F._scegli_sorgente = _scegli
        F._presave150 = True
        _spia('presave sorgente_scelta agganciato')

    # 2) sull'Applica forzo comunque il caricamento (rinforzo) + diagnostica
    hooked = []
    for n in dir(EG):
        cls = getattr(EG, n)
        if not isinstance(cls, type):
            continue
        for meth in ('_ok_chiude', '_applica_ora'):
            flag = '_bnc150_' + meth
            if hasattr(cls, meth) and not getattr(cls, flag, False):
                _o = getattr(cls, meth)
                def _wrap(self, _o=_o):
                    r = _o(self)
                    try:
                        _forza_banco()
                    except Exception as e:
                        _spia('hook: %s' % e)
                    return r
                setattr(cls, meth, _wrap)
                setattr(cls, flag, True)
                hooked.append(n + '.' + meth)
    _spia('apply: agganci=%r' % hooked)
    return bool(hooked) or getattr(F, '_presave150', False)


def revert():
    pass


try:
    apply()
except Exception as _e:
    print('patch 150: %s' % _e)
