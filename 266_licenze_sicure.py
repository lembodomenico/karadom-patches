import base64
import sys
import threading
import time

_VER = 1
_SRC_GRAZIA = '''GRAZIA_OFFLINE_GIORNI = 7


def _grazia_offline(motivo):
    adesso = time.time()
    chiave = 'grazia_' + hashlib.sha256(motivo.encode()).hexdigest()[:8]
    letti = []
    try:
        import winreg
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r'Software\\KaraDom') as k:
            try:
                letti.append(float(winreg.QueryValueEx(k, chiave)[0]))
            except Exception:
                pass
    except Exception:
        pass
    f = _get_base_internal_path() / ('_%s.dat' % chiave)
    try:
        letti.append(float(f.read_text().strip()))
    except Exception:
        pass
    inizio = min([x for x in letti if 0 < x <= adesso + 86400] or [adesso])
    try:
        import winreg
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r'Software\\KaraDom') as k:
            winreg.SetValueEx(k, chiave, 0, winreg.REG_SZ, repr(inizio))
    except Exception:
        pass
    try:
        f.write_text(repr(inizio))
    except Exception:
        pass
    giorni = (adesso - inizio) / 86400.0
    if giorni > GRAZIA_OFFLINE_GIORNI:
        print("Grazia senza Internet finita (%s, %.0f giorni): serve la rete una volta" % (motivo, giorni))
        return False
    print("Grazia senza Internet (%s): giorno %.1f di %d" % (motivo, giorni, GRAZIA_OFFLINE_GIORNI))
    return True
'''

_SRC_REC = '''import urllib.parse
import urllib.request

_VER = 1


def _licenza():
    try:
        from moduli.licensing import load_license
        s = load_license() or {}
        if s.get('nome') and s.get('cognome') and s.get('serial') and s.get('license'):
            return {'nome': s['nome'], 'cognome': s['cognome'], 'serial': s['serial'],
                    'license_key': s['license']}
    except Exception:
        pass
    return None


def installa():
    if getattr(urllib.request, '_rec_licenza', None) == _VER:
        return True
    o = getattr(urllib.request, '_rec_licenza_o', None) or urllib.request.urlopen
    urllib.request._rec_licenza_o = o

    def urlopen(url, data=None, *a, **k):
        try:
            u = url if isinstance(url, str) else getattr(url, 'full_url', '')
            if data is None and isinstance(u, str) and '/rec_cmd.php?' in u and 'key=' in u:
                lic = _licenza()
                if lic:
                    base, q = u.split('?', 1)
                    par = [(a_, b_) for a_, b_ in urllib.parse.parse_qsl(q, keep_blank_values=True)
                           if a_ != 'key']
                    nuovo = base + '?' + urllib.parse.urlencode(par)
                    corpo = urllib.parse.urlencode(lic).encode('utf-8')
                    req = urllib.request.Request(nuovo, data=corpo, method='POST')
                    return o(req, None, *a, **k)
        except Exception:
            pass
        return o(url, data, *a, **k)
    urllib.request.urlopen = urlopen
    urllib.request._rec_licenza = _VER
    return True
'''

_IMPRONTA = 'D621E1EC9010EECC900B6EB12B95719F914AC55B'


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_266', '1')) == '0'
    except Exception:
        return False


def _log(t):
    try:
        print('[S266] %s' % t)
    except Exception:
        pass


def _modulo(nome):
    m = sys.modules.get(nome)
    if m is None:
        import importlib
        m = importlib.import_module(nome)
    return m


def _grazia():
    L = _modulo('moduli.licensing')
    if getattr(L, '_s266', None) == _VER:
        return
    if hasattr(L, '_grazia_offline') or getattr(L, '_s264', None):
        L._s266 = _VER
        return
    sp = {}
    exec(compile(_SRC_GRAZIA, 's266_grazia', 'exec'), L.__dict__, sp)
    grazia = sp['_grazia_offline']
    L._grazia_offline = grazia
    L.GRAZIA_OFFLINE_GIORNI = sp['GRAZIA_OFFLINE_GIORNI']
    o_mig = L.migrate_license_serial
    o_firma = L._license_signature_valid
    o_rem = L.verify_license_remote
    stato = {'t': 0.0, 'th': None}

    def migrate_license_serial(saved, current_serial, *a, **k):
        r = o_mig(saved, current_serial, *a, **k)
        if r is None and not grazia('seriale ' + str((saved or {}).get('serial'))):
            return False
        return r

    def _license_signature_valid(saved, *a, **k):
        r = o_firma(saved, *a, **k)
        if not r:
            stato['t'], stato['th'] = time.time(), threading.get_ident()
        return r

    def verify_license_remote(*a, **k):
        r = o_rem(*a, **k)
        subito = stato['th'] == threading.get_ident() and time.time() - stato['t'] < 30
        if r is None and subito:
            stato['th'] = None
            if not grazia('non firmata'):
                return False
        return r
    L.migrate_license_serial = migrate_license_serial
    L._license_signature_valid = _license_signature_valid
    L.verify_license_remote = verify_license_remote
    L._s266 = _VER
    _log('licenza: senza rete al massimo %d giorni' % L.GRAZIA_OFFLINE_GIORNI)


def _rec():
    import types
    m = sys.modules.get('moduli.rec_licenza')
    if m is None:
        m = types.ModuleType('moduli.rec_licenza')
        exec(compile(_SRC_REC, 's266_rec', 'exec'), m.__dict__)
        sys.modules['moduli.rec_licenza'] = m
    if m.installa():
        _log('registrazioni della diretta: con la licenza')


def _devoc():
    L = _modulo('moduli.licensing')
    if hasattr(L, '_devoc_firmato') or not hasattr(L, '_set_devoc') or not hasattr(L, 'devoc_abilitato'):
        return
    if getattr(L, '_devoc266', None) == _VER:
        return
    verifica = L._rsa_verify_pkcs1_sha256

    def _set_devoc(devoc):
        if not isinstance(devoc, dict):
            devoc = {}
        sc = devoc.get('scadenza')
        sc = '' if sc is None else str(sc).strip()[:10]
        try:
            from moduli.database import Database
            Database.set_config('devoc_attivo', L._kdm_bool(devoc.get('attivo', 0)))
            Database.set_config('devoc_scadenza', sc)
            Database.set_config('devoc_sig', str(devoc.get('sig') or ''))
        except Exception:
            pass

    def _devoc_firmato(sc):
        try:
            from moduli.database import Database
            sig_b64 = (Database.get_config('devoc_sig', '') or '').strip()
            if not sig_b64:
                g = getattr(L, '_grazia_offline', None)
                return bool(g and g('devoc senza firma'))
            saved = L.load_license() or {}
            msg = ('DEVOC|%s|1|%s' % (saved.get('serial') or '', sc or '')).encode('utf-8')
            return bool(verifica(msg, base64.b64decode(sig_b64.encode())))
        except Exception:
            return False

    def devoc_abilitato():
        try:
            from moduli.database import Database
            if Database.get_config('devoc_attivo', '0') != '1':
                return False
            sc = (Database.get_config('devoc_scadenza', '') or '').strip()
        except Exception:
            return False
        if not _devoc_firmato(sc):
            return False
        if not sc:
            return True
        try:
            from datetime import date
            y, m, d = sc.split('-')
            return date(int(y), int(m), int(d)) >= date.today()
        except Exception:
            return True
    L._set_devoc = _set_devoc
    L._devoc_firmato = _devoc_firmato
    L.devoc_abilitato = devoc_abilitato
    L._devoc266 = _VER
    _log('devocalizza: abbonamento firmato dal server')


def _firma_ok(percorso):
    if sys.platform != 'win32':
        return True
    try:
        import os
        import subprocess
        cmd = ("$s = Get-AuthenticodeSignature -LiteralPath $env:KD_FILE; "
               "$s.Status.ToString() + '|' + $(if ($s.SignerCertificate) { $s.SignerCertificate.Thumbprint } else { '' })")
        env = dict(os.environ, KD_FILE=str(percorso))
        r = subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command', cmd],
                           capture_output=True, text=True, timeout=60, env=env,
                           creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        stato, _, impronta = (r.stdout or '').strip().partition('|')
        ok = stato not in ('HashMismatch', 'NotSigned', 'NotSupportedFileFormat', '') \
            and impronta.strip().upper() == _IMPRONTA
        _log('firma installer: %s %s -> %s' % (stato, impronta[:8], 'OK' if ok else 'RIFIUTATO'))
        return ok
    except Exception as e:
        _log('controllo firma installer non riuscito: %s' % e)
        return False


def _installer():
    U = _modulo('moduli.updater')
    if hasattr(U, 'firma_karadom_ok') or not hasattr(U, 'install_update'):
        return
    if getattr(U, '_inst266', None) == _VER:
        return
    o = getattr(U, '_inst266_o', None) or U.install_update
    U._inst266_o = o

    def install_update(installer_path, *a, **k):
        if not _firma_ok(installer_path):
            try:
                from tkinter import messagebox
                messagebox.showerror('Aggiornamento KaraDom',
                                     "L'aggiornamento scaricato non porta la firma di KaraDom e non e' stato "
                                     "installato.\n\nScarica KaraDom da www.karadom.it")
            except Exception:
                pass
            return False
        return o(installer_path, *a, **k)
    U.install_update = install_update
    U.firma_karadom_ok = _firma_ok
    U._inst266 = _VER
    _log('aggiornamenti: solo installatori firmati KaraDom')


def apply():
    if _spenta():
        return False
    for f in (_grazia, _rec, _devoc, _installer):
        try:
            f()
        except Exception as e:
            _log('%s: %s' % (f.__name__, e))
    return True


try:
    apply()
except Exception as _e:
    print('patch 266: %s' % _e)
