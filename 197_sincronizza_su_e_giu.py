# 197 - playlist: salva sul server e ripristina dal server

import json
import urllib.request

_VER = 2
URL_DEFAULT = "https://iocanto.karadom.it/api/sync_api.php"


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_197', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def _t(s):
    try:
        from moduli.i18n import _ as f
        return f(s)
    except Exception:
        return s


def _url(Database):
    try:
        u = (Database.get_config('sync_api_url', '') or '').strip()
    except Exception:
        u = ''
    return u or URL_DEFAULT


def _playlist(Database):
    liste = []
    try:
        for pl in (Database.get_playlist_standalone_list() or []):
            brani = []
            for b in (Database.get_playlist_standalone_brani(pl.get('id')) or []):
                brani.append({'artista': b.get('artista') or '',
                              'titolo': b.get('titolo') or '',
                              'path': b.get('path') or '',
                              'ext': b.get('ext') or '',
                              'tonalita': b.get('tonalita') or '0',
                              'ordine': b.get('ordine') or 0})
            liste.append({'nome': pl.get('nome') or '', 'brani': brani})
    except Exception as e:
        print("[197] playlist: %s" % e)
    return liste


def _invia(Database, pls):
    try:
        from moduli.requests_api_client import _credenziali_licenza
        nome, cognome, serial, key = _credenziali_licenza()
    except Exception:
        nome = cognome = serial = key = ''
    if not (nome and cognome and serial and key):
        return False, _t("licenza non trovata")
    payload = {'nome': nome, 'cognome': cognome, 'serial': serial,
               'license_key': key, 'action': 'sync_push',
               'playlist': json.dumps(pls, ensure_ascii=False)}
    req = urllib.request.Request(_url(Database), data=json.dumps(payload).encode('utf-8'),
                                 headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            r = json.loads(resp.read().decode('utf-8', 'replace'))
    except Exception as e:
        return False, _t("rete") + ": %s" % e
    if r.get('ok'):
        return True, ''
    if r.get('error') == 'not_enabled':
        return False, _t("richieste remote non attive per questa licenza")
    return False, str(r.get('error'))


def _verso_server(self):
    from tkinter import messagebox
    from moduli.database import Database
    pls = _playlist(Database)
    avviso = ""
    if not pls:
        avviso = "\n\n" + _t("ATTENZIONE: su questo PC ci sono 0 playlist: sul server verranno CANCELLATE.")
    if not messagebox.askyesno(
            _t("Salva le playlist sul server"),
            _t("Mandare al server le %d playlist di questo PC?\n"
               "Sostituiscono quelle salvate sul server.") % len(pls) + avviso,
            parent=self.window):
        return
    ok, msg = _invia(Database, pls)
    if ok:
        messagebox.showinfo(_t("Sincronizzazione"),
                            _t("Salvate sul server: %d playlist.") % len(pls),
                            parent=self.window)
    else:
        messagebox.showwarning(_t("Sincronizzazione"),
                               _t("Invio non riuscito: %s") % msg, parent=self.window)


def _scarica_playlist(Database):
    try:
        from moduli.requests_api_client import _credenziali_licenza
        nome, cognome, serial, key = _credenziali_licenza()
    except Exception:
        nome = cognome = serial = key = ''
    if not (nome and cognome and serial and key):
        return None
    payload = {'nome': nome, 'cognome': cognome, 'serial': serial,
               'license_key': key, 'action': 'sync_pull'}
    req = urllib.request.Request(_url(Database), data=json.dumps(payload).encode('utf-8'),
                                 headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            r = json.loads(resp.read().decode('utf-8', 'replace'))
    except Exception as e:
        print("[197] scarica: %s" % e)
        return None
    if not r.get('ok') or not r.get('playlist'):
        return None
    try:
        pls = json.loads(r.get('playlist'))
    except Exception:
        return None
    if not isinstance(pls, list):
        return None
    nomi = set()
    for pl in pls:
        nome_pl = (pl.get('nome') or '').strip()
        if not nome_pl:
            continue
        nomi.add(nome_pl)
        Database.save_playlist_standalone(nome_pl, pl.get('brani') or [])
    for loc in (Database.get_playlist_standalone_list() or []):
        if (loc.get('nome') or '') not in nomi:
            try:
                Database.delete_playlist_standalone(loc.get('id'))
            except Exception:
                pass
    return len(nomi)


def _dal_server(self):
    from tkinter import messagebox
    from moduli.database import Database
    n = None
    try:
        n = _scarica_playlist(Database)
    except Exception as e:
        print("[197] scarica: %s" % e)
    if n is not None:
        messagebox.showinfo(_t("Sincronizzazione"),
                            _t("Ripristinate dal server: %d playlist.\n"
                               "Riapri la finestra delle playlist per vederle.") % n,
                            parent=self.window)
    else:
        messagebox.showwarning(_t("Sincronizzazione"),
                               _t("Niente da ripristinare (o richieste remote non attive)."),
                               parent=self.window)


def _sistema_bottoni(self):
    import tkinter as tk
    var = getattr(self, 'sync_liste_var', None)
    if var is None:
        return
    try:
        from moduli.ui_scale import S, F
    except Exception:
        S = lambda x: x
        F = lambda *a, **k: (a[0], a[1], a[2]) if len(a) > 2 else (a[0], a[1])

    def cerca(w):
        for c in w.winfo_children():
            try:
                if c.winfo_class() == 'Checkbutton' and str(c.cget('variable')) == str(var):
                    return c.master
            except Exception:
                pass
            r = cerca(c)
            if r is not None:
                return r
        return None

    box = cerca(self.window)
    if box is None or getattr(box, '_sync197', False):
        return

    def ha_su(w):
        for c in w.winfo_children():
            try:
                if c.winfo_class() == 'Button' and '⬆' in str(c.cget('text')):
                    return True
            except Exception:
                pass
            if ha_su(c):
                return True
        return False

    if ha_su(box):
        return
    for c in list(box.winfo_children()):
        try:
            if c.winfo_class() == 'Button':
                c.destroy()
        except Exception:
            pass
    riga = tk.Frame(box, bg=box.cget('bg'))
    riga.pack(anchor='w', pady=(S(10), 0))
    tk.Button(riga, text="⬆  " + _t("Salva le playlist sul server"),
              command=lambda: _verso_server(self), bg='#28a745', fg='white',
              font=F('Arial', 10, 'bold'), relief='flat', padx=S(16), pady=S(6),
              cursor='hand2').pack(side='left')
    tk.Button(riga, text="⬇  " + _t("Ripristina le playlist dal server"),
              command=lambda: _dal_server(self), bg='#0078D7', fg='white',
              font=F('Arial', 10, 'bold'), relief='flat', padx=S(16), pady=S(6),
              cursor='hand2').pack(side='left', padx=(S(10), 0))
    box._sync197 = True


def apply():
    if _spenta():
        return False
    try:
        import moduli.opzioni as O
    except Exception:
        return False
    C = getattr(O, 'OpzioniWindow', None)
    if C is None or not hasattr(C, 'create_tab_playlist'):
        return False
    if getattr(C, '_sync197', None) == _VER:
        return True
    orig = getattr(C, '_sync197_o_tab', None)
    if orig is None:
        orig = C.create_tab_playlist
        C._sync197_o_tab = orig

    def create_tab_playlist(self, *a, **k):
        r = orig(self, *a, **k)
        try:
            _sistema_bottoni(self)
        except Exception as e:
            print("[197] bottoni: %s" % e)
        return r

    C.create_tab_playlist = create_tab_playlist
    C._sync197 = _VER
    return True


def revert():
    try:
        import moduli.opzioni as O
        C = O.OpzioniWindow
        o = getattr(C, '_sync197_o_tab', None)
        if o is not None:
            C.create_tab_playlist = o
        C._sync197 = None
    except Exception:
        pass
