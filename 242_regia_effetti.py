# 242 - regia effetti

import os
import threading
import math
import socket
import time

PORTA = 10024
TIPO_DELAY = 26          # Modulation Delay
TIPO_RIVERBERO = 22      # Chorus + Chamber


# ------------------------------------------------------------------ OSC minimo (niente dipendenze)
def _s(t):
    b = t.encode("latin-1", "replace") + b"\x00"
    return b + b"\x00" * ((4 - len(b) % 4) % 4)


def _osc(addr, *a):
    import struct
    tag, dati = ",", b""
    for v in a:
        if isinstance(v, int):
            tag += "i"
            dati += struct.pack(">i", v)
        elif isinstance(v, float):
            tag += "f"
            dati += struct.pack(">f", v)
        else:
            tag += "s"
            dati += _s(str(v))
    return _s(addr) + _s(tag) + dati


def _leggi_risposta(p):
    import struct
    try:
        e = p.index(b"\x00")
        i = (e + 4) & ~3
        te = p.index(b"\x00", i)
        tags = p[i + 1:te].decode()
        j = (te + 4) & ~3
        if tags[:1] == "i":
            return struct.unpack(">i", p[j:j + 4])[0]
        if tags[:1] == "f":
            return struct.unpack(">f", p[j:j + 4])[0]
        if tags[:1] == "s":
            return p[j:p.index(b"\x00", j)].decode("latin-1")
    except Exception:
        pass
    return None


class Mixer:
    def __init__(self, ip):
        self.ip = ip
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.settimeout(0.5)

    def get(self, addr):
        for _ in range(2):
            try:
                self.s.sendto(_osc(addr), (self.ip, PORTA))
                t0 = time.time()
                while time.time() - t0 < 0.5:
                    d = self.s.recv(4096)
                    if d.startswith(_s(addr)):
                        return _leggi_risposta(d)
            except Exception:
                pass
        return None

    def set(self, addr, v):
        try:
            self.s.sendto(_osc(addr, v), (self.ip, PORTA))
            time.sleep(0.003)
        except Exception:
            pass

    def chiudi(self):
        try:
            self.s.close()
        except Exception:
            pass


# ------------------------------------------------------------------ scale
def n_freq(f):
    return max(0.0, min(1.0, math.log(f / 20.0) / math.log(1000.0)))


def n_gain(db):
    return max(0.0, min(1.0, (db + 15.0) / 30.0))


def n_q(q):
    return max(0.0, min(1.0, math.log(q / 10.0) / math.log(0.03)))


def n_fader(db):
    if db <= -90.0:
        return 0.0
    if db < -60.0:
        return (db + 90.0) / 480.0
    if db < -30.0:
        return (db + 70.0) / 160.0
    if db < -10.0:
        return (db + 50.0) / 80.0
    return min(1.0, (db + 30.0) / 40.0)


def n_delay_ms(ms):
    return max(0.0, min(1.0, (ms - 1.0) / 2999.0))


def n_decay_s(s):
    return max(0.0, min(1.0, math.log(max(0.1, s) / 0.1) / math.log(50.0)))


# ------------------------------------------------------------------ chi e' chi sul mixer
def microfoni(m):
    """I canali dei cantanti: nome che comincia per 'Mic' (Mic Dom, Mic Giallo ...)."""
    out = []
    for c in range(1, 17):
        n = m.get("/ch/%02d/config/name" % c)
        if isinstance(n, str) and n.strip().lower().startswith("mic"):
            out.append(c)
    return out


def canali_base(m):
    """I canali della base che arriva dal PC: ritorno USB acceso, NON microfoni, e IN USO (fader sopra
    -45 dB e canale acceso). [24-10] prima prendeva anche 6, 9, 10 (USB acceso ma spenti/a -oo) e li alzava."""
    out = []
    for c in range(1, 17):
        b = "/ch/%02d" % c
        if m.get(b + "/preamp/rtnsw") != 1:
            continue
        nome = m.get(b + "/config/name")
        if isinstance(nome, str) and nome.strip().lower().startswith("mic"):
            continue
        f = m.get(b + "/mix/fader")
        if f is None or db_fader(f) <= -45.0 or not m.get(b + "/mix/on"):
            continue
        out.append(c)
    return out


def db_fader(n):
    n = max(0.0, min(1.0, float(n)))
    if n >= 0.5:
        return n * 40.0 - 30.0
    if n >= 0.25:
        return n * 80.0 - 50.0
    if n >= 0.0625:
        return n * 160.0 - 70.0
    return n * 480.0 - 90.0 if n > 0 else -90.0


def effetti(m):
    """{'riverbero': [k...], 'delay': [k...]} dai tipi caricati negli slot FX 1-4."""
    out = {"riverbero": [], "delay": []}
    for k in range(1, 5):
        t = m.get("/fx/%d/type" % k)
        if t == TIPO_RIVERBERO:
            out["riverbero"].append(k)
        elif t == TIPO_DELAY:
            out["delay"].append(k)
    return out


# ------------------------------------------------------------------ 1) impostazione di partenza
BASE = {"riverbero_db": -6.0, "delay_db": -18.0, "presenza_db": 2.0}   # = il MINIMO per tutti i brani: il brano puo' solo aggiungere


def configura(ip, log=print):
    m = Mixer(ip)
    try:
        mic = microfoni(m)
        fx = effetti(m)
        riv = fx["riverbero"][:1]          # un solo riverbero sulla voce (due insieme impastano)
        dly = fx["delay"][:1]
        for c in mic:
            b = "/ch/%02d" % c
            m.set(b + "/preamp/hpon", 1)
            m.set(b + "/preamp/hpf", float(math.log(100 / 20.0) / math.log(20.0)))     # 100 Hz
            m.set(b + "/gate/on", 0)
            m.set(b + "/dyn/on", 1)
            m.set(b + "/dyn/mode", 0)
            m.set(b + "/dyn/thr", float((-18.0 + 60.0) / 60.0))
            m.set(b + "/dyn/ratio", 5)                                                  # 3:1
            m.set(b + "/dyn/knee", 0.4)
            m.set(b + "/dyn/attack", float(10 / 120.0))
            m.set(b + "/dyn/release", float(math.log(150 / 5.0) / math.log(800.0)))
            m.set(b + "/dyn/mgain", float(3.0 / 24.0))
            m.set(b + "/dyn/mix", 1.0)
            m.set(b + "/eq/on", 1)
            for k, (tipo, f, g, q) in enumerate(((2, 250, -2.0, 1.4), (2, 800, 0.0, 1.4),
                                                 (2, 3000, BASE["presenza_db"], 1.4), (4, 10000, 1.5, 0.7)), 1):
                m.set(b + "/eq/%d/type" % k, tipo)
                m.set(b + "/eq/%d/f" % k, float(n_freq(f)))
                m.set(b + "/eq/%d/g" % k, float(n_gain(g)))
                m.set(b + "/eq/%d/q" % k, float(n_q(q)))
            for k in range(1, 5):
                lv = BASE["riverbero_db"] if k in riv else (BASE["delay_db"] if k in dly else -90.0)
                m.set(b + "/mix/%02d/level" % (6 + k), float(n_fader(lv)))
                m.set(b + "/mix/%02d/tap" % (6 + k), 4)                                  # post fader
        for k in range(1, 5):
            if k in riv:
                m.set("/rtn/%d/mix/fader" % k, float(n_fader(-3.0)))
                m.set("/rtn/%d/mix/on" % k, 1)
                m.set("/fx/%d/par/08" % k, float(n_decay_s(1.8)))
            elif k in dly:
                m.set("/rtn/%d/mix/fader" % k, float(n_fader(-6.0)))
                m.set("/rtn/%d/mix/on" % k, 1)
        log("configurato: microfoni %s, riverbero FX%s, delay FX%s" % (mic, riv, dly))
        return {"mic": mic, "riverbero": riv, "delay": dly}
    finally:
        m.chiudi()


# ------------------------------------------------------------------ 2) a ogni brano
def scelte(a):
    """a: {'bpm', 'dens', 'br'} -> cosa fare (numeri leggibili)."""
    dens, bpm, br = a.get("dens"), a.get("bpm"), a.get("br")
    carattere = "medio" if dens is None else ("ballata" if dens < 2.2 else ("veloce" if dens > 3.6 else "medio"))
    out = {"carattere": carattere,
           "decay_s": {"ballata": 2.6, "medio": 1.8, "veloce": 1.2}[carattere],
           "riverbero_db": BASE["riverbero_db"] + {"ballata": 2.0, "medio": 1.0, "veloce": 0.0}[carattere],
           "delay_db": BASE["delay_db"] + {"ballata": 3.0, "medio": 1.5, "veloce": 0.0}[carattere],
           "presenza_db": BASE["presenza_db"] + (0.0 if br is None else (1.5 if br < 0.08 else (-1.5 if br > 0.18 else 0.0)))}
    if a.get("pianobar"):
        out["carattere"] += " piano bar"
        out["decay_s"] = min(3.2, out["decay_s"] + 0.6)
        out["riverbero_db"] += 1.0
        out["delay_db"] -= 4.0
    if bpm:
        ms = 60000.0 / bpm
        while ms > 1000:          # sopra il secondo la ripetizione si perde: un ottavo
            ms /= 2.0
        out["delay_ms"] = round(ms)
    return out


def brano(ip, a, log=print):
    sc = scelte(a)
    m = Mixer(ip)
    try:
        mic = microfoni(m)
        fx = effetti(m)
        riv, dly = fx["riverbero"][:1], fx["delay"][:1]
        for k in riv:
            m.set("/fx/%d/par/08" % k, float(n_decay_s(sc["decay_s"])))
        for k in dly:
            if "delay_ms" in sc:
                m.set("/fx/%d/par/01" % k, float(n_delay_ms(sc["delay_ms"])))
        for c in mic:
            b = "/ch/%02d" % c
            for k in riv:
                m.set(b + "/mix/%02d/level" % (6 + k), float(n_fader(sc["riverbero_db"])))
            for k in dly:
                m.set(b + "/mix/%02d/level" % (6 + k), float(n_fader(sc["delay_db"])))
            m.set(b + "/eq/3/g", float(n_gain(sc["presenza_db"])))
        log("brano %s: delay %s ms, riverbero %.1f s, voce->riverbero %+.0f dB, voce->delay %+.0f dB, presenza %+.1f dB"
            % (sc["carattere"], sc.get("delay_ms", "-"), sc["decay_s"], sc["riverbero_db"], sc["delay_db"],
               sc["presenza_db"]))
        return sc
    finally:
        m.chiudi()


# ------------------------------------------------------------------ analisi del brano (ffmpeg + numpy)
def analizza(path, ffmpeg="ffmpeg", sr=11025):
    import subprocess
    import numpy as np
    fl = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0)

    def pcm(inizio):
        r = subprocess.run([ffmpeg, "-hide_banner", "-nostats", "-ss", str(inizio), "-t", "90", "-vn", "-i", path,
                            "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"], capture_output=True, timeout=120,
                           creationflags=fl)
        return np.frombuffer(r.stdout, dtype=np.int16).astype(np.float32) / 32768.0
    x = pcm(30)
    if x.size < sr * 10:
        x = pcm(0)
    if x.size < sr * 8:
        return {}
    hop, win = 128, 1024
    n = 1 + (x.size - win) // hop
    idx = np.arange(win)[None, :] + hop * np.arange(n)[:, None]
    S = np.abs(np.fft.rfft(x[idx] * np.hanning(win)[None, :], axis=1))
    f = np.fft.rfftfreq(win, 1.0 / sr)
    bordi = np.geomspace(40, 5000, 25)
    B = np.stack([S[:, (f >= a) & (f < b)].sum(axis=1) for a, b in zip(bordi[:-1], bordi[1:])], axis=1)
    fl_ = np.maximum(0, np.diff(np.log1p(B * 50), axis=0)).sum(axis=1)
    fl_ = np.maximum(fl_ - np.convolve(fl_, np.ones(32) / 32, mode="same"), 0)
    fps = sr / hop
    # densita' dei colpi (ballata / veloce)
    o = fl_
    picchi = ((o[1:-1] > o[:-2]) & (o[1:-1] > o[2:]) & (o[1:-1] > o.mean() + o.std())).sum()
    dens = float(picchi / (x.size / sr))
    # BPM: autocorrelazione con armoniche e preferenza intorno a 110 (banco 113 brani: come librosa)
    oz = (o - o.mean()) / (o.std() + 1e-9)
    ac = np.correlate(oz, oz, mode="full")[oz.size - 1:]
    ac /= ac[0] + 1e-9
    bpms = np.arange(55.0, 210.0, 0.5)
    lag = 60.0 * fps / bpms

    def val(l):
        i = np.floor(l).astype(int)
        fr = l - i
        ok = i + 1 < ac.size
        v = np.zeros_like(l)
        v[ok] = ac[i[ok]] * (1 - fr[ok]) + ac[i[ok] + 1] * fr[ok]
        return v
    sc = val(lag) + 0.5 * val(2 * lag) + 0.25 * val(4 * lag) + 0.3 * val(3 * lag)
    prior = np.exp(-0.5 * (np.log2(bpms / 110.0) / 0.7) ** 2)
    bpm = float(bpms[int(np.argmax(sc * prior))])
    br = float(S[:, f > 2000].sum() / (S.sum() + 1e-9))
    out = {"bpm": round(bpm, 1), "dens": round(dens, 2), "br": round(br, 3)}
    # tonalita' della base (cromagramma + profili di Krumhansl): serve a intonatore e armonie
    try:
        sel = (f >= 55) & (f <= 2000)
        pc = np.round(12 * np.log2(f[sel] / 440.0)).astype(int) % 12
        energia = (S[:, sel] ** 2).sum(axis=0)
        croma = np.bincount((pc + 9) % 12, weights=energia, minlength=12)     # 0 = Do
        mag = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
        mi = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
        prove = []
        for tn in range(12):
            for modo, prof in ((0, mag), (1, mi)):
                prove.append((float(np.corrcoef(croma, np.roll(prof, tn))[0, 1]), tn, modo))
        prove.sort(reverse=True)
        out["tonica"], out["modo"], out["fiducia"] = prove[0][1], prove[0][2], round(prove[0][0], 3)
    except Exception:
        pass
    # volume percepito del brano (LUFS, come la 241)
    try:
        import json
        r = subprocess.run([ffmpeg, "-hide_banner", "-nostats", "-vn", "-i", path, "-af", "loudnorm=print_format=json",
                            "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=300, creationflags=fl)
        o = r.stderr or ""
        v = float(json.loads(o[o.rfind("{"):o.rfind("}") + 1]).get("input_i", "-70"))
        if v > -60:
            out["lufs"] = round(v, 1)
    except Exception:
        pass
    return out


# ================================================================== aggancio a KaraDom
_VER = 10
_LOCK = threading.Lock()
_STATO = {"ip": None, "t": 0.0, "gen": 0}


def _titolare():
    """Solo sui PC del titolare: licenza FIRMATA intestata a Domenico Lembo (come la 233/241)."""
    try:
        from moduli.licensing import load_license
        d = load_license() or {}
        return (str(d.get('nome', '')).strip().lower(),
                str(d.get('cognome', '')).strip().lower()) == ('domenico', 'lembo')
    except Exception:
        return False


def _config(k, d):
    try:
        from moduli.database import Database
        return Database.get_config(k, d)
    except Exception:
        return d


def _log(msg):
    try:
        print('[242] %s' % msg)
        d = os.path.join(os.environ.get('LOCALAPPDATA') or os.path.expanduser('~'), 'KaraDom')
        with open(os.path.join(d, 'regia_effetti.log'), 'a', encoding='utf-8') as f:
            f.write('%s %s\n' % (time.strftime('%d-%m %H:%M:%S'), msg))
    except Exception:
        pass


def _risponde(ip):
    m = Mixer(ip)
    try:
        return m.get('/-snap/index') is not None
    finally:
        m.chiudi()


def _diretto():
    """Mixer col cavo diretto (169.254.x.x): broadcast da ogni scheda 169.254 del PC."""
    try:
        locali = [i[4][0] for i in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)
                  if i[4][0].startswith('169.254.')]
    except Exception:
        locali = []
    for loc in locali:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            s.bind((loc, 0))
            s.settimeout(0.8)
            s.sendto(_osc('/xinfo'), ('169.254.255.255', PORTA))
            d, a = s.recvfrom(2048)
            if d.startswith(_s('/xinfo')):
                return a[0]
        except Exception:
            pass
        finally:
            s.close()
    return None


def _ip_mixer():
    if _STATO['ip'] and time.time() - _STATO['t'] < 120:
        return _STATO['ip']
    prove = [str(_config(k, '') or '').strip() for k in ('console_xr18_ip', 'xr18_ip', 'xr18_ip_found')]
    if _STATO['ip']:
        prove.insert(0, _STATO['ip'])
    ip = next((p for p in prove if p and _risponde(p)), None) or _diretto()
    if not ip:
        try:
            from moduli.cuffia_guida import discover_xr18
            ip = discover_xr18()
        except Exception:
            ip = None
    _STATO['ip'], _STATO['t'] = ip, time.time()
    return ip


def _db():
    import sqlite3
    d = os.path.join(os.environ.get('LOCALAPPDATA') or os.path.expanduser('~'), 'KaraDom')
    os.makedirs(d, exist_ok=True)
    c = sqlite3.connect(os.path.join(d, 'regia.db'), timeout=10)
    c.execute('CREATE TABLE IF NOT EXISTS effetti (chiave TEXT PRIMARY KEY, bpm REAL, dens REAL, br REAL, quando REAL)')
    for col in ('lufs REAL', 'tonica INTEGER', 'modo INTEGER', 'fiducia REAL'):
        try:
            c.execute('ALTER TABLE effetti ADD COLUMN ' + col)
        except Exception:
            pass
    c.execute('CREATE TABLE IF NOT EXISTS base (canale INTEGER PRIMARY KEY, db REAL)')
    return c


def _chiave(path):
    try:
        st = os.stat(path)
        return '%s|%d|%d' % (os.path.normcase(os.path.normpath(path)), st.st_size, int(st.st_mtime))
    except Exception:
        return None


def _analisi(path):
    k = _chiave(path)
    if not k:
        return None
    with _LOCK:
        c = _db()
        r = c.execute('SELECT bpm, dens, br, lufs, tonica, modo, fiducia FROM effetti WHERE chiave=?',
                      (k,)).fetchone()
        c.close()
    if r and r[3] is not None and r[4] is not None:
        return {'bpm': r[0], 'dens': r[1], 'br': r[2], 'lufs': r[3], 'tonica': r[4], 'modo': r[5], 'fiducia': r[6]}
    try:
        from moduli.normalizzazione import _get_ffmpeg_path
        ff = _get_ffmpeg_path()
    except Exception:
        ff = 'ffmpeg'
    a = analizza(path, ff)
    if a:
        with _LOCK:
            c = _db()
            c.execute('INSERT OR REPLACE INTO effetti (chiave, bpm, dens, br, quando, lufs, tonica, modo, fiducia) '
                      'VALUES (?,?,?,?,?,?,?,?,?)', (k, a.get('bpm'), a.get('dens'), a.get('br'), time.time(),
                                                     a.get('lufs'), a.get('tonica'), a.get('modo'), a.get('fiducia')))
            c.commit()
            c.close()
    return a


_EST = ('.mp3', '.mp4', '.wav', '.flac', '.m4a', '.ogg', '.wma', '.aac', '.mkv', '.avi', '.webm', '.mov',
        '.kfn', '.mpg', '.mpeg', '.m4v', '.opus')


_ULTIMO = {}          # canale -> ultimo dB messo da noi (per capire se l'utente l'ha spostato a mano)
_OFFSET = {'db': 0.0}


def _volume_base(ip, lufs, nome, sistema):
    """Fader dei canali della base = misura dell'utente + correzione del brano (LUFS verso -11).
    Se tra un brano e l'altro l'utente ha spostato il fader, quella diventa la sua nuova misura."""
    try:
        target = float(_config('regia_target_lufs', '-11'))
    except Exception:
        target = -11.0
    corr = max(-10.0, min(8.0, target - lufs))
    if pb_acceso():
        corr -= 6.0                                          # piano bar: base piu' bassa
    m = Mixer(ip)
    try:
        canali = canali_base(m)
        if not canali:
            return
        with _LOCK:
            c = _db()
            base = dict(c.execute('SELECT canale, db FROM base').fetchall())
            # [24-10] si leggono TUTTI i fader prima di scriverne uno: 15-16 sono collegati (link) e
            # scrivendo il 15 cambiava anche il 16 -> la sua "misura" risultava gia' corretta (doppia)
            letti = {ch: m.get('/ch/%02d/mix/fader' % ch) for ch in canali}
            for ch in canali:
                ora = letti[ch]
                if ora is None:
                    continue
                ora_db = db_fader(ora)
                if ch not in base:
                    base[ch] = ora_db                                # la prima volta: com'e' adesso
                elif ch in _ULTIMO and abs(ora_db - _ULTIMO[ch]) > 0.6:
                    base[ch] = ora_db - _OFFSET['db']                # spostato a mano: impara
                nuovo = max(-60.0, min(10.0, base[ch] + corr))
                m.set('/ch/%02d/mix/fader' % ch, float(n_fader(nuovo)))
                _ULTIMO[ch] = nuovo
                _AGC['fader'][ch] = nuovo                    # la regia dei microfoni segue la base nuova
                c.execute('INSERT OR REPLACE INTO base VALUES (?,?)', (ch, base[ch]))
            c.commit()
            c.close()
        _OFFSET['db'] = corr
        _log('%s | base %.1f LUFS -> fader %+.1f dB (canali %s, misura tua %s)'
             % (nome, lufs, corr, canali, ', '.join('%.1f' % base[c] for c in canali if c in base)))
        # la correzione la fa il mixer: quella dentro KaraDom (241) si toglie, se no si raddoppia
        if sistema is not None:
            def togli241():
                try:
                    sistema.__dict__['_gen241'] = sistema.__dict__.get('_gen241', 0) + 1
                    sistema.__dict__['_att241'] = 1.0
                    sistema.normalization_gain = 1.0
                    sistema.set_volume(sistema.get_volume())
                except Exception:
                    pass
            try:
                sistema.master.after(0, togli241)
            except Exception:
                togli241()
    finally:
        m.chiudi()


NOTE = ['Do', 'Do#', 'Re', 'Mib', 'Mi', 'Fa', 'Fa#', 'Sol', 'Lab', 'La', 'Sib', 'Si']


def _per_gli_effetti(path, a, sc):
    """Il brano per i NOSTRI effetti voce (Mixer XR18): tonalita', tempo, carattere."""
    try:
        import json
        d = os.path.join(os.environ.get('LOCALAPPDATA') or os.path.expanduser('~'), 'KaraDom')
        j = {'t': time.time(), 'brano': os.path.basename(path), 'tonica': a.get('tonica'), 'modo': a.get('modo'),
             'fiducia': a.get('fiducia'), 'bpm': a.get('bpm'), 'delay_ms': (sc or {}).get('delay_ms'),
             'carattere': (sc or {}).get('carattere')}
        tmp = os.path.join(d, 'regia_brano.json.tmp')
        json.dump(j, open(tmp, 'w', encoding='utf-8'))
        os.replace(tmp, os.path.join(d, 'regia_brano.json'))
        if a.get('tonica') is not None:
            _log('%s | tonalita %s %s (fiducia %.2f)' % (os.path.basename(path), NOTE[int(a['tonica']) % 12],
                                                        'minore' if a.get('modo') == 1 else 'maggiore',
                                                        a.get('fiducia') or 0))
    except Exception as e:
        _log('effetti voce: %s' % e)


# ------------------------------------------------------------------ PIANO BAR
# [24-10] utente: "un bottone generale" (non per brano). Acceso: base piu' bassa (-6 dB), voce piu' avanti
# (+3 dB nell'equilibrio voce/base), effetti piu' caldi, e la base abbassata di tono con una regola FISSA
# PER BRANO: -1 semitono di partenza; MIDI: dalla nota alta della melodia (fino a -3, oppure 0 se e' gia'
# bassa); se l'utente cambia tono su un brano in piano bar, quel valore resta per quel brano.
def _pb_file():
    return os.path.join(os.environ.get('LOCALAPPDATA') or os.path.expanduser('~'), 'KaraDom', 'pianobar.json')


def pb_acceso():
    try:
        import json
        return bool(json.load(open(_pb_file(), encoding='utf-8')).get('on'))
    except Exception:
        return False


def _pb_metti(on):
    import json
    try:
        json.dump({'on': bool(on), 't': time.time()}, open(_pb_file(), 'w', encoding='utf-8'))
    except Exception:
        pass


def _pb_ricordato(path, semitoni=None):
    k = os.path.normcase(os.path.normpath(str(path)))
    with _LOCK:
        c = _db()
        c.execute('CREATE TABLE IF NOT EXISTS pianobar (brano TEXT PRIMARY KEY, semitoni INTEGER)')
        if semitoni is None:
            r = c.execute('SELECT semitoni FROM pianobar WHERE brano=?', (k,)).fetchone()
            c.close()
            return None if r is None else int(r[0])
        c.execute('INSERT OR REPLACE INTO pianobar VALUES (?,?)', (k, int(semitoni)))
        c.commit()
        c.close()


def _melodia_alta(path):
    """Nota alta (95 percentile) della melodia di un MIDI: canale non batteria con tante note e
    altezza da voce (mediana piu' vicina a Sol 4). None se non si capisce."""
    import struct
    try:
        d = open(path, 'rb').read()
        if d[:4] != b'MThd':
            return None
        note = {}
        pos = 14
        while pos + 8 <= len(d):
            tipo, ln = d[pos:pos + 4], struct.unpack('>I', d[pos + 4:pos + 8])[0]
            corpo = d[pos + 8:pos + 8 + ln]
            pos += 8 + ln
            if tipo != b'MTrk':
                continue
            i, run = 0, None
            while i < len(corpo):
                while corpo[i] & 0x80:
                    i += 1
                i += 1
                st = corpo[i]
                if st == 0xFF:
                    i += 2
                    L = 0
                    while True:
                        b = corpo[i]
                        i += 1
                        L = (L << 7) | (b & 0x7f)
                        if not b & 0x80:
                            break
                    i += L
                    continue
                if st in (0xF0, 0xF7):
                    i += 1
                    L = 0
                    while True:
                        b = corpo[i]
                        i += 1
                        L = (L << 7) | (b & 0x7f)
                        if not b & 0x80:
                            break
                    i += L
                    continue
                if st & 0x80:
                    run = st
                    i += 1
                if run is None:
                    break
                n = 1 if (run & 0xF0) in (0xC0, 0xD0) else 2
                if (run & 0xF0) == 0x90 and corpo[i + 1] > 0 and (run & 0x0F) != 9:
                    note.setdefault(run & 0x0F, []).append(corpo[i])
                i += n
        migliore = None
        for ch, v in note.items():
            if len(v) < 50:
                continue
            v = sorted(v)
            med = v[len(v) // 2]
            if 55 <= med <= 79 and (migliore is None or abs(med - 67) < abs(migliore[0] - 67)):
                migliore = (med, v[int(len(v) * 0.95)])
        return migliore[1] if migliore else None
    except Exception:
        return None


def pb_semitoni(path):
    """Di quanto abbassare il brano in piano bar (numero negativo o 0)."""
    r = _pb_ricordato(path)
    if r is not None:
        return r
    if os.path.splitext(str(path))[1].lower() in ('.mid', '.midi', '.kar'):
        alta = _melodia_alta(path)
        if alta is not None:
            return -3 if alta >= 77 else (-2 if alta >= 74 else (-1 if alta >= 69 else 0))
    return -1


def _pb_bottone():
    """Il bottone PB accanto a MIX (stesso modo della 233: si aggancia alla nascita del bottone SYN)."""
    try:
        import moduli.glow_button as gb
    except Exception:
        return
    G = gb.GlowButton
    if getattr(G, '_pb242', False):
        return
    prima = G.__init__

    def __init__(self, *a, **kw):
        prima(self, *a, **kw)
        try:
            if kw.get('text') != 'SYN' or getattr(self, '_pb242b', None) is not None:
                return
            colore = lambda: '#ff9f1c' if pb_acceso() else '#4a4a4a'
            pb = []

            def premi():
                on = not pb_acceso()
                _pb_metti(on)
                pb[0].configure(fg_color=colore())
                _log('PIANO BAR %s' % ('ACCESO' if on else 'spento'))
                cur = _STATO.get('ultimo_brano')
                if cur:
                    _al_brano(cur[0], cur[1])            # volumi ed effetti subito; il tono dal brano dopo
            b = G(self.master, text='PB', command=premi, width=kw.get('width'), height=kw.get('height'),
                  corner_radius=kw.get('corner_radius'), font_delta=kw.get('font_delta', -2),
                  fg_color=colore(), text_color='white', font=kw.get('font'), icons=False)
            pb.append(b)
            self._pb242b = b
            pack0 = self.pack

            def pack(*pa, **pk):
                r = pack0(*pa, **pk)
                try:
                    b.pack(side=pk.get('side', 'left'), padx=pk.get('padx', 4))
                except Exception:
                    pass
                return r
            self.pack = pack
            try:
                from moduli.ui import add_tooltip
                add_tooltip(b, 'PIANO BAR: base piu\' bassa e abbassata di tono, voce avanti, effetti caldi')
            except Exception:
                pass
        except Exception as e:
            _log('bottone PB: %s' % e)
    G.__init__ = __init__
    G._pb242 = True


def _al_brano(path, sistema=None):
    _STATO['ultimo_brano'] = (path, sistema)
    gen = _STATO['gen'] = _STATO['gen'] + 1
    _agc_inizio_brano()

    def lavora():
        try:
            time.sleep(0.5)
            if _STATO['gen'] != gen:
                return                       # nel frattempo e' partito un altro brano
            ip = _ip_mixer()
            if not ip:
                _log('mixer non trovato: niente regia effetti')
                return
            a = _analisi(path)
            if not a or _STATO['gen'] != gen:
                return
            a = dict(a, pianobar=pb_acceso())
            sc = brano(ip, a, log=lambda t: _log('%s | %s' % (os.path.basename(path), t)))
            _per_gli_effetti(path, a, sc)
            if a.get('lufs') is not None:
                _volume_base(ip, a['lufs'], os.path.basename(path), sistema)
        except Exception as e:
            _log('errore: %s' % e)
    threading.Thread(target=lavora, daemon=True, name='regia242').start()


# ------------------------------------------------------------------ volume automatico dei microfoni
# [24-10] VERIFICATO sul ferro: i livelli /meters/1 dei canali sono PRIMA del fader (ch15 -30 dB, fader
# -21, Main -50). Quindi il contributo di una voce = livello + fader, e quello della base idem.
# Si tiene l'equilibrio voce/base che usa l'utente (imparato), la voce segue la base del brano;
# duetto/gruppo: ogni voce attiva scende di 10*log10(N) cosi' la somma resta come una voce sola.
_AGC = {'margine': None, 'imparo': [], 'fader': {}, 'messo': {}, 'partenza': {}, 'canali': None, 't_canali': 0}


def _suona():
    try:
        import json
        d = os.path.join(os.environ.get('LOCALAPPDATA') or os.path.expanduser('~'), 'KaraDom', 'studio_bridge.json')
        j = json.load(open(d, encoding='utf-8'))
        return bool(j.get('playing')) and time.time() - float(j.get('ts', 0)) < 3
    except Exception:
        return False


def _margine_salvato(v=None):
    with _LOCK:
        c = _db()
        c.execute('CREATE TABLE IF NOT EXISTS agc (chiave TEXT PRIMARY KEY, valore REAL)')
        if v is None:
            r = c.execute("SELECT valore FROM agc WHERE chiave='margine'").fetchone()
            c.close()
            return r[0] if r else None
        c.execute("INSERT OR REPLACE INTO agc VALUES ('margine', ?)", (float(v),))
        c.commit()
        c.close()


def _mic_base(ch, v=None):
    """La posizione del fader del microfono scelta dall'utente (i limiti -8/+3 valgono da QUI, sempre).
    [24-10] prima la 'partenza' si rifaceva a ogni brano e i limiti si sommavano: mic1 +7 dB."""
    with _LOCK:
        c = _db()
        c.execute('CREATE TABLE IF NOT EXISTS agc (chiave TEXT PRIMARY KEY, valore REAL)')
        k = 'mic%02d' % ch
        if v is None:
            r = c.execute('SELECT valore FROM agc WHERE chiave=?', (k,)).fetchone()
            c.close()
            return r[0] if r else None
        c.execute('INSERT OR REPLACE INTO agc VALUES (?, ?)', (k, float(v)))
        c.commit()
        c.close()


def _agc_inizio_brano():
    _AGC['messo'] = {}
    _AGC['t_canali'] = 0


def _agc_giro():
    import struct
    from collections import deque
    storia = {}
    base_storia = deque()
    s = None
    ultimo_abbonamento = 0.0
    ultimo_passo = 0.0
    while True:
        try:
            if str(_config('regia_agc', '1')).strip() in ('0', 'no', 'off') or not _suona():
                time.sleep(0.5)
                continue
            ip = _ip_mixer()
            if not ip:
                time.sleep(2)
                continue
            if s is None:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.settimeout(0.3)
            adesso = time.time()
            if adesso - ultimo_abbonamento > 8:
                s.sendto(_osc('/meters', '/meters/1'), (ip, PORTA))
                ultimo_abbonamento = adesso
            if _AGC['canali'] is None or adesso - _AGC['t_canali'] > 30:
                m = Mixer(ip)
                try:
                    _AGC['canali'] = (microfoni(m), canali_base(m))
                    for ch in _AGC['canali'][0] + _AGC['canali'][1]:
                        v = m.get('/ch/%02d/mix/fader' % ch)
                        if v is not None:
                            _AGC['fader'][ch] = db_fader(v)
                finally:
                    m.chiudi()
                _AGC['t_canali'] = adesso
                if _AGC['margine'] is None:
                    _AGC['margine'] = _margine_salvato()
            try:
                d = s.recv(65535)
            except socket.timeout:
                continue
            if not d.startswith(_s('/meters/1')):
                continue
            j = d.index(b',b') + 4
            n = struct.unpack('>i', d[j:j + 4])[0]
            blob = d[j + 4:j + 4 + n]
            k = struct.unpack('<i', blob[:4])[0]
            liv = [x / 256.0 for x in struct.unpack('<%dh' % k, blob[4:4 + 2 * k])]
            mic, base = _AGC['canali']
            if not mic or not base:
                continue
            for ch in mic:
                q = storia.setdefault(ch, deque())
                q.append((adesso, liv[ch - 1]))
                while q and adesso - q[0][0] > 3:
                    q.popleft()
            b_lv = max(liv[ch - 1] for ch in base) + _AGC['fader'].get(base[0], -90)
            base_storia.append((adesso, b_lv))
            while base_storia and adesso - base_storia[0][0] > 3:
                base_storia.popleft()
            if adesso - ultimo_passo < 0.5:
                continue
            ultimo_passo = adesso
            cb = sum(v for _, v in base_storia) / len(base_storia)
            if cb < -70:
                continue                                   # base ferma o muta: niente da seguire
            medie = {}
            for ch in mic:
                canta = [v for _, v in storia[ch] if v > -50]
                if len(canta) >= 6:
                    medie[ch] = sum(canta) / len(canta)
            if not medie:
                continue
            forte = max(medie.values())
            attivi = {ch: v for ch, v in medie.items() if v >= forte - 12}
            nvoci = len(attivi)
            m = Mixer(ip)
            try:
                # l'utente ha spostato un fader a mano? quello e' il suo gusto: si sposta l'equilibrio
                for ch in attivi:
                    if ch in _AGC['messo']:
                        ora = m.get('/ch/%02d/mix/fader' % ch)
                        if ora is not None and abs(db_fader(ora) - _AGC['messo'][ch]) > 1.0:
                            delta = db_fader(ora) - _AGC['messo'][ch]
                            if _AGC['margine'] is not None:
                                _AGC['margine'] += delta
                                _margine_salvato(_AGC['margine'])
                            _AGC['fader'][ch] = db_fader(ora)
                            _AGC['partenza'][ch] = db_fader(ora)
                            _mic_base(ch, db_fader(ora))
                            _AGC['messo'][ch] = db_fader(ora)
                            _log('microfono %d spostato a mano di %+.1f dB: nuovo equilibrio voce/base %+.1f dB'
                                 % (ch, delta, _AGC['margine'] or 0))
                # la prima volta: si impara l'equilibrio che usa l'utente
                if _AGC['margine'] is None:
                    for ch, v in attivi.items():
                        _AGC['imparo'].append(v + _AGC['fader'].get(ch, 0) + 10 * math.log10(nvoci) - cb)
                    if len(_AGC['imparo']) >= 20:
                        _AGC['margine'] = sorted(_AGC['imparo'])[len(_AGC['imparo']) // 2]
                        _margine_salvato(_AGC['margine'])
                        _log('equilibrio voce/base imparato: voce %+.1f dB sopra la base' % _AGC['margine'])
                    continue
                obiettivo = cb + _AGC['margine'] - 10 * math.log10(nvoci) + (3.0 if pb_acceso() else 0.0)
                for ch, v in attivi.items():
                    ora = _AGC['fader'].get(ch)
                    if ora is None:
                        continue
                    if ch not in _AGC['partenza']:
                        mb = _mic_base(ch)
                        if mb is None:
                            mb = ora
                            _mic_base(ch, mb)
                        _AGC['partenza'][ch] = mb
                    part = _AGC['partenza'][ch]
                    voluto = max(part - 8.0, min(part + 3.0, obiettivo - v))
                    if abs(voluto - ora) < 0.75:
                        continue
                    nuovo = ora + max(-0.5, min(0.5, voluto - ora))
                    m.set('/ch/%02d/mix/fader' % ch, float(n_fader(nuovo)))
                    _AGC['fader'][ch] = nuovo
                    _AGC['messo'][ch] = nuovo
            finally:
                m.chiudi()
        except Exception as e:
            _log('agc: %s' % e)
            time.sleep(1)


def apply():
    if not _titolare():
        return False
    if str(_config('patch_242', '1')).strip() in ('0', 'no', 'off'):
        _log('spenta (patch_242=0)')
        return False
    try:
        import moduli.system as ms
    except Exception as e:
        _log('moduli: %s' % e)
        return False
    S = ms.KaraokeMonitorSystem
    if getattr(S, '_ver242', None) == _VER:
        return True
    load0 = getattr(S, '_o242_load', None) or S.load_file
    S._o242_load = load0

    def load_file(self, *a, **k):
        try:
            a = list(a)
            path0 = a[0] if a else k.get('file_path')
            solo = k.get('solo_audio', a[2] if len(a) > 2 else False)
            if path0 and pb_acceso() and not solo and not getattr(self, '_bu_carica_sottofondo', False):
                ton = k.get('tonalita', a[1] if len(a) > 1 else 0) or 0
                if int(ton) == 0:
                    ton = pb_semitoni(path0)
                else:
                    _pb_ricordato(path0, int(ton))           # tono scelto dall'utente in scaletta
                if 'tonalita' in k or len(a) < 2:
                    k['tonalita'] = int(ton)
                else:
                    a[1] = int(ton)
                _log('%s | piano bar: tono %+d' % (os.path.basename(str(path0)), int(ton)))
        except Exception as e:
            _log('piano bar tono: %s' % e)
        r = load0(self, *a, **k)
        try:
            path = getattr(self, '_original_file', None) or getattr(self, 'current_file', None)
            if (path and not getattr(self, '_bu_carica_sottofondo', False) and '://' not in str(path)
                    and os.path.splitext(str(path))[1].lower() in _EST):
                _al_brano(str(path), self)
        except Exception as e:
            _log('load: %s' % e)
        return r

    S.load_file = load_file
    pitch0 = getattr(S, '_o242_pitch', None) or S.set_pitch
    S._o242_pitch = pitch0

    def set_pitch(self, semitoni):
        r = pitch0(self, semitoni)
        try:
            cur = _STATO.get('ultimo_brano')
            if pb_acceso() and cur:
                _pb_ricordato(cur[0], int(semitoni))         # in piano bar il tono scelto resta per il brano
        except Exception:
            pass
        return r
    S.set_pitch = set_pitch
    _pb_bottone()
    S._ver242 = _VER
    threading.Thread(target=_agc_giro, daemon=True, name='regia242agc').start()
    _log('regia attiva (v%d): volume base sui fader, volume microfoni, delay a tempo, riverbero, mandate voce, presenza' % _VER)
    return True


def revert():
    return False
