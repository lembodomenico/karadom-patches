_VER = 3

_MOTORE = 'import math\nimport os\nimport re\nimport subprocess\nfrom bisect import bisect_right\nfrom pathlib import Path\n\nimport numpy as np\nfrom PIL import Image, ImageDraw, ImageFont\n\nLARGH, ALT, FPS = 1920, 1080, 60\nLH = 154\nRIGHE = 7\nFONT_PX = 125\nTEXT_PADX = 40\nBIANCO = (255, 255, 255, 255)\nROSSO = (255, 0, 0, 255)\nNOTTE = "0x060c1c"\nIMMAGINI = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}\nVIDEO = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}\n_QUI = Path(__file__).resolve().parent\nFONT_FILE = os.environ.get("KC_VIDEO_FONT", str(_QUI / "fonts" / "calibrib.ttf"))\nLOGO_FILE = _QUI / "logo_stage.png"\nVBR, ABR, CNW = "2M", "192k", 0\nPALLINO = True\nAVANZA = None\nLOGO_W, LOGO_X, LOGO_Y = 220, 38, 22\n\n\ndef _has_initial_credits(text):\n    if not text:\n        return False\n    normalized = text.lower()\n    strong = (\'all rights\', \'rights reserved\', \'copyright\', \'©\', \'(c)\', \'publishing\', \'publisher\', \'edizioni\',\n              \'edizioni musicali\', \'ricordi\', \'universal music\', \'warner chappell\', \'emi music\', \'sony/atv\',\n              \'sony music\', \'m-live\', \'m live\', \'songservice\', \'karaoke-version\', \'by m-live\')\n    if any(kw in normalized for kw in strong):\n        return True\n    head_lines = []\n    for raw_line in text.splitlines():\n        line = re.sub(r\'\\[[^\\]]+\\]\', \'\', raw_line).strip()\n        if line:\n            head_lines.append(line)\n        if len(head_lines) >= 6:\n            break\n    if not head_lines:\n        return False\n    head = \' \'.join(head_lines[:4])\n    if re.search(r\'["“”][^"“”]{2,80}["“”]\', head) and re.search(r\'\\([^\\)]{2,80}\\)\', head):\n        return True\n    if len(head_lines) >= 2:\n        first = head_lines[0].strip()\n        second = head_lines[1].strip()\n        first_is_title = bool(re.fullmatch(r\'["“”\\\']?[^"“”\\\']{2,80}["“”\\\']?\', first)) and len(first.split()) <= 8\n        second_is_author = bool(re.fullmatch(r\'\\(?[A-ZÀ-Üa-zà-ü0-9 .,&\\\'’\\-]{2,80}\\)?\', second)) and len(second.split()) <= 8\n        if first_is_title and second_is_author:\n            early_text = \' \'.join(head_lines[:4]).lower()\n            if any(w in early_text for w in (\'srl\', \'sas\', \'spa\', \'records\', \'music\', \'edizioni\', \'publisher\', \'publishing\')):\n                return True\n    return False\n\n\ndef _leading_blank_lines_count(text):\n    count = 0\n    for line in (text or \'\').split(\'\\n\'):\n        if line.strip():\n            break\n        count += 1\n    return count\n\n\ndef _padding_iniziale(full_text, sillabe):\n    if not sillabe or not any(s.strip() and s != \'\\n\' for s, _ in sillabe):\n        return 0\n    if _has_initial_credits(full_text):\n        return 0\n    return max(0, RIGHE // 2 - _leading_blank_lines_count(full_text))\n\n\ndef _monotone(sillabe):\n    out, prev = [], None\n    for s, ts in sillabe:\n        if prev is not None and ts < prev:\n            ts = prev\n        out.append((s, ts))\n        prev = ts\n    return out\n\n\ndef _font(px):\n    try:\n        return ImageFont.truetype(FONT_FILE, px)\n    except Exception:\n        for f in ("C:/Windows/Fonts/calibrib.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):\n            if os.path.exists(f):\n                return ImageFont.truetype(f, px)\n        return ImageFont.load_default()\n\n\ndef _yuv(rgb):\n    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]\n    y = 16 + (65.481 * r + 128.553 * g + 24.966 * b) / 255.0\n    u = 128 + (-37.797 * r - 74.203 * g + 112.0 * b) / 255.0\n    v = 128 + (112.0 * r - 93.786 * g - 18.214 * b) / 255.0\n    return y, u, v\n\n\ndef _mezzo(p, peso=None):\n    h, w = p.shape\n    if peso is None:\n        return p.reshape(h // 2, 2, w // 2, 2).mean(axis=(1, 3))\n    num = (p * peso).reshape(h // 2, 2, w // 2, 2).sum(axis=(1, 3))\n    den = peso.reshape(h // 2, 2, w // 2, 2).sum(axis=(1, 3))\n    return np.where(den > 0, num / np.maximum(den, 1e-6), 128.0)\n\n\ndef _piani(rgba, sfondo_rgb):\n    a = rgba[..., 3:4].astype(np.float32) / 255.0\n    rgb = rgba[..., :3].astype(np.float32)\n    if sfondo_rgb is not None:\n        rgb = rgb * a + np.array(sfondo_rgb, np.float32) * (1 - a)\n        y, u, v = _yuv(rgb)\n        u, v = _mezzo(u), _mezzo(v)\n    else:\n        y, u, v = _yuv(rgb)\n        u, v = _mezzo(u, a[..., 0]), _mezzo(v, a[..., 0])\n    c = lambda x: np.clip(np.rint(x), 0, 255).astype(np.uint8)\n    return c(y), c(u), c(v), rgba[..., 3].copy()\n\n\ndef _strisce(righe, bordo, sfondo_rgb):\n    lh = LH\n    base = _font(FONT_PX)\n    max_w = LARGH - TEXT_PADX * 2 - 20\n    out = []\n    for testo in righe:\n        t = testo.rstrip()\n        if not t:\n            out.append(None)\n            continue\n        f, px = base, FONT_PX\n        while f.getlength(t) > max_w and px > 6:\n            px -= 1\n            f = _font(px)\n        w = f.getlength(t)\n        x0 = (LARGH - w) / 2.0                               # justify=\'center\'\n        xs = [int(round(x0 + f.getlength(testo[:k]))) & ~1 for k in range(len(testo) + 1)]\n        strip = []\n        for col in (BIANCO, ROSSO):\n            im = Image.new("RGBA", (LARGH, lh), (0, 0, 0, 0))\n            d = ImageDraw.Draw(im)\n            d.text((x0, lh / 2.0), t, font=f, fill=col, anchor="lm",\n                   stroke_width=1 if bordo else 0, stroke_fill=(0, 0, 0, 255))\n            strip.append(_piani(np.asarray(im), sfondo_rgb))\n        out.append((strip[0], strip[1], xs))\n    return out\n\n\ndef _sillabe_da_eventi(eventi):\n    sil = []\n    for txt, ms in eventi or []:\n        if txt is None:\n            continue\n        sil.append((str(txt).upper(), float(ms)))\n    full = "".join(s for s, _ in sil)\n    pad = _padding_iniziale(full, sil)\n    if pad:\n        sil = [("\\n", 0.0)] * pad + sil\n    return _monotone(sil)\n\n\nclass _Motore:\n\n    def __init__(self, sillabe):\n        self.sil = sillabe\n        self.ts = [t for _, t in sillabe]\n        self.testo = "".join(s for s, _ in sillabe)\n        self.cumul = []\n        tot = 0\n        for s, _ in sillabe:\n            tot += len(s)\n            self.cumul.append(tot)\n        self.nl_prima = [0] * (len(self.testo) + 1)\n        n = 0\n        for k, c in enumerate(self.testo):\n            self.nl_prima[k] = n\n            if c == "\\n":\n                n += 1\n        self.nl_prima[len(self.testo)] = n\n        self.inizio_riga = [0]\n        for k, c in enumerate(self.testo):\n            if c == "\\n":\n                self.inizio_riga.append(k + 1)\n        self.righe = self.testo.split("\\n")\n        self.y = 0.0\n        self.nodi_t, self.nodi_r = [], []\n        k0 = 0\n        for i, (s, ts) in enumerate(sillabe):\n            k1 = self.cumul[i]\n            a = k0\n            while a < k1 and self.testo[a] in "\\n ":\n                a += 1\n            k0 = k1\n            if a >= k1:\n                continue\n            r = self.nl_prima[a]\n            if self.nodi_r and r <= self.nodi_r[-1]:\n                continue\n            if self.nodi_t and ts <= self.nodi_t[-1]:\n                continue\n            self.nodi_t.append(ts)\n            self.nodi_r.append(r)\n        self.y_max = max(0, len(self.righe) - RIGHE) * (LH)\n\n    def riga_nastro(self, t_ms):\n        nt, nr = self.nodi_t, self.nodi_r\n        if not nt:\n            return 0.0\n        if t_ms <= nt[0]:\n            return float(nr[0])\n        j = bisect_right(nt, t_ms)\n        if j >= len(nt):\n            return float(nr[-1])\n        f = (t_ms - nt[j - 1]) / (nt[j] - nt[j - 1])\n        return nr[j - 1] + (nr[j] - nr[j - 1]) * f\n\n    def indice(self, t_ms):\n        if not self.ts or t_ms < self.ts[0]:\n            return -1\n        return bisect_right(self.ts, t_ms) - 1\n\n    def passo(self, t_ms, dt):\n        idx = self.indice(t_ms)\n        rossi = self.cumul[idx] if idx >= 0 else 0\n        lh = LH\n        y = (self.riga_nastro(t_ms) - RIGHE // 2 - 0.5) * lh\n        self.y = min(max(0.0, y), float(self.y_max))\n        return rossi\n\n\ndef _fotogramma(mot, strisce, rossi, piani, vuoto, off):\n    lh = LH\n    H = piani[0].shape[0]\n    for p, val in zip(piani, vuoto):\n        p[:] = val\n    fonte_h = {1: lh, 2: lh // 2}\n    prima = off // lh\n    for r in range(prima, prima + RIGHE + 2):\n        if r < 0 or r >= len(strisce) or strisce[r] is None:\n            continue\n        y = r * lh - off\n        a, b = max(0, y), min(H, y + lh)\n        if a >= b:\n            continue\n        bianca, rossa, xs = strisce[r]\n        k = rossi - mot.inizio_riga[r]\n        if k <= 0:\n            fonte, x = bianca, None\n        elif k >= len(xs) - 1:\n            fonte, x = rossa, None\n        else:\n            fonte, x = None, xs[k]\n        for i, p in enumerate(piani):\n            sc = 2 if i in (1, 2) else 1\n            pa, pb = a // sc, (b + sc - 1) // sc\n            sa = (a - y) // sc\n            sb = min(sa + (pb - pa), fonte_h[sc])\n            pb = pa + (sb - sa)\n            if x is None:\n                p[pa:pb] = fonte[i][sa:sb]\n            else:\n                xc = x // sc\n                p[pa:pb, :xc] = rossa[i][sa:sb, :xc]\n                p[pa:pb, xc:] = bianca[i][sa:sb, xc:]\n\n\nPALLA_D = 34\nPALLA_SALTO = 0.45                          # altezza dell\'arco rispetto alla riga (x 154 px)\nPALLA_MAX_MS = 800\nPALLA_PAUSA_MS = 3000                       # pausa piu\' lunga: il pallino sparisce e rientra da sinistra\n\n\nclass _Pallino:\n\n    def __init__(self, mot, strisce, sfondo):\n        self.mot = mot\n        self.punti = []\n        primo = 0\n        for r, riga in enumerate(mot.righe[:10]):\n            if riga.strip() and set(riga.strip()) <= set("-_=*"):\n                primo = mot.inizio_riga[r] + len(riga)\n                break\n        k0 = 0\n        for i, (s, ts) in enumerate(mot.sil):\n            k1 = mot.cumul[i]\n            a, b = k0, k1\n            while a < b and mot.testo[a] in "\\n ":\n                a += 1\n            k0 = k1\n            if a >= b or a < primo:\n                continue\n            r = mot.nl_prima[a]\n            if r >= len(strisce) or strisce[r] is None:\n                continue\n            xs = strisce[r][2]\n            la, lb = a - mot.inizio_riga[r], b - mot.inizio_riga[r]\n            if lb >= len(xs):\n                continue\n            self.punti.append((ts, r, (xs[la] + xs[lb]) / 2.0, xs[0]))\n        self.ts = [p[0] for p in self.punti]\n        im = Image.new("RGBA", (PALLA_D + 4, PALLA_D + 4), (0, 0, 0, 0))\n        ImageDraw.Draw(im).ellipse((2, 2, PALLA_D + 1, PALLA_D + 1), fill=ROSSO, outline=(255, 255, 255, 255), width=2)\n        rgba = np.asarray(im).astype(np.float32)\n        self.a = rgba[..., 3] / 255.0\n        y, u, v = _yuv(rgba[..., :3])\n        self.y = y\n        self.u, self.v = _mezzo(u, self.a), _mezzo(v, self.a)\n        self.a2 = _mezzo(self.a)\n        self.alfa = sfondo\n\n    def _schermo(self, r, x, off):\n        lh = LH\n        return x, r * lh - off + lh * 0.245\n\n    def posizione(self, t, off):\n        if not self.punti or t < self.ts[0] - 1000:\n            return None\n        lh = LH\n        j = bisect_right(self.ts, t)\n        if j >= len(self.punti):\n            ts, r, x, _ = self.punti[-1]\n            return self._schermo(r, x, off) if t < ts + 1000 else None\n        tj, rj, xj, x0j = self.punti[j]\n        if j == 0 or tj - self.ts[j - 1] > PALLA_PAUSA_MS:\n            if j > 0 and t < self.ts[j - 1] + 600:\n                ti, ri, xi, _ = self.punti[j - 1]\n                return self._schermo(ri, xi, off)\n            if t < tj - 1000:\n                return None\n            da, ts0 = (rj, x0j - 2 * PALLA_D), tj - 1000\n        else:\n            ti, ri, xi, _ = self.punti[j - 1]\n            ts0 = max(ti, tj - PALLA_MAX_MS)\n            if t < ts0:\n                return self._schermo(ri, xi, off)\n            da = (ri, xi)\n        f = (t - ts0) / max(1.0, tj - ts0)\n        xa, ya = self._schermo(da[0], da[1], off)\n        xb, yb = self._schermo(rj, xj, off)\n        return xa + (xb - xa) * f, ya + (yb - ya) * f - math.sin(math.pi * f) * lh * PALLA_SALTO\n\n    def disegna(self, piani, pos):\n        h, w = self.y.shape\n        x0 = int(round(pos[0] - w / 2.0)) & ~1\n        y0 = int(round(pos[1] - h)) & ~1\n        if x0 < 0 or y0 < 0 or x0 + w > LARGH or y0 + h > ALT:\n            return\n        Y = piani[0][y0:y0 + h, x0:x0 + w]\n        Y[:] = np.clip(self.y * self.a + Y * (1 - self.a) + 0.5, 0, 255).astype(np.uint8)\n        for i, c in ((1, self.u), (2, self.v)):\n            P = piani[i][y0 // 2:y0 // 2 + h // 2, x0 // 2:x0 // 2 + w // 2]\n            P[:] = np.clip(c * self.a2 + P * (1 - self.a2) + 0.5, 0, 255).astype(np.uint8)\n        if len(piani) > 3:\n            A = piani[3][y0:y0 + h, x0:x0 + w]\n            A[:] = np.maximum(A, (self.a * 255 + 0.5).astype(np.uint8))\n\n\nBANDA_H, BARRA_W, BARRA_H = 45, 300, 35\nBANDA_MIN_MS = 1000                         # compare solo nelle pause piu\' lunghe di 1 s\n\n\nclass _Banda:\n\n    def __init__(self, mot):\n        self.sil = [(s, t) for s, t in mot.sil]\n        self.ts = [t for _, t in self.sil]\n        self.primo = 0\n        for s, t in self.sil:\n            if t > 0 and s.strip() and s != "\\n":\n                self.primo = t\n                break\n        c = lambda rgb: [int(round(float(x[0, 0]))) for x in _yuv(np.array([[rgb]], np.float32))]\n        self.nero, self.grigio, self.giallo = c((0, 0, 0)), c((0x33, 0x33, 0x33)), c((255, 255, 0))\n        self.x0 = (LARGH - BARRA_W) // 2 & ~1\n        self.y0 = (BANDA_H - BARRA_H) // 2\n\n    def resto(self, t):\n        if not self.sil:\n            return None\n        if self.primo > 0 and t < self.primo:\n            durata, fatto = self.primo, t\n        else:\n            j = bisect_right(self.ts, t) - 1\n            if j < 0 or j + 1 >= len(self.ts):\n                return None\n            a, b = self.ts[j], self.ts[j + 1]\n            if not (a < t < b):\n                return None\n            durata, fatto = b - a, t - a\n        if durata <= BANDA_MIN_MS:\n            return None\n        return 1.0 - min(1.0, max(0.0, fatto / durata))\n\n    def disegna(self, piani, resto):\n        wg = int(BARRA_W * resto)\n        x0, y0 = self.x0, self.y0\n        for i, p in enumerate(piani[:3]):\n            sc = 2 if i else 1\n            p[:BANDA_H // sc] = self.nero[i]\n            ya, yb = (y0 + sc - 1) // sc, (y0 + BARRA_H) // sc\n            xa = x0 // sc\n            p[ya:yb, xa:xa + BARRA_W // sc] = self.grigio[i]\n            p[ya:yb, xa:xa + wg // sc] = self.giallo[i]\n        if len(piani) > 3:\n            piani[3][:BANDA_H] = 255\n\n\ndef _FINE_YT(durata_s):\n    return ["-t", "%.2f" % durata_s, "-c:v", "libx264", "-preset", "medium", "-profile:v", "high",\n            "-crf", "18", "-maxrate", "12M", "-bufsize", "24M", "-pix_fmt", "yuv420p",\n            "-g", str(FPS // 2), "-bf", "2", "-flags", "+cgop",\n            "-c:a", "aac", "-b:a", "384k", "-ar", "48000", "-movflags", "+faststart"]\n\n\ndef crea_video(eventi, audio_base, audio_guida, out_base, out_guida, sfondo=None,\n               ffmpeg="ffmpeg", durata_s=None, log=print, out_yt=None, out_yt_guida=None):\n    cartella = Path(out_base).parent\n    if isinstance(sfondo, (list, tuple)):\n        foto = [Path(x) for x in sfondo if Path(x).suffix.lower() in IMMAGINI and Path(x).exists()]\n        sfondo = foto[0] if len(foto) == 1 else (foto or None)\n    if not durata_s:\n        durata_s = None\n    ext = Path(sfondo).suffix.lower() if sfondo and not isinstance(sfondo, list) else ""\n    if isinstance(sfondo, list):                              # piu\' foto: ognuna per un tratto uguale del brano\n        sil0 = _sillabe_da_eventi(eventi)\n        tot = durata_s or ((sil0[-1][1] / 1000.0 + 5) if sil0 else 10)\n        tratto = tot / len(sfondo)\n        elenco = cartella / "_sfondi.txt"\n        righe = []\n        for x in sfondo:\n            righe += ["file \'%s\'" % Path(x).resolve().as_posix().replace("\'", "\'\\\\\'\'"), "duration %.3f" % tratto]\n        righe.append("file \'%s\'" % Path(sfondo[-1]).resolve().as_posix().replace("\'", "\'\\\\\'\'"))\n        elenco.write_text("\\n".join(righe) + "\\n", encoding="utf-8")\n        ingresso = ["-f", "concat", "-safe", "0", "-i", str(elenco)]\n    elif sfondo and ext in IMMAGINI:\n        ingresso = ["-loop", "1", "-framerate", str(FPS), "-i", str(sfondo)]\n    elif sfondo and ext in VIDEO:\n        ingresso = ["-stream_loop", "-1", "-i", str(sfondo)]\n    else:\n        sfondo = None\n        ingresso = ["-f", "lavfi", "-i", "color=c=%s:s=%dx%d:r=%d" % (NOTTE, LARGH, ALT, FPS)]\n\n    sil = _sillabe_da_eventi(eventi)\n    mot = _Motore(sil)\n    notte = tuple(int(NOTTE[2:][i:i + 2], 16) for i in (0, 2, 4))\n    strisce = _strisce(mot.righe, bordo=bool(sfondo), sfondo_rgb=None if sfondo else notte)\n    if not durata_s:\n        durata_s = (sil[-1][1] / 1000.0 + 5) if sil else 10\n    n_fot = int(math.ceil(durata_s * FPS))\n    log("[VIDEO] %d righe, %d fotogrammi, sfondo: %s" % (len(mot.righe), n_fot, ("%d foto" % len(sfondo)) if isinstance(sfondo, list)\n        else (Path(sfondo).name if sfondo else "blu notte")))\n\n    raw = ["-f", "rawvideo", "-pix_fmt", "yuva420p" if sfondo else "yuv420p",\n           "-s", "%dx%d" % (LARGH, ALT), "-r", str(FPS), "-i", "-"]\n    fine = ["-t", "%.2f" % durata_s, "-c:v", "libx264", "-preset", "medium", "-crf", "23", "-maxrate", VBR, "-bufsize", "%dM" % (2 * int(re.sub(r"\\D", "", VBR) or 2)),\n            "-pix_fmt", "yuv420p", "-g", str(FPS * 4), "-c:a", "aac", "-b:a", ABR, "-movflags", "+faststart", str(out_base)]\n    yt = bool(out_yt and out_yt_guida)\n    if sfondo:\n        cad = "framerate=fps=%d" % FPS if ext in VIDEO else "fps=%d" % FPS\n        fc = ("[0:v]%s,scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d,setsar=1,format=yuv420p[bg];"\n              "[bg][1:v]overlay=0:0:format=yuv420[t]" % (cad, LARGH, ALT, LARGH, ALT))\n        cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error"] + ingresso + raw + ["-i", str(audio_base)]\n        n_logo = 3\n    else:\n        fc = "[0:v]null[t]"\n        cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error"] + raw + ["-i", str(audio_base)]\n        n_logo = 2\n    if LOGO_FILE.exists():\n        fc += ";[%d:v]scale=%d:-1:flags=lanczos[logo];[t][logo]overlay=W-w-%d:%d[v]" % (n_logo, LOGO_W, LOGO_X, LOGO_Y)\n        cmd += ["-i", str(LOGO_FILE)]\n    else:\n        fc += ";[t]null[v]"\n    a_in = "%d:a:0" % (n_logo - 1)\n    if yt:\n        fc += ";[v]split=2[v][vy]"\n    cmd += ["-filter_complex", fc, "-map", "[v]", "-map", a_in] + fine\n    if yt:\n        cmd += ["-map", "[vy]", "-map", a_in] + _FINE_YT(durata_s) + [str(out_yt)]\n    p = subprocess.Popen(cmd, cwd=str(cartella), stdin=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=CNW)\n    alti = [np.zeros((ALT + 2, LARGH), np.uint8), np.zeros((ALT // 2 + 1, LARGH // 2), np.uint8),\n            np.zeros((ALT // 2 + 1, LARGH // 2), np.uint8)]\n    if sfondo:\n        alti.append(np.zeros((ALT + 2, LARGH), np.uint8))\n        vuoto = (16, 128, 128, 0)\n    else:\n        yy, uu, vv = _yuv(np.array([[notte]], np.float32))\n        vuoto = (int(round(yy[0, 0])), int(round(uu[0, 0])), int(round(vv[0, 0])))\n    pieni = [i for i in range(len(alti)) if i in (0, 3)]\n    uscita = [np.empty((ALT, LARGH) if i in (0, 3) else (ALT // 2, LARGH // 2), np.uint8) for i in range(len(alti))]\n    t16a, t16b = np.empty((ALT, LARGH), np.uint16), np.empty((ALT, LARGH), np.uint16)\n    dt = 1.0 / FPS\n    ultimo = None\n    palla = _Pallino(mot, strisce, bool(sfondo))\n    banda = _Banda(mot)\n    try:\n        for f in range(n_fot):\n            t = (f + 0.5) * 1000.0 / FPS                       # meta\' del tempo a schermo del fotogramma\n            rossi = mot.passo(t, dt)\n            off = int(math.floor(mot.y))\n            w = int(round((mot.y - off) * 256))\n            if w >= 256:\n                off, w = off + 1, 0\n            chiave = (rossi, off)\n            if chiave != ultimo:\n                _fotogramma(mot, strisce, rossi, alti, vuoto, off)\n                ultimo = chiave\n            for i, src in enumerate(alti):\n                if i in pieni and w:\n                    np.multiply(src[:ALT], 256 - w, out=t16a, dtype=np.uint16)\n                    np.multiply(src[1:ALT + 1], w, out=t16b, dtype=np.uint16)\n                    t16a += t16b\n                    t16a += 128\n                    t16a >>= 8\n                    uscita[i][:] = t16a\n                else:\n                    uscita[i][:] = src[:uscita[i].shape[0]]\n            pos = palla.posizione(t, mot.y) if PALLINO else None\n            if pos is not None:\n                palla.disegna(uscita, pos)\n            resto = banda.resto(t)\n            if resto is not None:\n                banda.disegna(uscita, resto)\n            for pl in uscita:\n                p.stdin.write(pl)\n            if AVANZA is not None and f % 30 == 0 and AVANZA(f, n_fot) is False:\n                p.kill()\n                p.wait()\n                raise RuntimeError("annullata")\n        p.stdin.close()\n    except BrokenPipeError:\n        pass\n    err = p.stderr.read().decode("utf-8", "replace")\n    p.wait()\n    if p.returncode != 0 or not Path(out_base).exists() or (yt and not Path(out_yt).exists()):\n        raise RuntimeError("video base: " + err[-400:])\n\n    if not out_guida:\n        return True\n    cmd2 = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", str(out_base), "-i", str(audio_guida),\n            "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",\n            "-shortest", "-movflags", "+faststart", str(out_guida)]\n    r = subprocess.run(cmd2, cwd=str(cartella), capture_output=True, text=True, errors="replace", creationflags=CNW)\n    if r.returncode != 0 or not Path(out_guida).exists():\n        raise RuntimeError("video voce guida: " + (r.stderr or "")[-400:])\n    if yt:\n        cmd3 = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", str(out_yt), "-i", str(audio_guida),\n                "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "384k", "-ar", "48000",\n                "-shortest", "-movflags", "+faststart", str(out_yt_guida)]\n        r = subprocess.run(cmd3, cwd=str(cartella), capture_output=True, text=True, errors="replace")\n        if r.returncode != 0 or not Path(out_yt_guida).exists():\n            raise RuntimeError("video YouTube voce guida: " + (r.stderr or "")[-400:])\n    return True\n'

_FILE_FONT = {'Arial': ('arial', 'arialbd'), 'Calibri': ('calibri', 'calibrib'),
              'Verdana': ('verdana', 'verdanab'), 'Tahoma': ('tahoma', 'tahomabd'),
              'Impact': ('impact', 'impact'), 'Georgia': ('georgia', 'georgiab'),
              'Times New Roman': ('times', 'timesbd'), 'Comic Sans MS': ('comic', 'comicbd'),
              'Trebuchet MS': ('trebuc', 'trebucbd')}


def _titolare():
    try:
        from moduli.licensing import load_license
        d = load_license() or {}
        return (str(d.get('nome', '')).strip().lower(),
                str(d.get('cognome', '')).strip().lower()) == ('domenico', 'lembo')
    except Exception:
        return False


def _rgb(h, dif):
    h = str(h or dif).lstrip('#')
    try:
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    except Exception:
        return _rgb(dif, dif)


def _file_font(nome, grassetto):
    import os
    fonts = os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts')
    coppia = _FILE_FONT.get(nome, ('arial', 'arialbd'))
    for f in (coppia[1 if grassetto else 0], coppia[0], 'arialbd', 'arial'):
        p = os.path.join(fonts, f + '.ttf')
        if os.path.exists(p):
            return p
    return 'arial.ttf'


def _durata(source, cnw):
    import subprocess
    try:
        r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                            '-of', 'default=noprint_wrappers=1:nokey=1', source],
                           capture_output=True, text=True, timeout=15, creationflags=cnw)
        return float(r.stdout.strip())
    except Exception:
        return 0.0


def _motore(width, height, righe, dim, grassetto, font, testo, evid, sfondo_col, vbr, abr, logo, cnw, avanza, pallino=True):
    from pathlib import Path
    ns = {'__name__': 'convertitore_kc', '__file__': str(logo)}
    exec(compile(_MOTORE, 'convertitore_kc', 'exec'), ns)
    w, h = int(width) // 2 * 2, int(height) // 2 * 2
    righe = max(3, int(righe))
    lh = (h // righe) // 2 * 2
    dim = str(dim).strip()
    if dim.isdigit():
        scala = min(w / 1024.0, h / 600.0)
        px = min(int(int(dim) * scala), int(lh * 0.95))
    else:
        px = int(round(lh * 125 / 154.0))
    k = lh / 154.0
    pari = lambda x: max(2, int(round(x)) // 2 * 2)
    ns.update(LARGH=w, ALT=h, FPS=60, RIGHE=righe, LH=lh, FONT_PX=max(8, px),
              FONT_FILE=_file_font(font, grassetto), TEXT_PADX=max(10, int(round(40 * w / 1920.0))),
              BIANCO=_rgb(testo, '#FFFFFF') + (255,), ROSSO=_rgb(evid, '#FF0000') + (255,),
              NOTTE='0x%02x%02x%02x' % _rgb(sfondo_col, '#060c1c'),
              LOGO_FILE=Path(logo), LOGO_W=pari(220 * min(w, h * 16 / 9.0) / 1920.0),
              LOGO_X=pari(38 * w / 1920.0), LOGO_Y=pari(22 * h / 1080.0),
              PALLA_D=pari(34 * k), BANDA_H=pari(45 * h / 1080.0), BARRA_W=pari(300 * w / 1920.0),
              BARRA_H=pari(35 * h / 1080.0), VBR=vbr, ABR=abr, CNW=cnw, AVANZA=avanza, PALLINO=bool(pallino))
    return ns


def _conversione(self, source, syllables):
    import os
    import moduli.convertitore as mc
    _t = getattr(mc, '_', lambda x: x)
    try:
        preset = None
        nome = self.preset_combo.get()
        for p in mc.PRESETS.values():
            if p['name'] == nome:
                preset = p
                break
        if not preset:
            preset = list(mc.PRESETS.values())[0]
        cartella = self.output_entry.get()
        os.makedirs(cartella, exist_ok=True)
        base = os.path.splitext(os.path.basename(source))[0]
        uscita = os.path.join(cartella, f"{base}_karaoke.mp4")
        self._update_progress(5, _t("Preparazione testo sincronizzato..."))
        durata = _durata(source, mc._CNW) or ((syllables[-1][1] / 1000.0 + 5) if syllables else 10)
        self.audio_duration_total = durata
        sfondo = None
        if self.bg_type.get() == 'image':
            f = self.bg_image_entry.get().strip()
            if f and os.path.exists(f):
                sfondo = f
        radice = os.path.dirname(os.path.dirname(os.path.abspath(mc.__file__)))
        logo = os.path.join(radice, 'img', 'logo_stage.png')
        grassetto = True if getattr(self, 'bold_var', None) is None else bool(self.bold_var.get())

        def avanza(f, n):
            if not self.is_converting:
                return False
            sec = f / 60.0
            self._update_progress(min(99, 5 + 94.0 * f / max(1, n)), _t("Creazione video karaoke..."), sec, durata)
            return True

        ns = _motore(preset['width'], preset['height'], self.lines_var.get(), self.font_size_var.get(), grassetto,
                     self.font_var.get(), self.text_color.get(), self.highlight_color.get(), self.bg_color.get(),
                     preset.get('video_bitrate', '8M'), preset.get('audio_bitrate', '192k'), logo, mc._CNW, avanza,
                     pallino=True if getattr(self, 'pallino_var', None) is None else bool(self.pallino_var.get()))
        eventi = [(s, t) for s, t in syllables]
        ns['crea_video'](eventi, source, None, uscita, None, sfondo=sfondo, durata_s=durata,
                         log=lambda m: print('[250] %s' % m))
        self._update_progress(100, f"✅ {os.path.basename(uscita)}")
        self.window.after(0, lambda of=uscita: mc.messagebox.showinfo(
            _t("Successo"), _t("Video karaoke creato!\n\n{of}").format(of=of), parent=self.window))
    except Exception as e:
        msg = str(e)
        if msg == 'annullata':
            msg = _t("Conversione annullata")
        self._update_progress(0, f"❌ {msg}")
        self.window.after(0, lambda m=msg: mc.messagebox.showerror(_t("Errore"), m, parent=self.window))
    finally:
        self.is_converting = False
        try:
            self.window.after(0, lambda: self.btn_convert.config(state='normal'))
            self.window.after(0, lambda: self.btn_cancel.config(state='disabled'))
        except Exception:
            pass


def _scegli_sfondo(self):
    import tkinter as tk
    import moduli.convertitore as mc
    _t = getattr(mc, '_', lambda x: x)
    f = mc.filedialog.askopenfilename(
        parent=self.window,
        filetypes=[(_t("Immagini o video"), "*.jpg *.jpeg *.png *.bmp *.webp *.mp4 *.mov *.mkv *.webm *.avi *.m4v"),
                   (_t("Immagini"), "*.jpg *.jpeg *.png *.bmp *.webp")])
    if f:
        self.bg_image_entry.delete(0, tk.END)
        self.bg_image_entry.insert(0, f)
        self._save_setting('converter_bg_image', f)


def _ui(self):
    import tkinter as tk
    import moduli.convertitore as mc
    _t = getattr(mc, '_', lambda x: x)
    try:
        v = mc.Database.get_config('converter_pallino', '1')
    except Exception:
        v = '1'
    self.pallino_var = tk.BooleanVar(value=str(v) != '0')
    bv = str(getattr(self, 'bold_var', ''))
    trovato = []

    def giro(w):
        for c in w.winfo_children():
            if isinstance(c, tk.Checkbutton) and bv and str(c.cget('variable')) == bv:
                trovato.append(c)
            giro(c)
    giro(self.window)
    if not trovato:
        return
    tk.Checkbutton(trovato[0].master, text=_t("Pallino"), variable=self.pallino_var,
                   bg='#1a1a1a', fg='white', selectcolor='#333333', activebackground='#1a1a1a',
                   activeforeground='white', font=mc.F('Arial', 10, 'bold'),
                   command=lambda: self._save_setting('converter_pallino', '1' if self.pallino_var.get() else '0')
                   ).pack(side='left', padx=(mc.S(15), mc.S(0)))


def apply():
    try:
        import moduli.convertitore as mc
        C = mc.ConvertitoreKaraoke
        if getattr(C, '_ver250', None) == _VER:
            return True
        if not getattr(C, '_o250_conv', None):
            C._o250_conv = C._do_conversion
        if not getattr(C, '_o250_sfondo', None):
            C._o250_sfondo = C._select_bg_image
        ui0 = getattr(C, '_o250_ui', None) or C._create_ui
        C._o250_ui = ui0

        def _create_ui(self, *a, **k):
            r = ui0(self, *a, **k)
            try:
                _ui(self)
            except Exception as e:
                print('[250] %s' % e)
            return r

        C._do_conversion = _conversione
        C._select_bg_image = _scegli_sfondo
        C._create_ui = _create_ui
        C._ver250 = _VER
        print('[250] convertitore come KC v%d' % _VER)
        return True
    except Exception as e:
        print('[250] %s' % e)
        return False
