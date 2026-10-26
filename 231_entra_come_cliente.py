# 231 - il titolare entra come un cliente (richieste remote e catalogo sul DB del cliente)

_VER = 2

_MODULO = '# -*- coding: utf-8 -*-\n"""\ncome_cliente.py — [20-10-2026] il TITOLARE entra in KaraDom come uno dei clienti.\n\nUtente: "farai in modo che solo io dalla mia GUI possa accedere come se fossi il cliente".\n\nOgni cliente con le richieste remote ha il SUO database sul server (creato dal pannello quando\ngli si abilitano le richieste: nome \'nomecognome\', utente = la sua email). Il titolare sceglie un\ncliente da qui e da quel momento richieste remote e catalogo (requests_api / catalogo_api) lavorano\nsul tenant e sul database di quel cliente, come se fosse lui.\n⛔ Preferiti e playlist (sync_api) NO: scaricherebbero le liste del cliente sopra le proprie, e\n   l\'invio automatico scriverebbe le proprie sopra le sue.\n\n⛔ Chi puo\' farlo lo decide il SERVER (_come_cliente.php): la richiesta parte con la licenza di\n   questo PC e il campo `come_cliente`; se la licenza non e\' del titolare risponde \'vietato\'.\n   Qui la voce di menu compare solo se il server ha accettato l\'elenco dei clienti.\n⛔ \'whoami\' (id_software per la diretta del karaoke) resta sempre il proprio: la diretta e\' di\n   chi sta cantando qui, non del cliente.\n"""\nimport threading\n\nfrom moduli.database import Database\n\nCHIAVE = \'come_cliente\'          # config: email del cliente (\'\' = se stessi)\n_stato = {\'titolare\': None, \'clienti\': []}\n\n\ndef attuale():\n    """Email del cliente in cui si e\' entrati, \'\' se si e\' se stessi."""\n    try:\n        return str(Database.get_config(CHIAVE, \'\') or \'\').strip().lower()\n    except Exception:\n        return \'\'\n\n\ndef con_cliente(payload):\n    """Aggiunge `come_cliente` al corpo di una chiamata alle API (tranne \'whoami\')."""\n    c = attuale()\n    if c and isinstance(payload, dict) and payload.get(\'action\') != \'whoami\':\n        payload[\'come_cliente\'] = c\n    return payload\n\n\ndef elenco_clienti():\n    """[(email, \'Nome Cognome (ALIAS)\')] dal server; None se non si e\' il titolare."""\n    from moduli.requests_api_client import api_call\n    r = api_call(\'clienti\')\n    if not (isinstance(r, dict) and r.get(\'ok\')):\n        return None\n    out = []\n    for c in r.get(\'clienti\') or []:\n        nome = (\'%s %s\' % (c.get(\'nome\') or \'\', c.get(\'cognome\') or \'\')).strip()\n        if c.get(\'alias\'):\n            nome += \' (%s)\' % c[\'alias\']\n        out.append((str(c.get(\'email\') or \'\').lower(), nome or c.get(\'email\')))\n    return out\n\n\ndef sono_titolare():\n    """True/False appena il server ha risposto; la prima volta chiede in background (False intanto)."""\n    if _stato[\'titolare\'] is None:\n        _stato[\'titolare\'] = False\n\n        def chiedi():\n            try:\n                el = elenco_clienti()\n                _stato[\'titolare\'] = el is not None\n                _stato[\'clienti\'] = el or []\n            except Exception:\n                pass\n        threading.Thread(target=chiedi, daemon=True).start()\n    return bool(_stato[\'titolare\'])\n\n\ndef nome_attuale():\n    c = attuale()\n    for email, nome in _stato[\'clienti\']:\n        if email == c:\n            return nome\n    return c\n\n\ndef apri_scelta(parent):\n    """Finestrella: elenco dei clienti, \'Entra\' e \'Torna a me\'."""\n    import tkinter as tk\n    from tkinter import messagebox\n\n    el = elenco_clienti()\n    if el is None:\n        messagebox.showerror(\'KaraDom\', \'Solo il titolare puo\\\' entrare come un cliente.\', parent=parent)\n        return\n    _stato[\'clienti\'] = el\n    win = tk.Toplevel(parent)\n    win.title(\'Entra come cliente\')\n    win.configure(bg=\'#1a1a2e\')\n    win.transient(parent)\n    win.attributes(\'-topmost\', True)\n    ora = attuale()\n    tk.Label(win, text=\'Ora sei: \' + (nome_attuale() if ora else \'te stesso\'),\n             bg=\'#1a1a2e\', fg=\'#ffd700\', font=(\'Segoe UI\', 12, \'bold\')).pack(padx=16, pady=(14, 6))\n    lb = tk.Listbox(win, width=46, height=min(14, max(4, len(el))), bg=\'#0a0a0a\', fg=\'white\',\n                    selectbackground=\'#00d4ff\', font=(\'Segoe UI\', 11), activestyle=\'none\')\n    lb.pack(padx=16, pady=6)\n    for i, (email, nome) in enumerate(el):\n        lb.insert(\'end\', \'%s  —  %s\' % (nome, email))\n        if email == ora:\n            lb.selection_set(i)\n\n    def scegli(email):\n        Database.set_config(CHIAVE, email)\n        win.destroy()\n        messagebox.showinfo(\'KaraDom\', (\'Ora lavori come \' + nome_attuale()) if email else \'Sei tornato te stesso.\',\n                            parent=parent)\n\n    def entra(_e=None):\n        sel = lb.curselection()\n        if sel:\n            scegli(el[sel[0]][0])\n\n    lb.bind(\'<Double-Button-1>\', entra)\n    bar = tk.Frame(win, bg=\'#1a1a2e\')\n    bar.pack(padx=16, pady=(6, 14), fill=\'x\')\n    tk.Button(bar, text=\'Entra\', command=entra, width=12).pack(side=\'left\')\n    tk.Button(bar, text=\'Torna a me\', command=lambda: scegli(\'\'), width=12).pack(side=\'right\')\n    win.update_idletasks()\n    win.lift()\n    win.focus_force()\n    if not el:\n        tk.Label(win, text=\'Nessun cliente con le richieste remote.\', bg=\'#1a1a2e\', fg=\'#cccccc\').pack(pady=(0, 10))\n'


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_231', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def _modulo():
    import sys
    import types
    m = types.ModuleType('moduli.come_cliente')
    m.__file__ = '<patch 231>'
    exec(compile(_MODULO, '<patch 231 come_cliente>', 'exec'), m.__dict__)
    m._da231 = _VER
    sys.modules['moduli.come_cliente'] = m
    try:
        import moduli
        moduli.come_cliente = m
    except Exception:
        pass
    return m


def apply():
    if _spenta():
        return False
    try:
        import importlib
        try:
            importlib.import_module('moduli.come_cliente')
            return True                         # compilato nuovo: fa tutto da se'
        except Exception:
            pass
        cc = _modulo()
        cc.sono_titolare()
        import moduli.requests_api_client as R
        if getattr(R, '_ver231', None) != _VER:
            prima = getattr(R, '_o231_api_call', None) or R.api_call
            R._o231_api_call = prima

            def api_call(action, timeout=R._TIMEOUT, **params):
                c = cc.attuale()
                if c and action != 'whoami' and 'come_cliente' not in params:
                    params['come_cliente'] = c
                return prima(action, timeout, **params)
            R.api_call = api_call
            R._ver231 = _VER
        try:
            import moduli.catalogo_remoto as C
            if getattr(C, '_ver231', None) != _VER:
                prima_c = getattr(C, '_o231_chiedi', None) or C._chiedi
                C._o231_chiedi = prima_c

                def _chiedi(azione, **extra):
                    c = cc.attuale()
                    if c and 'come_cliente' not in extra:
                        extra['come_cliente'] = c
                    return prima_c(azione, **extra)
                C._chiedi = _chiedi
                C._ver231 = _VER
        except Exception as e:
            print('[231] catalogo: %s' % e)
        import tkinter as tk
        if getattr(tk.Menu, '_ver231', None) != _VER:
            prima_m = getattr(tk.Menu, '_o231_add_command', None) or tk.Menu.add_command
            tk.Menu._o231_add_command = prima_m

            def add_command(self, cnf=None, **kw):
                esito = prima_m(self, cnf, **kw) if cnf is not None else prima_m(self, **kw)
                try:
                    lab = str(kw.get('label') or '')
                    if 'Remot' in lab and not getattr(self, '_cc231', False) and cc.sono_titolare():
                        self._cc231 = True
                        ora = cc.attuale()
                        prima_m(self, label='Entra come cliente' + ((' (' + cc.nome_attuale() + ')') if ora else '...'),
                                command=lambda w=self: cc.apri_scelta(getattr(tk, '_default_root', None) or w.master))
                except Exception as e:
                    print('[231] menu: %s' % e)
                return esito
            tk.Menu.add_command = add_command
            tk.Menu._ver231 = _VER
        return True
    except Exception as e:
        print('[231] %s' % e)
        return False


def revert():
    try:
        import moduli.requests_api_client as R
        if getattr(R, '_o231_api_call', None):
            R.api_call = R._o231_api_call
            R._ver231 = None
    except Exception:
        pass
    try:
        import moduli.catalogo_remoto as C
        if getattr(C, '_o231_chiedi', None):
            C._chiedi = C._o231_chiedi
            C._ver231 = None
    except Exception:
        pass
    try:
        import tkinter as tk
        if getattr(tk.Menu, '_o231_add_command', None):
            tk.Menu.add_command = tk.Menu._o231_add_command
            tk.Menu._ver231 = None
    except Exception:
        pass
