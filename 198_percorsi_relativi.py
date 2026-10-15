# 198 - brani delle playlist trovati anche se le basi stanno in un altro posto

import os
import sys
import types

_VER = 2
_SORGENTE = '# -*- coding: utf-8 -*-\n"""Percorsi RELATIVI dei brani (playlist, scaletta, preferiti).\n\nUna playlist fatta su un PC si porta dietro percorsi assoluti (C:\\\\KARAOKE\\\\Basi\\\\x.mp3,\nC:/DJSet\\\\2025\\\\y.mp4): su un altro computer - KaraDom OS, un PC con le basi su D:, una\nchiavetta - quei percorsi non esistono e il brano "non si trova" anche se c\'e\'.\n\nStesso metodo di linux/touch/percorsi_touch.py:\n  1) la parte RELATIVA del percorso (Basi/4 - MP3/x.mp3, poi 4 - MP3/x.mp3, poi x.mp3)\n     cercata sotto le cartelle delle basi di QUESTO computer;\n  2) se non c\'e\' su disco, il file per nome (o artista + titolo) negli ARCHIVI delle basi\n     (basi_mp3/video/midi.db), estratto solo adesso che serve.\n\n⛔ Il percorso trovato NON si riscrive nel database delle playlist: con la sincronizzazione\n   finirebbe sul server e rovinerebbe le playlist degli altri PC.\n"""\nimport os\nimport re\nimport sqlite3\nimport sys\n\n_cache = {}\n\n\ndef _pezzi(p):\n    """\'C:\\\\KARAOKE\\\\Basi\\\\x.mp3\' -> [\'KARAOKE\', \'Basi\', \'x.mp3\'] (senza unita\')."""\n    pezzi = [x for x in re.split(r\'[\\\\/]+\', str(p or \'\')) if x]\n    if pezzi and re.fullmatch(r\'[A-Za-z]:\', pezzi[0]):\n        pezzi = pezzi[1:]\n    return pezzi\n\n\ndef _cartella_estratte():\n    try:\n        from moduli.carica_basi import _destinazione_estrazione_predefinita\n        d = _destinazione_estrazione_predefinita()\n        if d:\n            return d\n    except Exception:\n        pass\n    base = os.environ.get(\'LOCALAPPDATA\') or os.path.expanduser(\'~\')\n    return os.path.join(base, \'KaraDom\', \'basi_estratte\')\n\n\ndef radici():\n    """Le cartelle sotto cui cercare la parte relativa."""\n    out = []\n    try:\n        from moduli.database import Database\n        for k in (\'cartella_basi\', \'ultima_cartella_preferita\'):\n            v = Database.get_config(k, \'\') or \'\'\n            if v:\n                out += [v, os.path.dirname(v.rstrip(\'/\\\\\'))]\n        for pr in (Database.get_preferiti() or []):\n            v = pr.get(\'path\') if isinstance(pr, dict) else pr\n            if v:\n                out += [v, os.path.dirname(str(v).rstrip(\'/\\\\\'))]\n    except Exception:\n        pass\n    out.append(_cartella_estratte())\n    if sys.platform.startswith(\'win\'):\n        import string\n        out += [\'%s:\\\\\' % l for l in string.ascii_uppercase if os.path.isdir(\'%s:\\\\\' % l)]\n    else:\n        casa = os.path.expanduser(\'~\')\n        out += [os.path.join(casa, \'KARAOKE\'), os.path.join(casa, \'KaraDom\'), casa]\n        for base in (\'/media\', \'/run/media\', \'/mnt\'):\n            try:\n                out += [os.path.join(base, n) for n in os.listdir(base)]\n            except Exception:\n                pass\n    visti, buone = set(), []\n    for r in out:\n        k = os.path.normcase(os.path.normpath(r)) if r else \'\'\n        if r and k not in visti and os.path.isdir(r):\n            visti.add(k)\n            buone.append(r)\n    return buone\n\n\ndef _da_archivio(p):\n    """Il brano negli archivi delle basi, estratto adesso. Percorso o None."""\n    pezzi = _pezzi(p)\n    if not pezzi:\n        return None\n    nome = pezzi[-1]\n    stem, est = os.path.splitext(nome)\n    est = est.lower()\n    try:\n        from moduli import carica_basi as CB\n        dbs = CB.db_disponibili()\n    except Exception:\n        return None\n    ordine = sorted(dbs.items(), key=lambda kv: 0 if (\n        (kv[0] == \'midi\' and est in (\'.mid\', \'.midi\', \'.kar\')) or\n        (kv[0] == \'video\' and est in (\'.mp4\', \'.mkv\', \'.avi\', \'.webm\', \'.mov\', \'.mpg\', \'.wmv\')) or\n        (kv[0] == \'mp3\' and est in (\'.mp3\', \'.wav\', \'.m4a\', \'.flac\', \'.ogg\'))) else 1)\n    artista, titolo = \'\', \'\'\n    if \' - \' in stem:\n        artista, titolo = [x.strip().lower() for x in stem.split(\' - \', 1)]\n    for _chiave, db in ordine:\n        try:\n            con = sqlite3.connect(\'file:%s?mode=ro\' % db, uri=True, timeout=5)\n            try:\n                # ⛔ prima il nome ESATTO: lower() di SQLite non tocca le lettere accentate\n                #    ("È" resta "È"), quindi "Marlon Brando È Sempre Lui" col solo lower non si trovava\n                r = con.execute(\'SELECT id FROM basi WHERE file_nome=? LIMIT 1\', (nome,)).fetchone()\n                if not r:\n                    r = con.execute(\'SELECT id FROM basi WHERE lower(file_nome)=? LIMIT 1\',\n                                    (nome.lower(),)).fetchone()\n                if not r and artista and titolo:\n                    r = con.execute(\'SELECT id FROM basi WHERE lower(artista)=? AND lower(titolo)=? LIMIT 1\',\n                                    (artista, titolo)).fetchone()\n            finally:\n                con.close()\n            if r:\n                return CB.estrai_una_base(db, r[0], _cartella_estratte())\n        except Exception as e:\n            print(\'⚠️ archivio %s: %s\' % (db, e))\n    return None\n\n\ndef risolvi(p):\n    """Il file vero per un percorso salvato; se non si trova, il percorso com\'era."""\n    if not p or not isinstance(p, str) or \'://\' in p:\n        return p\n    if os.path.exists(p):\n        return p\n    if p in _cache and os.path.exists(_cache[p]):\n        return _cache[p]\n    pezzi = _pezzi(p)\n    if not pezzi:\n        return p\n    trovato = None\n    dove = radici()\n    for i in range(len(pezzi)):          # dal percorso piu\' lungo al solo nome del file\n        coda = os.path.join(*pezzi[i:])\n        for r in dove:\n            c = os.path.join(r, coda)\n            if os.path.isfile(c):\n                trovato = c\n                break\n        if trovato:\n            break\n    if not trovato:\n        trovato = _da_archivio(p)\n    if trovato:\n        _cache[p] = trovato\n        print(\'📂 percorso relativo: %s -> %s\' % (p, trovato))\n        return trovato\n    return p\n'


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_198', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def _modulo():
    # se il programma ha gia' il suo modulo (sorgente nuovo, KaraDom OS) si usa quello
    try:
        import importlib
        vero = importlib.import_module('moduli.percorsi_brani')
        if getattr(vero, '__file__', '') != '<patch198>' and hasattr(vero, 'risolvi'):
            return vero
    except Exception:
        pass
    m = sys.modules.get('moduli.percorsi_brani')
    if m is not None and getattr(m, '_ver198', None) == _VER:
        return m
    m = types.ModuleType('moduli.percorsi_brani')
    m.__file__ = '<patch198>'
    exec(compile(_SORGENTE, 'percorsi_brani_198', 'exec'), m.__dict__)
    m._ver198 = _VER
    sys.modules['moduli.percorsi_brani'] = m
    try:
        import moduli
        moduli.percorsi_brani = m
    except Exception:
        pass
    return m


def _avvolgi(C, nome, flag):
    if C is None or not hasattr(C, nome):
        return
    if getattr(C, flag, None) == _VER:
        return
    orig = getattr(C, flag + '_o', None) or getattr(C, nome)
    setattr(C, flag + '_o', orig)

    def nuovo(self, path=None, *a, **k):
        try:
            if isinstance(path, str) and path and '://' not in path and not os.path.exists(path):
                path = sys.modules['moduli.percorsi_brani'].risolvi(path)
        except Exception:
            pass
        return orig(self, path, *a, **k)

    setattr(C, nome, nuovo)
    setattr(C, flag, _VER)


def apply():
    if _spenta():
        return False
    _modulo()
    for mod, cls, met in (('moduli.libreria', 'LibreriaSlider', 'play_brano'),
                          ('moduli.playlist', 'PlaylistSlider', 'play_brano'),
                          ('moduli.engine', 'KaraokeTextEngine', 'extract')):
        try:
            __import__(mod)
            _avvolgi(getattr(sys.modules[mod], cls, None), met, '_rel198_' + met)
        except Exception as e:
            print('[198] %s.%s: %s' % (cls, met, e))
    return True
