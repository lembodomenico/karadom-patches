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
    _state = {'timer': None}

    def _url():
        try:
            u = (Database.get_config('sync_api_url', '') or '').strip()
        except Exception:
            u = ''
        return u or URL_DEFAULT

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
        try:
            if str(Database.get_config('sync_liste_attiva', '1')) == '0':
                return
        except Exception:
            pass
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
        with _lock:
            t = _state.get('timer')
            if t is not None:
                try: t.cancel()
                except Exception: pass
            nt = threading.Timer(0.5 if subito else 3.0, _invia)
            nt.daemon = True
            _state['timer'] = nt
            nt.start()

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
    Database._sync_liste_push = sincronizza   # per il toggle in Opzioni (patch 092)
    sincronizza(subito=True)
    return True


def revert():
    return False


try:
    apply()
except Exception:
    pass
