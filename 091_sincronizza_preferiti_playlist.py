# 091 - sincronizza preferiti e playlist
def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_091', '1')) == '0'
    except Exception:
        return False


def apply():
    if _spenta():
        return False
    try:
        from moduli.database import Database
    except Exception:
        return False
    if getattr(Database, '_syncliste091', False):
        return True
    import json
    import threading
    import urllib.request

    URL_DEFAULT = "https://iocanto.karadom.it/api/sync_api.php"
    _lock = threading.Lock()
    _st = {'timer': None, 'applica': False}

    def _url():
        try:
            u = (Database.get_config('sync_api_url', '') or '').strip()
        except Exception:
            u = ''
        return u or URL_DEFAULT

    def _attiva():
        try:
            return str(Database.get_config('sync_liste_attiva', '1')) != '0'
        except Exception:
            return True

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
        payload = {'nome': nome, 'cognome': cognome, 'serial': serial,
                   'license_key': key, 'action': 'sync_push',
                   'preferiti': json.dumps(racc_pref(), ensure_ascii=False),
                   'playlist': json.dumps(racc_pl(), ensure_ascii=False)}
        req = urllib.request.Request(_url(),
                                     data=json.dumps(payload).encode('utf-8'),
                                     headers={'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                r = json.loads(resp.read().decode('utf-8', 'replace'))
            if r.get('ok'):
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
