# 241 - regia: volume della base uguale per tutti i brani

import os
import threading
import time

_VER = 1
_TARGET = -11.0              # livello tipico delle basi (misurato: -14..-8,6, mediana ~-11,5): il totale non si abbassa
_MIN_DB, _MAX_DB = -10.0, 8.0
_ESTENSIONI = ('.mp3', '.mp4', '.wav', '.flac', '.m4a', '.ogg', '.wma', '.aac', '.mkv', '.avi', '.webm',
               '.mov', '.kfn', '.mpg', '.mpeg', '.flv', '.m4v', '.opus')
_LIBRERIE = []
_LOCK = threading.Lock()


def _titolare():
    """Solo sui PC del titolare: licenza FIRMATA intestata a Domenico Lembo (come la 233)."""
    try:
        from moduli.licensing import load_license
        d = load_license() or {}
        return (str(d.get('nome', '')).strip().lower(),
                str(d.get('cognome', '')).strip().lower()) == ('domenico', 'lembo')
    except Exception:
        return False


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_241', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def _log(msg):
    try:
        print('[241] %s' % msg)
    except Exception:
        pass


def _target():
    try:
        from moduli.database import Database
        return float(Database.get_config('regia_target_lufs', str(_TARGET)))
    except Exception:
        return _TARGET


# ------------------------------------------------------------------ cache delle misure
def _db():
    import sqlite3
    d = os.path.join(os.environ.get('LOCALAPPDATA') or os.path.expanduser('~'), 'KaraDom')
    os.makedirs(d, exist_ok=True)
    c = sqlite3.connect(os.path.join(d, 'regia.db'), timeout=10)
    c.execute('CREATE TABLE IF NOT EXISTS brani (chiave TEXT PRIMARY KEY, lufs REAL, quando REAL)')
    return c


def _chiave(path):
    try:
        st = os.stat(path)
        return '%s|%d|%d' % (os.path.normcase(os.path.normpath(path)), st.st_size, int(st.st_mtime))
    except Exception:
        return None


def _lufs_salvato(path):
    k = _chiave(path)
    if not k:
        return None, None
    try:
        with _LOCK:
            c = _db()
            r = c.execute('SELECT lufs FROM brani WHERE chiave=?', (k,)).fetchone()
            c.close()
        return k, (r[0] if r else None)
    except Exception:
        return k, None


def _misura(path):
    """LUFS con ffmpeg (processo a parte, priorita' bassa): il Python non lavora."""
    import json
    import subprocess
    try:
        from moduli.normalizzazione import _get_ffmpeg_path
        ff = _get_ffmpeg_path()
    except Exception:
        ff = 'ffmpeg'
    fl = getattr(subprocess, 'CREATE_NO_WINDOW', 0) | getattr(subprocess, 'BELOW_NORMAL_PRIORITY_CLASS', 0)
    r = subprocess.run([ff, '-hide_banner', '-nostats', '-vn', '-i', path, '-af', 'loudnorm=print_format=json',
                        '-f', 'null', '-'], capture_output=True, text=True, encoding='utf-8', errors='replace',
                       timeout=300, creationflags=fl)
    o = r.stderr or ''
    a, b = o.rfind('{'), o.rfind('}')
    if a < 0 or b <= a:
        return None
    v = float(json.loads(o[a:b + 1]).get('input_i', '-70'))
    return v if v > -60 else None


_IN_CORSO = set()


def _analizza(path):
    """Misura e salva (una volta sola per file). Ritorna i LUFS o None."""
    if not path or '://' in str(path) or os.path.splitext(str(path))[1].lower() not in _ESTENSIONI:
        return None
    k, v = _lufs_salvato(path)
    if v is not None or not k:
        return v
    if k in _IN_CORSO:
        return None
    _IN_CORSO.add(k)
    try:
        v = _misura(path)
        if v is not None:
            with _LOCK:
                c = _db()
                c.execute('INSERT OR REPLACE INTO brani VALUES (?,?,?)', (k, v, time.time()))
                c.commit()
                c.close()
        return v
    except Exception as e:
        _log('misura %s: %s' % (os.path.basename(str(path)), e))
        return None
    finally:
        _IN_CORSO.discard(k)


def _guadagno_db(lufs):
    return max(_MIN_DB, min(_MAX_DB, _target() - lufs))


# ------------------------------------------------------------------ in anticipo: i brani della scaletta
def _avvia_preparazione():
    def giro():
        time.sleep(20)
        while True:
            try:
                for lib in list(_LIBRERIE):
                    for r in list(getattr(lib, 'righe', None) or ()):
                        p = r.get('path') if isinstance(r, dict) else None
                        if p and os.path.isfile(p):
                            k, v = _lufs_salvato(p)
                            if k and v is None:
                                _analizza(p)
                                time.sleep(1)
            except Exception as e:
                _log('scaletta: %s' % e)
            time.sleep(15)
    threading.Thread(target=giro, daemon=True, name='regia241').start()


# ------------------------------------------------------------------ aggancio
def apply():
    if not _titolare():
        return False
    if _spenta():
        _log('spenta (patch_241=0)')
        return False
    try:
        import moduli.system as ms
        import moduli.libreria as ml
    except Exception as e:
        _log('moduli: %s' % e)
        return False
    S = ms.KaraokeMonitorSystem
    L = ml.LibreriaSlider
    if getattr(S, '_ver241', None) == _VER:
        return True

    # il volume che si sente = volume dell'utente x attenuazione del brano (solo se la base e' FORTE;
    # se e' bassa la alza la normalizzazione che c'e' gia', normalization_gain). Il cursore resta il suo.
    def _get(self):
        raw = self.__dict__.get('_uv241', self.__dict__.get('_user_volume', 1.0))
        out = raw * self.__dict__.get('_att241', 1.0)
        self.__dict__['_ultimo241'] = out
        return out

    def _set(self, v):
        try:
            v = float(v)
        except Exception:
            self.__dict__['_uv241'] = v
            return
        ultimo = self.__dict__.get('_ultimo241')
        if ultimo is not None and abs(v - ultimo) < 1e-9 and self.__dict__.get('_att241', 1.0) != 1.0:
            return                  # e' il valore attenuato appena letto (es. sottofondo): resta il grezzo
        self.__dict__['_uv241'] = v

    if not isinstance(S.__dict__.get('_user_volume'), property):
        S._user_volume = property(_get, _set)

    get0 = getattr(S, '_o241_get_volume', None) or S.get_volume
    S._o241_get_volume = get0

    def get_volume(self):
        return self.__dict__.get('_uv241', self.__dict__.get('_user_volume', 1.0))

    set0 = getattr(S, '_o241_set_volume', None) or S.set_volume
    S._o241_set_volume = set0

    def set_volume(self, volume):
        try:
            raw = max(0.0, min(1.0, float(volume)))
        except Exception:
            return set0(self, volume)
        r = set0(self, raw * self.__dict__.get('_att241', 1.0))
        self.__dict__['_uv241'] = raw          # il cursore resta quello dell'utente
        return r

    load0 = getattr(S, '_o241_load', None) or S.load_file
    S._o241_load = load0

    def _applica(self, path, lufs, subito):
        g = _guadagno_db(lufs)
        if g >= 0:
            self.__dict__['_att241'] = 1.0
            self.normalization_enabled = True
            self.normalization_gain = 10 ** (g / 20.0)
        else:
            self.__dict__['_att241'] = 10 ** (g / 20.0)
            self.normalization_gain = 1.0
        _log('%s: %.1f LUFS -> base %+.1f dB' % (os.path.basename(str(path)), lufs, g))
        if subito:
            try:
                set_volume(self, self.__dict__.get('_uv241', 1.0))
            except Exception:
                pass

    def load_file(self, *a, **k):
        r = load0(self, *a, **k)
        try:
            self.__dict__['_att241'] = 1.0
            path = getattr(self, '_original_file', None) or getattr(self, 'current_file', None)
            if path and not getattr(self, '_bu_carica_sottofondo', False):
                _k, v = _lufs_salvato(path)
                if v is not None:
                    _applica(self, path, v, False)
                else:
                    # non ancora misurato: si misura adesso; se arriva entro 4 s dall'inizio si applica,
                    # altrimenti vale dalla prossima volta
                    t0 = time.time()
                    gen = self.__dict__['_gen241'] = self.__dict__.get('_gen241', 0) + 1

                    def dopo(p=path):
                        v2 = _analizza(p)
                        if v2 is None or self.__dict__.get('_gen241') != gen or time.time() - t0 > 4:
                            return
                        try:
                            self.master.after(0, lambda: _applica(self, p, v2, True))
                        except Exception:
                            pass
                    threading.Thread(target=dopo, daemon=True, name='regia241m').start()
        except Exception as e:
            _log('load: %s' % e)
        return r

    init0 = getattr(L, '_o241_init', None) or L.__init__
    L._o241_init = init0

    def l_init(self, *a, **k):
        init0(self, *a, **k)
        _LIBRERIE.append(self)

    S.get_volume = get_volume
    S.set_volume = set_volume
    S.load_file = load_file
    L.__init__ = l_init
    S._ver241 = _VER
    _avvia_preparazione()
    _log('volume base automatico: tutti i brani a %.0f LUFS (da %+.0f a %+.0f dB)' % (_target(), _MIN_DB, _MAX_DB))
    return True


def revert():
    return False
