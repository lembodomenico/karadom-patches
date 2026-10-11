# 214 - preferiti e playlist: niente rete senza richieste remote, invio solo se cambiati (= 091 v2)
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
        return str(Database.get_config('patch_214', '1')) == '0'
    except Exception:
        return False


def apply():
    if _spenta():
        return False
    try:
        from moduli.database import Database
    except Exception:
        return False
    # sui PC del gestore la 214 prende il posto della 091: la 091 si spegne (vale dal prossimo avvio;
    # se in questo avvio la 091 ha gia' agganciato, per questa volta resta lei)
    try:
        if str(Database.get_config('patch_091', '1')) != '0':
            Database.set_config('patch_091', '0')
            print("[214] la 091 si spegne su questo PC: dal prossimo avvio sincronizza la 214")
    except Exception:
        pass
    if getattr(Database, '_syncliste091', False):
        return True
    import hashlib
    import json
    import threading
    import urllib.request

    URL_DEFAULT = "https://iocanto.karadom.it/api/sync_api.php"
    _lock = threading.Lock()
    # v2 (11-10-2026): 'inviato' = impronta dell'ultimo contenuto mandato o scaricato: uguale = niente rete
    _st = {'timer': None, 'applica': False, 'inviato': None}

    def _url():
        try:
            u = (Database.get_config('sync_api_url', '') or '').strip()
        except Exception:
            u = ''
        return u or URL_DEFAULT

    def _attiva():
        try:
            if str(Database.get_config('sync_liste_attiva', '1')) == '0':
                return False
        except Exception:
            pass
        # v2: licenza senza richieste remote = niente rete (il server direbbe solo not_enabled)
        try:
            from moduli.licensing import richieste_abilitate
            if not richieste_abilitate():
                return False
        except Exception:
            pass
        return True

    def _impronta(pref_json, pl_json):
        return hashlib.sha1(((pref_json or '') + '|' + (pl_json or '')).encode('utf-8')).hexdigest()

    def _cred():
        try:
            from moduli.requests_api_client import _credenziali_licenza
            return _credenziali_licenza()
        except Exception:
            return '', '', '', ''

    def racc_pref():
        try:
            return Database.get_preferiti() or []
        except Exception:
            return []

    def racc_pl():
        liste = []
        try:
            for pl in (Database.get_playlist_standalone_list() or []):
                pid = pl.get('id')
                brani = []
                for b in (Database.get_playlist_standalone_brani(pid) or []):
                    brani.append({'artista': b.get('artista') or '',
                                  'titolo': b.get('titolo') or '',
                                  'path': b.get('path') or '',
                                  'ext': b.get('ext') or '',
                                  'tonalita': b.get('tonalita') or '0',
                                  'ordine': b.get('ordine') or 0})
                liste.append({'nome': pl.get('nome') or '', 'brani': brani})
        except Exception as e:
            print(f"[sync liste] pl: {e}")
        return liste

    def _invia():
        if not _attiva():
            return
        nome, cognome, serial, key = _cred()
        if not (nome and cognome and serial and key):
            return
        pref_json = json.dumps(racc_pref(), ensure_ascii=False)
        pl_json = json.dumps(racc_pl(), ensure_ascii=False)
        impronta = _impronta(pref_json, pl_json)
        if impronta == _st['inviato']:
            return                       # v2: uguale all'ultimo invio/scarico: niente rete
        payload = {'nome': nome, 'cognome': cognome, 'serial': serial,
                   'license_key': key, 'action': 'sync_push',
                   'preferiti': pref_json, 'playlist': pl_json}
        req = urllib.request.Request(_url(),
                                     data=json.dumps(payload).encode('utf-8'),
                                     headers={'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                r = json.loads(resp.read().decode('utf-8', 'replace'))
            if r.get('ok'):
                _st['inviato'] = impronta
                print(f"[sync liste] caricate su VPS (elementi={r.get('salvati')})")
            elif r.get('error') != 'not_enabled':
                print(f"[sync liste] server: {r.get('error')}")
        except Exception as e:
            print(f"[sync liste] rete: {e}")

    def sincronizza(subito=False):
        if _st['applica']:
            return
        with _lock:
            t = _st.get('timer')
            if t is not None:
                try: t.cancel()
                except Exception: pass
            nt = threading.Timer(0.5 if subito else 3.0, _invia)
            nt.daemon = True
            _st['timer'] = nt
            nt.start()

    def _applica(pref_json, pl_json):
        _st['applica'] = True
        try:
            if pref_json:
                try:
                    pref = json.loads(pref_json)
                    if isinstance(pref, list):
                        Database.save_preferiti(pref)
                except Exception as e:
                    print(f"[sync liste] applica pref: {e}")
            if pl_json:
                try:
                    pls = json.loads(pl_json)
                    if isinstance(pls, list):
                        nomi = set()
                        for pl in pls:
                            nome = (pl.get('nome') or '').strip()
                            if not nome:
                                continue
                            nomi.add(nome)
                            Database.save_playlist_standalone(nome, pl.get('brani') or [])
                        for loc in (Database.get_playlist_standalone_list() or []):
                            if (loc.get('nome') or '') not in nomi:
                                try: Database.delete_playlist_standalone(loc.get('id'))
                                except Exception: pass
                except Exception as e:
                    print(f"[sync liste] applica pl: {e}")
        finally:
            _st['applica'] = False

    def scarica(*a, **k):
        if not _attiva():
            return False
        nome, cognome, serial, key = _cred()
        if not (nome and cognome and serial and key):
            return False
        payload = {'nome': nome, 'cognome': cognome, 'serial': serial,
                   'license_key': key, 'action': 'sync_pull'}
        req = urllib.request.Request(_url(),
                                     data=json.dumps(payload).encode('utf-8'),
                                     headers={'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                r = json.loads(resp.read().decode('utf-8', 'replace'))
        except Exception as e:
            print(f"[sync liste] pull rete: {e}")
            return False
        if not r.get('ok'):
            if r.get('error') != 'not_enabled':
                print(f"[sync liste] pull server: {r.get('error')}")
            return False
        if not r.get('preferiti') and not r.get('playlist'):
            return False
        _applica(r.get('preferiti'), r.get('playlist'))
        # v2: quello appena scaricato e' gia' sul server: non va rimandato indietro uguale
        try:
            _st['inviato'] = _impronta(json.dumps(racc_pref(), ensure_ascii=False),
                                       json.dumps(racc_pl(), ensure_ascii=False))
        except Exception:
            pass
        print("[sync liste] scaricate dal VPS e applicate in locale")
        return True

    def _wrap(nome):
        orig = getattr(Database, nome, None)
        if orig is None:
            return

        def nuovo(cls, *a, __orig=orig, **k):
            r = __orig(*a, **k)
            try: sincronizza()
            except Exception: pass
            return r

        setattr(Database, nome, classmethod(nuovo))

    for m in ('save_preferiti', 'save_playlist_standalone',
              'delete_playlist_standalone', 'delete_playlist_brano',
              'rename_playlist_standalone', 'update_playlist_brano_tonalita',
              'create_playlist_auto', 'delete_playlist_auto', 'rename_playlist_auto'):
        try: _wrap(m)
        except Exception:
            pass

    Database._syncliste091 = True
    Database._sync_liste_push = sincronizza
    Database._sync_liste_pull = scarica   # per il pulsante "Scarica ora" (patch 092)

    # All'avvio SCARICA dal VPS (l'altro PC prende le modifiche), poi i cambi risalgono
    def _startup():
        try: scarica()
        except Exception as e: print(f"[sync liste] avvio: {e}")
    t0 = threading.Timer(1.5, _startup)
    t0.daemon = True
    t0.start()
    return True


def revert():
    return False


try:
    apply()
except Exception:
    pass
