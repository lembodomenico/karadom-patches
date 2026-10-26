# 227 - KaraDom DJ: automix a tempo (ritornelli, dissolvenza sulla frase, SYNC FADE, 4 deck)
import base64
import os
import sys
import types
import zlib

_VER191 = 14
ESCLUSI = ('3DCB-B3E0-C35B-FAED', '605C-14CE-1283-C667')

_CODICE = (
    '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'
)


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_191', '1')) == '0'
    except Exception:
        return False


def _modulo():
    nome = 'moduli.karadom_dj'
    m = sys.modules.get(nome)
    if m is not None and getattr(m, '_v191', 0) >= _VER191:
        return m
    import moduli
    m = types.ModuleType(nome)
    m.__package__ = 'moduli'
    m.__file__ = nome.replace('.', '/') + '.py'
    sys.modules[nome] = m
    exec(compile(zlib.decompress(base64.b64decode(_CODICE)).decode('utf-8'), 'karadom_dj.py', 'exec'), m.__dict__)
    m._v191 = _VER191
    moduli.karadom_dj = m
    return m


def _escluso():
    try:
        from moduli.licensing import get_hardware_id, generate_serial
        c, m = get_hardware_id()
        return generate_serial(c, m) in ESCLUSI
    except Exception:
        return False


def _senza_dj():
    try:
        import zipfile
        from moduli import dep_sync as S
    except Exception:
        return

    def _completa_mancanti_ora(dest_dir=None, url=None, timeout=S.TIMEOUT, log=print):
        dest = dest_dir or S._dest_dir()
        indirizzo = url or S.DEP_ZIP_URL
        try:
            zf = zipfile.ZipFile(S._HttpRangeFile(indirizzo, timeout))
        except Exception as e:
            log("[dipendenze] zip non raggiungibile: %s" % e)
            return -1, 0
        manca = [i for i in zf.infolist() if not i.is_dir()
                 and not i.filename.replace(chr(92), '/').startswith(('karadom_dj/', 'karadom_remix/'))
                 and not os.path.exists(os.path.join(dest, i.filename.replace("/", os.sep)))]
        presi = byte = 0
        for info in manca:
            try:
                S._write_atomic(os.path.join(dest, info.filename.replace("/", os.sep)),
                                S._fetch_member(indirizzo, info, timeout))
                presi += 1
                byte += info.file_size
            except Exception as e:
                log("[dipendenze] %s non scaricato: %s" % (info.filename, e))
        return presi, byte
    S._completa_mancanti_ora = _completa_mancanti_ora



def _titolare():
    """[26-10-2026] Solo sui PC del titolare (licenza Domenico Lembo), come 239/242/245-249."""
    try:
        from moduli.licensing import load_license
        d = load_license() or {}
        return (str(d.get('nome', '')).strip().lower(),
                str(d.get('cognome', '')).strip().lower()) == ('domenico', 'lembo')
    except Exception:
        return False


def apply():
    if not _titolare():
        return False
    if _spenta() or os.name != 'nt':      # KaraDom OS (Linux): KaraDom DJ non c'e', resta il DJ-set
        return False
    if _escluso():
        _senza_dj()
        return False
    try:
        import moduli.djset as D
        if getattr(D, '_p191', None) == _VER191:
            return True
        if getattr(D, '_p191_o', None) is None:
            D._p191_o = D.apri_djset

        def apri_djset(parent, system):
            return _modulo().apri_karadom_dj(parent, system)
        D.apri_djset = apri_djset
        D._p191 = _VER191
        return True
    except Exception as e:
        print('[patch191] %s' % e)
        return False


def revert():
    try:
        import moduli.djset as D
        if getattr(D, '_p191_o', None) is not None:
            D.apri_djset = D._p191_o
            D._p191 = None
        return True
    except Exception:
        return False


try:
    apply()
except Exception:
    pass
