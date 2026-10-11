# 212 - campanella delle richieste: ogni 30 s chiede solo il NUMERO, non tutte le righe

_VER = 1


# [11-10-2026] estesa a TUTTI i PC (prima solo quelli del gestore)
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
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_212', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def apply():
    """La campanella (ui.check_remote_requests -> _db_check) ogni 30 s faceva api_call('load')
    e scaricava tutte le richieste solo per contarle. Il server ora ha l'azione 'count'.
    Si cambia SOLO la chiamata che arriva da _db_check: il pannello delle richieste (160)
    continua a ricevere le righe."""
    if _spenta():
        return False
    import sys
    try:
        from moduli import requests_api_client as R
    except Exception:
        return False
    if getattr(R, '_ver212', None) == _VER:
        return True
    vera = R.api_call
    senza_count = [False]                 # server vecchio che non conosce 'count': si torna a 'load'

    def api_call(action, *a, **k):
        if action == 'load' and not senza_count[0]:
            try:
                chi = sys._getframe(1).f_code.co_name
            except Exception:
                chi = ''
            if chi == '_db_check':
                r = vera('count', *a, **k)
                if isinstance(r, dict) and r.get('ok') and 'n' in r:
                    return {'ok': True, 'rows': [{}] * int(r.get('n') or 0)}
                if isinstance(r, dict) and r.get('error') not in ('not_enabled', None):
                    senza_count[0] = True
                return vera(action, *a, **k) if not (isinstance(r, dict) and r.get('error') == 'not_enabled') else r
        return vera(action, *a, **k)

    R.api_call = api_call
    R._ver212 = _VER
    print("[212] campanella: chiede solo il numero delle richieste")
    return True


def revert():
    return False


try:
    apply()
except Exception:
    pass
