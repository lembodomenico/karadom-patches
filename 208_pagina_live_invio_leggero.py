# 208 - pagina Live: un solo invio alla volta, connessione riusata, tempo solo se qualcuno guarda

_VER = 1
CODICE = '\n    # ── invio [11-10-2026]: pensato per le linee lente ─────────────────────\n    # Prima: un thread e una connessione HTTPS NUOVI per ogni invio, il tempo ogni 1,2 s a\n    # tutti, senza limite -> su linea lenta 8+ strette di mano TLS insieme che intasano la\n    # linea ("handshake timed out"). Ora:\n    #   * UN solo lavoratore con una coda, UNA connessione che resta aperta (keep-alive);\n    #   * il tempo parte ogni 2 s solo se qualcuno guarda la pagina Live (il server lo dice\n    #     nella risposta: \'spettatori\'), altrimenti ogni 15 s (il server proietta da solo);\n    #   * se un invio e\' in corso il tempo nuovo SOSTITUISCE quello in attesa (mai accodati);\n    #   * linea che non risponde: attesa crescente 2..60 s, il tempo intanto si salta.\n    _OGNI_CON_SPETTATORI = 2.0\n    _OGNI_SENZA = 15.0\n\n    def _invio_init(self):\n        if getattr(self, \'_coda_invii\', None) is not None:\n            return\n        import collections\n        self._coda_invii = collections.deque()\n        self._tempo_in_attesa = None\n        self._evento_invii = threading.Event()\n        self._conn_https = None\n        self._spettatori = True            # finche\' il server non dice il contrario\n        self._ultimo_tempo_inviato = 0.0\n        self._pausa_rete_fino = 0.0\n        self._attesa_rete = 0.0\n        threading.Thread(target=self._lavoratore_invii, name=\'WebSyncInvii\', daemon=True).start()\n\n    def _post(self, data, blocking=False):\n        """Mette in coda l\'invio verso live_text.php (un lavoratore solo, connessione riusata)."""\n        if not self.connected or not self.id_software:\n            if data.get(\'type\') in (\'song_start\', \'song_stop\', \'pause\'):\n                _log(f"SEND SALTATO (connected={self.connected}): {data.get(\'type\')}")\n            return\n        self._invio_init()\n        tipo = data.get(\'type\')\n        adesso = time.time()\n        if tipo == \'time_update\':\n            if adesso < self._pausa_rete_fino:\n                return                                   # linea giu\': il tempo si salta\n            ogni = self._OGNI_CON_SPETTATORI if self._spettatori else self._OGNI_SENZA\n            if adesso - self._ultimo_tempo_inviato < ogni:\n                return\n            self._tempo_in_attesa = data                 # sostituisce quello non ancora partito\n        else:\n            if tipo == \'song_start\':                     # brano nuovo: le cose vecchie non servono piu\'\n                self._coda_invii.clear()\n                self._tempo_in_attesa = None\n            self._coda_invii.append(data)\n        self._evento_invii.set()\n\n    def _carico(self, data):\n        nome, cognome, serial, key = self._cred\n        payload = {k: v for k, v in data.items() if not k.startswith(\'_\')}\n        payload.update({\n            "action": "push", "id_software": self.id_software,\n            "nome": nome, "cognome": cognome, "serial": serial, "license_key": key,\n        })\n        if self._seq is not None:\n            payload.setdefault("seq", self._seq)\n        return payload\n\n    def _manda(self, payload):\n        """Un POST sulla connessione che resta aperta; la rifa\' una volta se il server l\'ha chiusa."""\n        import http.client\n        import ssl\n        from urllib.parse import urlparse\n        u = urlparse(self.endpoint)\n        body = json.dumps(payload).encode(\'utf-8\')\n        for tentativo in (1, 2):\n            if self._conn_https is None:\n                ctx = getattr(type(self), \'_ctx_ssl\', None)\n                if ctx is None:\n                    try:\n                        import certifi\n                        ctx = ssl.create_default_context(cafile=certifi.where())\n                    except Exception:\n                        ctx = ssl.create_default_context()\n                    type(self)._ctx_ssl = ctx\n                self._conn_https = http.client.HTTPSConnection(u.hostname, u.port or 443, timeout=8, context=ctx)\n            try:\n                self._conn_https.request(\'POST\', u.path or \'/\', body=body,\n                                         headers={\'Content-Type\': \'application/json\', \'Connection\': \'keep-alive\'})\n                r = self._conn_https.getresponse()\n                testo = r.read()\n                try:\n                    return json.loads(testo.decode(\'utf-8\', \'replace\'))\n                except Exception:\n                    return {}\n            except (http.client.RemoteDisconnected, http.client.CannotSendRequest, BrokenPipeError,\n                    ConnectionResetError):\n                self._chiudi_conn()                      # il server ha chiuso la connessione: si riapre\n                if tentativo == 2:\n                    raise\n            except Exception:\n                self._chiudi_conn()\n                raise\n\n    def _chiudi_conn(self):\n        try:\n            if self._conn_https is not None:\n                self._conn_https.close()\n        except Exception:\n            pass\n        self._conn_https = None\n\n    def _lavoratore_invii(self):\n        while True:\n            self._evento_invii.wait(5)\n            self._evento_invii.clear()\n            while True:\n                if self._coda_invii:\n                    data = self._coda_invii.popleft()\n                elif self._tempo_in_attesa is not None:\n                    data, self._tempo_in_attesa = self._tempo_in_attesa, None\n                else:\n                    break\n                tipo = data.get(\'type\')\n                if tipo == \'time_update\' and time.time() < self._pausa_rete_fino:\n                    continue\n                try:\n                    r = self._manda(self._carico(data))\n                    if isinstance(r, dict) and \'spettatori\' in r:\n                        self._spettatori = bool(r[\'spettatori\'])\n                    if tipo == \'time_update\':\n                        self._ultimo_tempo_inviato = time.time()\n                    self._attesa_rete = 0.0\n                    self._pausa_rete_fino = 0.0\n                except Exception as e:\n                    self._attesa_rete = min(60.0, (self._attesa_rete * 2) or 2.0)\n                    self._pausa_rete_fino = time.time() + self._attesa_rete\n                    _log(f"POST {tipo} fallito: {e} (riprovo fra {int(self._attesa_rete)} s)")\n                    if tipo != \'time_update\' and not data.get(\'_ritentato\'):\n                        # i messaggi del brano (inizio, pausa, fine): un secondo tentativo dopo l\'attesa\n                        self._coda_invii.appendleft(dict(data, _ritentato=1))\n                        time.sleep(self._attesa_rete)\n\n\n    def send_song_start(self, title, artist, syllables_data):\n        # system.py lo chiama al caricamento E al play dello stesso brano: il testo parte una volta\n        chiave = (title, artist, len(syllables_data or ()))\n        if getattr(self, \'_ultimo_brano\', None) == chiave and time.time() - getattr(self, \'_ultimo_brano_t\', 0) < 15:\n            self._playing = True\n            return\n        self._ultimo_brano, self._ultimo_brano_t = chiave, time.time()\n        self._seq = int(time.time() * 1000)\n        self._playing = True\n        self._last_time_ms = 0\n        self._last_sent_time = -1\n        syl = [{"text": _fix_testo(s[0]), "time": s[1]} for s in syllables_data]\n        _log(f"song_start: {title} ({len(syl)} sillabe) connected={self.connected}")\n        self._post({\n            "type": "song_start", "title": _fix_testo(title) or "Sconosciuto",\n            "artist": _fix_testo(artist) or "", "syllables": syl, "seq": self._seq,\n        })\n'


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
        return str(Database.get_config('patch_208', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def apply():
    if _spenta():
        return False
    try:
        from moduli import websocket_sync as W
    except Exception:
        return False
    K = getattr(W, 'KaraokeWebSync', None)
    if K is None or getattr(K, '_ver208', None) == _VER:
        return K is not None
    if hasattr(K, '_lavoratore_invii'):
        K._ver208 = _VER                 # eseguibile nuovo: lo fa gia' da se'
        return True
    ns = {}
    # le funzioni nascono nel modulo vero (threading, time, json, _log, _fix_testo sono i suoi)
    exec(compile("class _Nuova:\n" + CODICE, "<patch208>", "exec"), W.__dict__, ns)
    nuova = ns['_Nuova']
    for nome, valore in list(nuova.__dict__.items()):
        if nome.startswith('__'):
            continue
        setattr(K, nome, valore)
    K._ver208 = _VER
    print("[208] pagina Live: invio unico, connessione riusata, tempo solo se qualcuno guarda")
    return True


def revert():
    return False


try:
    apply()
except Exception:
    pass
