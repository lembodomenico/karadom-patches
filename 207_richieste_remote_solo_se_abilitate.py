# 207 - licenza senza richieste remote: niente chiamate al server

_VER = 1
PAUSA_NON_ABILITATA = 1800          # dopo un "not_enabled" si riprova fra 30 minuti (una volta)


# PER ORA SOLO SUI PC DEL GESTORE (DOMMSI, DOMHP, KARADOM, KaraDomOS): sugli altri non fa niente
SOLO_SERIALI = ('1A55-2CD1-3303-20EB', '64D4-81C3-65D3-C024', '0182-5846-232C-930E', '4D8E-F63F-45E1-8F06')


def _pc_del_gestore():
    import sys
    gia = getattr(sys, '_kd_pc_del_gestore', None)
    if gia is None:
        try:
            from moduli.licensing import get_hardware_id, generate_serial
            c, m = get_hardware_id()
            gia = generate_serial(c, m) in SOLO_SERIALI
        except Exception:
            gia = False
        sys._kd_pc_del_gestore = gia
    return gia


def _spenta():
    if not _pc_del_gestore():
        return True
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_207', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def apply():
    if _spenta():
        return False
    import time
    try:
        from moduli import requests_api_client as R
    except Exception:
        return False
    if getattr(R, '_ver207', None) == _VER:
        return True
    if hasattr(R, 'richieste_abilitate'):
        R._ver207 = _VER                 # eseguibile nuovo: lo fa gia' da se'
        return True
    vera = getattr(R, '_o207_api_call', None) or R.api_call
    R._o207_api_call = vera
    fino = [0.0]

    def richieste_abilitate():
        # prima il tipo di licenza salvato in locale (lo stesso che decide la campanella)
        try:
            from moduli.licensing import richieste_abilitate as tipo_licenza
            if not tipo_licenza():
                return False
        except Exception:
            pass
        return time.time() >= fino[0]

    def segna_risposta(r):
        if isinstance(r, dict):
            if r.get('error') == 'not_enabled':
                if time.time() >= fino[0]:
                    print("[requests_api] richieste remote non abilitate: niente chiamate per %d min"
                          % (PAUSA_NON_ABILITATA // 60))
                fino[0] = time.time() + PAUSA_NON_ABILITATA
            elif r.get('ok'):
                fino[0] = 0.0

    def api_call(action, *a, **k):
        # licenza senza richieste remote: si risponde da soli, senza rete
        if not richieste_abilitate():
            return {'ok': False, 'error': 'not_enabled', 'senza_rete': True}
        r = vera(action, *a, **k)
        segna_risposta(r)
        return r

    R.api_call = api_call
    R.richieste_abilitate = richieste_abilitate
    R.segna_risposta = segna_risposta
    R._ver207 = _VER
    print("[207] richieste remote: niente chiamate se la licenza non le ha")
    return True


def revert():
    return False


try:
    apply()
except Exception:
    pass
