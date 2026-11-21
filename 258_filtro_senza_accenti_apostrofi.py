# 258 - filtro senza accenti e apostrofi

import os
import re
import threading
import unicodedata

_VER = 2

_PESO = {
    'mp3': 0, 'wav': 0, 'm4a': 0, 'flac': 0, 'ogg': 0, 'wma': 0,
    'mp4': 1, 'mkv': 1, 'avi': 1, 'mov': 1, 'webm': 1, 'mpg': 1, 'mpeg': 1, 'm4v': 1, 'wmv': 1, 'flv': 1,
    'mid': 2, 'midi': 2, 'kar': 2,
}


def _peso(ext):
    return _PESO.get((ext or '').lower(), 3)


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_258', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def _parole(s):
    s = unicodedata.normalize('NFD', str(s or '').lower())
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.findall(r'[a-z0-9]+', s)


def _file_norm(f016):
    if f016.endswith('.ricerca.db'):
        return f016[:-len('.ricerca.db')] + '.norm258.db'
    return f016 + '.norm258'


def _firma(f016, n):
    try:
        return '%d|%d|%d' % (_VER, n, int(os.path.getmtime(f016)))
    except Exception:
        return None


def _prepara(self):
    pronta = getattr(self, '_tabella016', None)
    if not pronta or getattr(self, '_n258_in_corso', False):
        return
    fatta = getattr(self, '_tabella258', None)
    if fatta and fatta[0] is pronta[0] and fatta[1] == pronta[1]:
        return
    self._n258_in_corso = True

    def lavora(lista=pronta[0], n=pronta[1], f016=pronta[2]):
        import sqlite3
        import time
        try:
            f = _file_norm(f016)
            firma = _firma(f016, n)
            if firma is None:
                return
            if os.path.exists(f):
                try:
                    c = sqlite3.connect('file:%s?mode=ro' % f, uri=True, timeout=3)
                    v = c.execute("SELECT v FROM meta WHERE k = 'firma'").fetchone()
                    c.close()
                    if v and v[0] == firma:
                        self._tabella258 = (lista, n, f)
                        return
                except Exception:
                    pass
            src = sqlite3.connect('file:%s?mode=ro' % f016, uri=True, timeout=3)
            righe = []
            for k, (pos, nome, ext) in enumerate(src.execute('SELECT pos, nome, ext FROM basi')):
                w = _parole(nome)
                e = (ext or os.path.splitext(nome or '')[1][1:]).lower()
                righe.append((pos, ' ' + ' '.join(w) + ' ', ''.join(w), e, _peso(e)))
                if k % 4000 == 3999:
                    time.sleep(0.002)
            src.close()
            tmp = f + '.tmp'
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except Exception:
                pass
            con = sqlite3.connect(tmp)
            con.execute('PRAGMA journal_mode=OFF')
            con.execute('PRAGMA synchronous=OFF')
            con.execute('CREATE TABLE norm (pos INTEGER PRIMARY KEY, norm TEXT, unito TEXT, ext TEXT, peso INTEGER)')
            con.execute('CREATE TABLE meta (k TEXT PRIMARY KEY, v TEXT)')
            con.executemany('INSERT INTO norm VALUES (?,?,?,?,?)', righe)
            con.execute("INSERT INTO meta VALUES ('firma', ?)", (firma,))
            con.commit()
            con.close()
            os.replace(tmp, f)
            self._tabella258 = (lista, n, f)
            print('[258] %d brani pronti per la ricerca senza accenti' % n)
        except Exception as e:
            print('[258] tabella non creata: %s' % e)
        finally:
            self._n258_in_corso = False

    threading.Thread(target=lavora, daemon=True).start()


def _condizioni(parti, parti_ext):
    dove, valori = [], []
    for k, parte in enumerate(parti):
        if parti_ext[k]:
            dove.append('ext = ?')
            valori.append(parte)
            continue
        w = _parole(parte)
        if not w:
            continue
        frase = ' '.join(w)
        if len(frase) == 1:
            dove.append('norm LIKE ?')
            valori.append('%% %s %%' % frase)
        elif len(frase) >= 5:
            dove.append('(norm LIKE ? OR unito LIKE ?)')
            valori.append('%%%s%%' % frase)
            valori.append('%%%s%%' % ''.join(w))
        else:
            dove.append('norm LIKE ?')
            valori.append('%%%s%%' % frase)
    return dove, valori


def _cerca(self, parti, parti_ext, brani_ref, tetto):
    import sqlite3
    fatta = getattr(self, '_tabella258', None)
    brani = self.brani_pc or ()
    if not fatta or fatta[0] is not brani or fatta[1] != len(brani) or not os.path.exists(fatta[2]):
        return None
    dove, valori = _condizioni(parti, parti_ext)
    if not dove:
        return None
    con = sqlite3.connect('file:%s?mode=ro' % fatta[2], uri=True, timeout=3)
    try:
        cur = con.execute('SELECT pos FROM norm WHERE %s ORDER BY peso, pos LIMIT ?' % ' AND '.join(dove),
                          valori + [tetto])
        fuori = [r[0] for r in cur.fetchall()]
    finally:
        con.close()
    return [p for p in fuori if 0 <= p < len(brani_ref)]


def _una_volta(posizioni, brani_ref, tetto):
    visti, tenuti = set(), []
    for p in posizioni:
        try:
            n = brani_ref[p]['nome'].strip().lower()
        except Exception:
            n = None
        if n is not None and n in visti:
            continue
        if n is not None:
            visti.add(n)
        tenuti.append(p)
        if len(tenuti) >= tetto:
            break
    return tenuti


def _per_tipo(posizioni, brani_ref):
    def chiave(p):
        try:
            b = brani_ref[p]
            return _peso(b.get('ext') or os.path.splitext(b.get('nome') or '')[1][1:])
        except Exception:
            return 3
    return sorted(posizioni, key=chiave)


def _riga_scaletta(parti, parti_ext):
    import sys
    try:
        if sys._getframe(2).f_code.co_name != '_do_search':
            return
    except Exception:
        return
    for k in range(len(parti)):
        if not parti_ext[k]:
            parti[k] = ''


def apply():
    if _spenta():
        return False
    try:
        import moduli.libreria as lib
    except Exception:
        return False
    C = getattr(lib, 'LibreriaSlider', None)
    if C is None or not hasattr(C, '_cerca_in_tabella_016'):
        return False
    if getattr(C, '_ver258', None) == _VER:
        return True
    prima = getattr(C, '_o258_cerca', None) or C._cerca_in_tabella_016
    C._o258_cerca = prima

    def _cerca_in_tabella_016(self, parti, parti_ext, brani_ref, tetto):
        try:
            r = _cerca(self, parti, parti_ext, brani_ref, tetto * 4)
        except Exception:
            r = None
        if r is None:
            try:
                _prepara(self)
            except Exception:
                pass
            r = prima(self, parti, parti_ext, brani_ref, tetto * 10)
            return None if r is None else _per_tipo(r, brani_ref)[:tetto]
        _riga_scaletta(parti, parti_ext)
        return _una_volta(r, brani_ref, tetto)

    C._cerca_in_tabella_016 = _cerca_in_tabella_016

    if hasattr(C, '_debounce_suggerimenti'):
        prima_deb = getattr(C, '_o258_debounce', None) or C._debounce_suggerimenti
        C._o258_debounce = prima_deb

        def _debounce_suggerimenti(self, event=None):
            try:
                _prepara(self)
            except Exception:
                pass
            return prima_deb(self, event)

        C._debounce_suggerimenti = _debounce_suggerimenti

    C._ver258 = _VER
    print('[258] filtro: ricerca senza accenti e apostrofi, parole in qualsiasi ordine')
    return True


def revert():
    try:
        import moduli.libreria as lib
        C = lib.LibreriaSlider
        if hasattr(C, '_o258_cerca'):
            C._cerca_in_tabella_016 = C._o258_cerca
        if hasattr(C, '_o258_debounce'):
            C._debounce_suggerimenti = C._o258_debounce
        C._ver258 = None
        return True
    except Exception:
        return False


try:
    apply()
except Exception as _e:
    print('[258] %s' % _e)
