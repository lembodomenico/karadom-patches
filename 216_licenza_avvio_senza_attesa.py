# 216 - licenza all'avvio: controllo locale subito, verifica sul server in sottofondo

_VER = 1
CODICE = '\n# ── [11-10-2026] verifica all\'avvio senza aspettare il server ──────────────────────────────\n# Prima: is_licensed() all\'avvio aspettava il server (fino a 8 s, prima che esistesse una finestra:\n# schermo nero sulle linee lente). Ora: controllo LOCALE subito (file firmato + hardware), la\n# finestra parte; la verifica sul server gira in sottofondo. Licenza REVOCATA/bloccata/scaduta\n# dal server -> messaggio e KaraDom si chiude (la revoca funziona come prima). Server che\n# semplicemente non conferma (disguido): si prosegue e si riprova al prossimo avvio.\n_ESITI_REVOCA = ("Licenza revocata, bloccata o scaduta", "Licenza non valida",\n                 "File licenza manomesso", "Firma licenza non valida (server non attendibile)")\n\n\ndef _avvio_chiudi_per_revoca(messaggio):\n    import os\n    import time\n    import tkinter\n    for _ in range(120):                      # la finestra puo\' non esistere ancora\n        root = getattr(tkinter, \'_default_root\', None)\n        if root is not None:\n            def _fai():\n                try:\n                    from tkinter import messagebox\n                    messagebox.showerror("KaraDom", "%s\\n\\nIl programma si chiude." % messaggio, parent=root)\n                finally:\n                    os._exit(0)\n            try:\n                root.after(0, _fai)\n                return\n            except Exception:\n                pass\n        time.sleep(1)\n    os._exit(0)\n\n\ndef is_licensed_avvio(_vera=None):\n    """Come is_licensed(), ma per l\'AVVIO: risponde subito col controllo locale e verifica il\n    server in sottofondo. Ritorna (valida, errore, edizione) come is_licensed()."""\n    import sys\n    import threading\n    mod = sys.modules[__name__]\n    vera = _vera or mod.is_licensed\n    rete = mod._is_online_quick\n    mod._is_online_quick = lambda *a, **k: False        # solo locale: nessuna attesa del server\n    try:\n        esito = vera()\n    finally:\n        mod._is_online_quick = rete\n    if not esito[0]:\n        return esito                                     # non valida in locale: si va all\'attivazione\n\n    def _dopo():\n        try:\n            ok, err, _ed = vera()                        # verifica vera, col server\n        except Exception as e:\n            print("Verifica licenza in sottofondo: %s" % e)\n            return\n        if ok:\n            return\n        motivo = (getattr(mod, \'_LAST_REMOTE_REASON\', \'\') or \'\').lower()\n        revoca = err in _ESITI_REVOCA or any(r in motivo for r in getattr(mod, \'_REVOKE_REASONS\', ()))\n        if revoca:\n            print("Licenza revocata dal server: %s" % err)\n            _avvio_chiudi_per_revoca(err or "Licenza non valida")\n        else:\n            print("Licenza non confermata dal server (%s): si riprova al prossimo avvio" % err)\n\n    threading.Thread(target=_dopo, name=\'LicenzaSottofondo\', daemon=True).start()\n    return esito\n'


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
        return str(Database.get_config('patch_216', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def apply():
    """KaraDom.py chiama is_licensed() prima della finestra e aspettava il server (fino a 8 s di
    schermo nero). La PRIMA chiamata dell'avvio diventa: locale subito + server in sottofondo
    (revoca -> messaggio e chiusura). Le chiamate dopo restano quelle di sempre."""
    if _spenta():
        return False
    import sys
    try:
        import moduli.licensing as L
    except Exception:
        return False
    if getattr(L, '_ver216', None) == _VER:
        return True
    if not hasattr(L, 'is_licensed_avvio'):
        exec(compile(CODICE, '<patch216>', 'exec'), L.__dict__)
    vera = L.is_licensed
    stato = {'prima': True}

    def is_licensed(*a, **k):
        if stato['prima']:
            stato['prima'] = False
            return L.is_licensed_avvio(_vera=lambda: vera(*a, **k))
        return vera(*a, **k)

    L.is_licensed = is_licensed
    # KaraDom.py ha preso is_licensed all'inizio, prima delle patch: si cambia anche li'
    principale = sys.modules.get('__main__')
    if principale is not None and getattr(principale, 'is_licensed', None) is vera:
        try:
            setattr(principale, 'is_licensed', is_licensed)
        except Exception:
            pass
    L._ver216 = _VER
    print("[216] licenza all'avvio: controllo locale subito, server in sottofondo")
    return True


def revert():
    return False


try:
    apply()
except Exception:
    pass
