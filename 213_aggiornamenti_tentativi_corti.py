# 213 - aggiornamenti e stato dispositivo: niente secondo tentativo SSL dopo un errore di rete

_VER = 1
# Funzioni copiate dal sorgente moduli/updater.py (identiche, piu' la correzione):
# dopo un tempo scaduto/connessione rifiutata non si riprova con l'altro contesto SSL (serve solo
# se l'errore e' di certificato) e il controllo aggiornamenti aspetta 10 s invece di 20.
# Caso peggiore: aggiornamenti da 80 a 20 s, stato dispositivo (prova) da 32 a 16 s.
CODICE = 'def _errore_certificato(e) -> bool:\n    """True se l\'errore riguarda il CERTIFICATO (allora ha senso provare l\'altro contesto SSL).\n    Un tempo scaduto o una connessione rifiutata non c\'entrano col certificato: riprovare con\n    l\'altro contesto raddoppiava solo l\'attesa sulle linee lente. [11-10-2026]"""\n    import ssl\n    rag = getattr(e, \'reason\', e)\n    return isinstance(rag, (ssl.SSLCertVerificationError,)) or \'CERTIFICATE_VERIFY_FAILED\' in str(e)\n\n\ndef check_for_updates(current_version=None):\n    """\n    Controlla se esiste una versione più recente.\n    Ritorna: (has_update, new_version, download_url, debug_info)\n    """\n    if current_version is None:\n        current_version = CURRENT_VERSION\n\n    debug_lines = [f"Versione locale: {current_version}"]\n    data = None\n    last_err = None\n\n    # Seriale hardware del PC (best-effort) per registrazione dispositivo.\n    # Se non disponibile si procede comunque: il server tratta la richiesta\n    # come "legacy" e risponde solo version/download_url.\n    _serial = ""\n    try:\n        from .licensing import get_hardware_id, generate_serial\n        _cpu, _mb = get_hardware_id()\n        if _cpu and _mb:\n            _serial = generate_serial(_cpu, _mb)\n    except Exception as _e:\n        debug_lines.append(f"serial non disponibile: {_e}")\n\n    # Costruisci 3 contesti SSL in ordine: certifi → sistema → senza verifica\n    contexts = []\n    if _CERTIFI_CA:\n        try:\n            c = _ssl_mod.create_default_context(cafile=_CERTIFI_CA)\n            contexts.append(("certifi", c))\n        except Exception as e:\n            debug_lines.append(f"certifi non utilizzabile: {e}")\n    try:\n        contexts.append(("system", _ssl_mod.create_default_context()))\n    except Exception as e:\n        debug_lines.append(f"system SSL non utilizzabile: {e}")\n    # NIENTE fallback CERT_NONE: un canale TLS non verificato consente il MITM.\n    # Se la verifica fallisce, l\'update non procede (fail sicuro) -> niente installer\n    # malevolo eseguito. (Resta certifi+system, entrambi verificati.)\n    if not contexts:\n        contexts.append(("none", None))\n\n    debug_lines.append(f"SSL contexts disponibili: {[n for n, _ in contexts]}")\n\n    for version_url in VERSION_CHECK_URLS:\n        for ctx_name, ssl_ctx in contexts:\n            try:\n                _sep = \'&\' if \'?\' in version_url else \'?\'\n                _url = f"{version_url}{_sep}v={current_version}"\n                if _serial:\n                    _url += f"&serial={_serial}"\n                req = urllib.request.Request(\n                    _url,\n                    headers={\n                        \'User-Agent\': f\'KaraDom Pro Updater/{current_version}\',\n                        \'Accept\': \'application/json\',\n                        \'Cache-Control\': \'no-cache\',\n                    }\n                )\n                kwargs = {\'timeout\': 10}\n                if ssl_ctx is not None:\n                    kwargs[\'context\'] = ssl_ctx\n                with urllib.request.urlopen(req, **kwargs) as response:\n                    raw = response.read().decode(\'utf-8\', errors=\'replace\')\n                    debug_lines.append(f"OK {version_url} [{ctx_name}] HTTP {response.status}")\n                    debug_lines.append(f"Risposta: {raw[:200]}")\n                    data = json.loads(raw)\n                    # Memorizza lo stato registrazione dispositivo (se presente)\n                    global LAST_REGISTRATION\n                    LAST_REGISTRATION = {\n                        "registered":   bool(data.get("registered", True)),\n                        "action":       str(data.get("action", "none")),\n                        "register_url": str(data.get("register_url", "")),\n                        "days_used":    int(data.get("days_used", 0) or 0),\n                        "message":      str(data.get("message", "")),\n                    }\n                    break\n            except Exception as e:\n                last_err = e\n                debug_lines.append(f"FAIL {version_url} [{ctx_name}]: {type(e).__name__}: {e}")\n                if not _errore_certificato(e):\n                    break           # errore di rete: l\'altro contesto SSL non serve, prossimo indirizzo\n                continue\n        if data:\n            break\n\n    if not data:\n        debug_info = "\\n".join(debug_lines)\n        print(f"❌ Controllo aggiornamenti fallito:\\n{debug_info}")\n        return False, None, None, debug_info\n\n    remote_version = str(data.get(\'version\', \'0.0\')).strip()\n    download_url = str(data.get(\'download_url\', \'\')).strip()\n    current_tuple = parse_version(current_version)\n    remote_tuple = parse_version(remote_version)\n\n    debug_lines.append(f"Locale={current_tuple}  Remota={remote_tuple}")\n    debug_lines.append(f"download_url=\'{download_url}\'")\n    debug_info = "\\n".join(debug_lines)\n    print(debug_info)\n\n    if remote_tuple > current_tuple and download_url:\n        return True, remote_version, download_url, debug_info\n    return False, remote_version, download_url, debug_info\n\n\ndef check_device_status(serial="", app_version=None, timeout=8):\n    """Interroga version.php per lo STATO del dispositivo (registered/action/message).\n    Serve a far valere il BLOCCO server-side (devices.blocked / trial_scadenza /\n    licenza revocata|scaduta) ANCHE all\'ingresso in TRIAL, non solo dopo l\'avvio.\n\n    Ritorna un dict {registered, action, message, register_url} oppure None se\n    offline/errore (il chiamante applica la GRAZIA: non blocca chi non ha rete).\n    """\n    if not _is_online():\n        return None\n    import urllib.request, ssl as _ssl_mod\n    av = app_version or CURRENT_VERSION\n    if not serial:\n        try:\n            from .licensing import get_hardware_id, generate_serial\n            _cpu, _mb = get_hardware_id()\n            serial = generate_serial(_cpu, _mb)\n        except Exception:\n            serial = ""\n    contexts = []\n    if _CERTIFI_CA:\n        try:\n            contexts.append(_ssl_mod.create_default_context(cafile=_CERTIFI_CA))\n        except Exception:\n            pass\n    try:\n        contexts.append(_ssl_mod.create_default_context())\n    except Exception:\n        pass\n    if not contexts:\n        contexts = [None]\n    for base in VERSION_CHECK_URLS:\n        sep = \'&\' if \'?\' in base else \'?\'\n        url = f"{base}{sep}v={av}"\n        if serial:\n            url += f"&serial={serial}"\n        for ctx in contexts:\n            try:\n                req = urllib.request.Request(url, headers={\n                    \'User-Agent\': f\'KaraDom Pro/{av}\',\n                    \'Accept\': \'application/json\', \'Cache-Control\': \'no-cache\'})\n                kwargs = {\'timeout\': timeout}\n                if ctx is not None:\n                    kwargs[\'context\'] = ctx\n                with urllib.request.urlopen(req, **kwargs) as r:\n                    data = json.loads(r.read().decode(\'utf-8\', \'replace\'))\n                return {\n                    "registered":   bool(data.get("registered", True)),\n                    "action":       str(data.get("action", "none")),\n                    "message":      str(data.get("message", "")),\n                    "register_url": str(data.get("register_url", "")),\n                }\n            except Exception as e:\n                if not _errore_certificato(e):\n                    break           # errore di rete: l\'altro contesto SSL non serve, prossimo indirizzo\n                continue\n    return None\n'


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
        return str(Database.get_config('patch_213', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def apply():
    if _spenta():
        return False
    try:
        import moduli.updater as up
    except Exception:
        return False
    if getattr(up, '_ver213', None) == _VER or hasattr(up, '_errore_certificato'):
        up._ver213 = _VER
        return True
    exec(compile(CODICE, '<patch213>', 'exec'), up.__dict__)
    up._ver213 = _VER
    print("[213] aggiornamenti: niente secondo tentativo SSL dopo un errore di rete")
    return True


def revert():
    return False


try:
    apply()
except Exception:
    pass
