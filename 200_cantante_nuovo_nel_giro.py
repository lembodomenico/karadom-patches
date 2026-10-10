# 200 - un cantante nuovo entra nel giro in corso, sotto chi ha cantato per ultimo nel giro precedente

import sys
import types

_VER = 1
_SORGENTE = '# -*- coding: utf-8 -*-\n"""Giro della scaletta: un cantante NUOVO entra nel giro in corso.\n\nChi ha cantato va in fondo (🔄 / tasto G) e li\' resta, anche quando gli si mette\nun brano nuovo. Accodando il nuovo cantante all\'ultima riga finiva DOPO chi ha\ngia\' ricominciato il giro: aspettava un giro intero.\n\nOgni cantante ha il numero di volte che e\' andato in fondo. Il nuovo prende il\nnumero piu\' basso della scaletta (entra nel giro di quelli) e si mette subito\nsotto l\'ultimo di loro, cioe\' sotto chi ha cantato per ultimo nel giro precedente,\nsopra quelli che hanno gia\' ricominciato.\n\nEsempio: A B C D hanno cantato tutti una volta, A ricanta e va in fondo:\nB C D A -> arriva E -> B C D E A.\n\nIl conteggio resta salvato (config \'giri_scaletta\') e si azzera quando la\nscaletta si svuota.\n"""\nimport json\n\n_CHIAVE = \'giri_scaletta\'\n_VER = 1\n\n\ndef _nome(riga):\n    try:\n        n = riga[\'cantante\'].get().strip().upper()\n    except Exception:\n        return \'\'\n    return \'\' if n in (\'\', \'---\') else n\n\n\ndef _leggi():\n    try:\n        from moduli.database import Database\n        d = json.loads(Database.get_config(_CHIAVE, \'{}\') or \'{}\')\n        return d if isinstance(d, dict) else {}\n    except Exception:\n        return {}\n\n\ndef _scrivi(d):\n    try:\n        from moduli.database import Database\n        Database.set_config(_CHIAVE, json.dumps(d, ensure_ascii=False))\n    except Exception as e:\n        print(\'[GIRO] salvataggio: %s\' % e)\n\n\ndef conta(cantante):\n    """Il cantante e\' andato in fondo: ha finito il suo turno di questo giro."""\n    n = (cantante or \'\').strip().upper()\n    if not n or n == \'---\':\n        return\n    d = _leggi()\n    d[n] = int(d.get(n, 0)) + 1\n    _scrivi(d)\n\n\ndef colloca(lib, prima):\n    """L\'ultima riga e\' un cantante nuovo (la scaletta prima ne aveva `prima`):\n    la sposta sotto chi ha cantato per ultimo nel giro precedente."""\n    righe = lib.righe\n    if len(righe) != prima + 1:\n        return\n    nuovo = _nome(righe[-1])\n    if not nuovo:\n        return\n    d = _leggi()\n    altri = [_nome(r) for r in righe[:-1]]\n    if not any(altri):\n        if d:\n            _scrivi({nuovo: 0})          # scaletta vuota: sera nuova, si riparte da zero\n        return\n    giri = [int(d.get(n, 0)) for n in altri if n]\n    m = min(giri)\n    d[nuovo] = m\n    _scrivi(d)\n    i = len(altri)\n    while i > 0 and altri[i - 1] and int(d.get(altri[i - 1], 0)) > m:\n        i -= 1\n    if i == len(altri):\n        return                           # nessuno ha ricominciato il giro: resta in fondo\n    righe.insert(i, righe.pop())\n    print(\'[GIRO] %s messo al posto %d (giro %d, sotto %s)\' % (nuovo, i + 1, m, altri[i - 1] if i else \'-\'))\n    try:\n        lib.riordina_righe()\n    except Exception as e:\n        print(\'[GIRO] ridisegno: %s\' % e)\n    try:\n        lib._salva_e_riordina_remoto()\n    except Exception as e:\n        print(\'[GIRO] salvataggio scaletta: %s\' % e)\n\n\ndef installa(C):\n    """Aggancia crea_riga e sposta_in_fondo della libreria (una volta per versione)."""\n    if C is None or getattr(C, \'_giro_ver\', None) == _VER:\n        return\n    o_crea = getattr(C, \'_giro_o_crea_riga\', None) or C.crea_riga\n    o_fondo = getattr(C, \'_giro_o_sposta_in_fondo\', None) or C.sposta_in_fondo\n    C._giro_o_crea_riga, C._giro_o_sposta_in_fondo = o_crea, o_fondo\n\n    def crea_riga(self, cantante, brano, tonalita, path, from_playlist=False, salta_dedup=False):\n        prima = len(getattr(self, \'righe\', []) or [])\n        r = o_crea(self, cantante, brano, tonalita, path, from_playlist, salta_dedup)\n        if not from_playlist and not getattr(self, \'_batch_loading\', False):\n            try:\n                colloca(self, prima)\n            except Exception as e:\n                print(\'[GIRO] %s\' % e)\n        return r\n\n    def sposta_in_fondo(self, frame):\n        chi = \'\'\n        try:\n            for riga in self.righe:\n                if riga[\'frame\'] == frame:\n                    chi = _nome(riga)\n                    break\n        except Exception:\n            pass\n        r = o_fondo(self, frame)\n        try:\n            conta(chi)\n        except Exception as e:\n            print(\'[GIRO] %s\' % e)\n        return r\n\n    C.crea_riga = crea_riga\n    C.sposta_in_fondo = sposta_in_fondo\n    C._giro_ver = _VER\n'


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_200', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def _modulo():
    try:
        import importlib
        vero = importlib.import_module('moduli.giro_scaletta')
        if getattr(vero, '__file__', '') != '<patch200>' and hasattr(vero, 'installa'):
            return vero
    except Exception:
        pass
    m = sys.modules.get('moduli.giro_scaletta')
    if m is not None and getattr(m, '_ver200', None) == _VER:
        return m
    m = types.ModuleType('moduli.giro_scaletta')
    m.__file__ = '<patch200>'
    exec(compile(_SORGENTE, 'giro_scaletta_200', 'exec'), m.__dict__)
    m._ver200 = _VER
    sys.modules['moduli.giro_scaletta'] = m
    try:
        import moduli
        moduli.giro_scaletta = m
    except Exception:
        pass
    return m


def apply():
    if _spenta():
        return False
    try:
        m = _modulo()
        import moduli.libreria as lib
        m.installa(getattr(lib, 'LibreriaSlider', None))
        print('[GIRO200] cantante nuovo nel giro in corso')
    except Exception as e:
        print('[GIRO200] hook:', e)
    return True


def revert():
    pass


try:
    apply()
except Exception as _e:
    print('patch 200: %s' % _e)
