def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_178', '1')) == '0'
    except Exception:
        return False


def _set(k, v):
    try:
        from moduli.database import Database
        Database.set_config(k, v)
    except Exception:
        pass


def apply():
    if _spenta():
        return False
    import sys
    eg = sys.modules.get('moduli.expander_gui')
    if eg is None:
        try:
            import moduli.expander_gui as eg  # noqa
        except Exception:
            return False
    F = getattr(eg, 'FinestraExpander', None)
    if F is None or not hasattr(F, '_scegli_sorgente') or getattr(F, '_mio178', False):
        return True
    _orig = F._scegli_sorgente

    def _scegli_sorgente(self, _solo_ui=False):
        # Il ramo 'software_mio' faceva return senza passare da _orig_scegli, l'unico
        # che scrive sorgente_scelta='software'. Il motore 109 parte solo con quel
        # flag, quindi il 'mio' diretto non si agganciava: andava solo DOPO essere
        # passati da "Expander Software". Imposto io il flag PRIMA, cosi' il 'mio'
        # diretto inizializza il motore come il software. Tocco solo 'software_mio':
        # il fisico non viene sfiorato.
        try:
            if not _solo_ui and str(self.var_sorgente.get()) == 'software_mio':
                _set('sorgente_scelta', 'software')
        except Exception as e:
            print('[EXP178]', e)
        return _orig(self, _solo_ui)

    F._scegli_sorgente = _scegli_sorgente
    F._mio178 = True
    print('[EXP178] mio diretto: sorgente_scelta=software prima di agganciare')
    return True


try:
    apply()
except Exception as _e:
    print('patch 178: %s' % _e)
