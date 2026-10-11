# 210 - verifica licenza una volta per sessione (15 min) e cestino della scaletta in sottofondo

_VER = 1
VALIDA_PER = 900          # un esito POSITIVO del server vale 15 minuti


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
        return str(Database.get_config('patch_210', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def _licenza(L):
    """All'avvio is_licensed() gira piu' volte (avvio, splash x2, Info, aggiornamenti) e ognuna
    aspettava il server fino a 8-12 s. Un esito POSITIVO vale 15 minuti; i 'no' e gli errori di
    rete non si ricordano: revoca/blocco funzionano come prima."""
    import time
    if getattr(L, '_ver210', None) == _VER or hasattr(L, '_verify_license_remote_server'):
        return
    vera = getattr(L, '_o210_verify', None) or L.verify_license_remote
    L._o210_verify = vera
    ricordo = {'chiave': None, 't': 0.0, 'esito': None}

    def verify_license_remote(nome, cognome, serial, license_key, timeout=12, *a, **k):
        chiave = (nome, cognome, serial, license_key)
        if ricordo['chiave'] == chiave and time.time() - ricordo['t'] < VALIDA_PER:
            return dict(ricordo['esito'])
        esito = vera(nome, cognome, serial, license_key, timeout, *a, **k)
        if isinstance(esito, dict) and esito.get('valid'):
            ricordo.update(chiave=chiave, t=time.time(), esito=dict(esito))
        else:
            ricordo.update(chiave=None, t=0.0, esito=None)
        return esito

    L.verify_license_remote = verify_license_remote
    L._ver210 = _VER


def _cestino(R):
    """'clear_all' (cestino della scaletta) partiva dal thread della finestra: fino a 12 s fermo.
    Se arriva dal thread principale, va in sottofondo."""
    import threading
    if getattr(R, '_ver210', None) == _VER:
        return
    vera = R.api_call

    def api_call(action, *a, **k):
        if action == 'clear_all' and threading.current_thread() is threading.main_thread():
            threading.Thread(target=lambda: vera(action, *a, **k), name='SvuotaRemoto', daemon=True).start()
            return {'ok': True, 'in_sfondo': True}
        return vera(action, *a, **k)

    R.api_call = api_call
    R._ver210 = _VER


def apply():
    if _spenta():
        return False
    try:
        from moduli import licensing as L
        _licenza(L)
    except Exception as e:
        print("[210] licenza: %s" % e)
    try:
        from moduli import requests_api_client as R
        _cestino(R)
    except Exception as e:
        print("[210] cestino: %s" % e)
    return True


def revert():
    return False


try:
    apply()
except Exception:
    pass
