# 235 - testo sfumato
# PROVA della 234 v10 (numero libero: la 234 online la sovrascriverebbe)
# 234 - testo scorrevole del monitor pubblico FLUIDO + SFONDO TRASPARENTE
# [21-10-2026] utente: "il testo scorrevole scorre a scatti anziche' in modo fluido" (PC KARADOM .214)
# + "voglio vedere se e' possibile su sfondo trasparente".
# Fluido (misurato, D:\\Claude\\testo_scorrevole): prima 16 passi/s da 3 px (after(50) = 62,5 ms col
# timer di Windows), ora ~60 passi/s da ~0,8 px dal tempo trascorso + timeBeginPeriod(1); stessa velocita'.
# Trasparente: nel campo "Sfondo (HEX con alpha)" alpha 00 (es. #00000000) -> niente striscia, testo
# col bordo nero direttamente sul video (finestrella figlia del monitor con -transparentcolor).
# [22-10-2026] v8: piu' colori nel campo Sfondo = striscia SFUMATA IN ALTO nel video (niente bordino).
# Codice preso dal sorgente moduli/karaoke_monitor.py (fai_patch_234.py): col compilato nuovo non serve.

_VER = 10

import sys
import time
import tkinter as tk

_timer_fatto = [False]


def _timer_1ms():
    """Su Windows il timer di serie va a 15,6 ms: un after(16) diventa 15 o 31 ms a caso e il
    testo scorrevole va a scatti. timeBeginPeriod(1) lo porta a 1 ms (lo fa gia' anche
    fluidsynth_player); una volta sola."""
    if _timer_fatto[0]:
        return
    _timer_fatto[0] = True
    if sys.platform.startswith("win"):
        try:
            import ctypes
            ctypes.windll.winmm.timeBeginPeriod(1)
        except Exception:
            pass

def _ensure_ctk_window_compat(window):
    if not hasattr(window, "block_update_dimensions_event"):
        window.block_update_dimensions_event = lambda *a, **k: None
    if not hasattr(window, "unblock_update_dimensions_event"):
        window.unblock_update_dimensions_event = lambda *a, **k: None


_BLOCCO = '''class _Nuovi:
    # -- [21-10-2026] SFONDO TRASPARENTE del testo scorrevole -----------------------------------
    # Utente: "voglio vedere se e' possibile su sfondo trasparente". Il campo "Sfondo (HEX con
    # alpha)" aveva gia' l'alpha, ma Tk lo ignorava (striscia sempre piena). Ora alpha 00
    # (es. #00000000) = TRASPARENTE: il testo sta in una finestrella senza cornice, FIGLIA del
    # monitor (transient = Windows la tiene sopra il suo padrone da solo, SENZA rialzarla di
    # continuo: era il rialzo continuo sopra VLC a rompere il video nella prova del logo), con
    # -transparentcolor; il testo ha un bordo nero per leggersi su qualunque video.
    # Solo Windows: su Linux (X11) -transparentcolor non c'e' e resta la striscia.
    _OVL_CHIAVE = '#010203'

    @staticmethod
    def _sfondo_trasparente(background):
        b = str(background or '').strip().lower()
        if b in ('trasparente', 'transparent', 'none'):
            return True
        return len(b) == 9 and b.startswith('#') and b[7:] == '00'

    def _ovl_finestra(self):
        w = getattr(self, '_ovl_win', None)
        try:
            if w is not None and w.winfo_exists():
                return w
        except Exception:
            pass
        w = tk.Toplevel(self.window)
        w.withdraw()
        w.overrideredirect(True)
        w.transient(self.window)
        w.configure(bg=self._OVL_CHIAVE)
        w.attributes('-transparentcolor', self._OVL_CHIAVE)
        cv = tk.Canvas(w, bg=self._OVL_CHIAVE, highlightthickness=0, bd=0)
        cv.pack(fill='both', expand=True)
        self._ovl_win, self._ovl_cv = w, cv
        # [22-10-2026] NIENTE proprietario: KaraDom ricrea la finestra del monitor quando lo si tocca
        # (overrideredirect su/giu' = finestra Windows nuova) e Windows DISTRUGGE le finestre di
        # proprieta' di quella vecchia: il testo spariva e non tornava. Sempre davanti, ripetuto.
        return w

    def _ovl_proprietario(self):
        """Il monitor diventa il PROPRIETARIO della finestrella: Windows tiene sempre una finestra
        sopra il suo proprietario, anche quando lui si rimette in primo piano. ⛔ Con
        overrideredirect wm transient di Tk NON lo fa (misurato: proprietario = 0, e il monitor
        sempre-in-primo-piano copriva il testo): lo si imposta direttamente."""
        try:
            import ctypes
            u = ctypes.windll.user32
            u.GetAncestor.restype = ctypes.c_void_p
            u.GetAncestor.argtypes = [ctypes.c_void_p, ctypes.c_uint]
            self._ovl_win.update_idletasks()
            h = u.GetAncestor(ctypes.c_void_p(self._ovl_win.winfo_id()), 2)
            hm = u.GetAncestor(ctypes.c_void_p(self.window.winfo_id()), 2)
            if h and hm and u.GetWindow(ctypes.c_void_p(h), 4) != hm:            # GW_OWNER
                f = getattr(u, 'SetWindowLongPtrW', None) or u.SetWindowLongW
                f.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]
                f(ctypes.c_void_p(h), -8, ctypes.c_void_p(hm))                     # GWLP_HWNDPARENT
        except Exception as e:
            print(f"⚠️ testo trasparente, proprietario: {e}")

    def _ovl_hwnd(self):
        import ctypes
        u = ctypes.windll.user32
        u.GetAncestor.restype = ctypes.c_void_p
        u.GetAncestor.argtypes = [ctypes.c_void_p, ctypes.c_uint]
        return (u.GetAncestor(ctypes.c_void_p(self._ovl_win.winfo_id()), 2),
                u.GetAncestor(ctypes.c_void_p(self.window.winfo_id()), 2))

    def _ovl_davanti(self):
        try:
            h, _hm = self._ovl_hwnd()
            self._sopra_monitor(h)
        except Exception as e:
            print(f"⚠️ testo trasparente, davanti: {e}")

    def _sopra_monitor(self, h):
        """La finestrella del testo sta SUBITO SOPRA il monitor pubblico, non sopra tutto.
        [22-10-2026] utente: "compare sul monitor principale": con un solo schermo il monitor
        pubblico e' una finestra normale e la striscia "sempre in primo piano" copriva KaraDom.
        Sempre in primo piano solo se lo e' il monitor (serata a schermo intero). Senza prendere
        il fuoco; non fa niente se e' gia' al posto giusto."""
        import ctypes
        u = ctypes.windll.user32
        u.GetAncestor.restype = ctypes.c_void_p
        u.GetAncestor.argtypes = [ctypes.c_void_p, ctypes.c_uint]
        u.GetWindow.restype = ctypes.c_void_p
        u.GetWindow.argtypes = [ctypes.c_void_p, ctypes.c_uint]
        u.GetWindowLongW.restype = ctypes.c_long
        hm = u.GetAncestor(ctypes.c_void_p(self.window.winfo_id()), 2)
        if not hm or not h:
            return
        top = bool(u.GetWindowLongW(ctypes.c_void_p(hm), -20) & 0x8)
        mio_top = bool(u.GetWindowLongW(ctypes.c_void_p(h), -20) & 0x8)
        prima = u.GetWindow(ctypes.c_void_p(hm), 3)                       # GW_HWNDPREV: chi sta sopra
        if prima == h and mio_top == top:
            return
        F = 0x0001 | 0x0002 | 0x0010                                     # no size/move/activate
        if mio_top and not top:
            u.SetWindowPos(ctypes.c_void_p(h), ctypes.c_void_p(-2), 0, 0, 0, 0, F)   # NOTOPMOST
            prima = u.GetWindow(ctypes.c_void_p(hm), 3)
        if top:
            u.SetWindowPos(ctypes.c_void_p(h), ctypes.c_void_p(-1), 0, 0, 0, 0, F)   # TOPMOST
        elif prima != h:
            # subito sotto chi stava sopra il monitor = subito sopra il monitor
            u.SetWindowPos(ctypes.c_void_p(h), ctypes.c_void_p(prima or 0), 0, 0, 0, 0, F)

    def _ovl_diagnosi(self):
        """[21-10-2026] sul PC KARADOM il testo trasparente non si vedeva: nel diario va scritto
        DOVE sta la finestrella, chi e' il proprietario e cosa vede Windows nel punto del testo."""
        try:
            import ctypes
            u = ctypes.windll.user32

            class R(ctypes.Structure):
                _fields_ = [("l", ctypes.c_long), ("t", ctypes.c_long), ("r", ctypes.c_long), ("b", ctypes.c_long)]

            class P(ctypes.Structure):
                _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

            h, hm = self._ovl_hwnd()
            ro, rm = R(), R()
            u.GetWindowRect(ctypes.c_void_p(h), ctypes.byref(ro))
            u.GetWindowRect(ctypes.c_void_p(hm), ctypes.byref(rm))
            u.GetWindow.restype = ctypes.c_void_p
            own = u.GetWindow(ctypes.c_void_p(h), 4)
            u.GetWindowLongW.restype = ctypes.c_long
            ex = u.GetWindowLongW(ctypes.c_void_p(h), -20)
            bb = self.overlay_canvas.bbox('tsc')
            px = (ro.l + ro.r) // 2
            py = (ro.t + ro.b) // 2
            u.WindowFromPoint.restype = ctypes.c_void_p
            sotto = u.WindowFromPoint(P(px, py))
            radice = u.GetAncestor(ctypes.c_void_p(sotto), 2) if sotto else 0
            nome = ctypes.create_unicode_buffer(128)
            u.GetClassNameW(ctypes.c_void_p(radice or 0), nome, 128)
            tit = ctypes.create_unicode_buffer(128)
            u.GetWindowTextW(ctypes.c_void_p(radice or 0), tit, 128)
            try:
                dpi = u.GetDpiForWindow(ctypes.c_void_p(hm))
            except Exception:
                dpi = '?'
            print(f"[OVL-DIAG] finestrella {ro.l},{ro.t}-{ro.r},{ro.b} visibile={u.IsWindowVisible(ctypes.c_void_p(h))} "
                  f"exstyle=0x{ex & 0xffffffff:x} proprietario={own} | monitor {rm.l},{rm.t}-{rm.r},{rm.b} hwnd={hm} dpi={dpi} "
                  f"| tk geo ovl={self._ovl_win.geometry()} mon={self.window.winfo_rootx()},{self.window.winfo_rooty()} "
                  f"{self.window.winfo_width()}x{self.window.winfo_height()} | testo bbox={bb} canvas="
                  f"{self.overlay_canvas.winfo_width()}x{self.overlay_canvas.winfo_height()} "
                  f"| nel punto ({px},{py}) c'e' hwnd={radice} classe='{nome.value}' titolo='{tit.value}' (ovl={h})")
        except Exception as e:
            print(f"[OVL-DIAG] errore: {e}")

    def _ovl_posiziona(self, h):
        """La finestrella sta sul fondo del monitor, larga quanto lui (lo segue se si sposta)."""
        w = getattr(self, '_ovl_win', None)
        if w is None:
            return
        x, y = self.window.winfo_rootx(), self.window.winfo_rooty()
        W, H = self.window.winfo_width(), self.window.winfo_height()
        geo = "%dx%d+%d+%d" % (max(1, W), max(1, h), x, y + H - h)
        if getattr(self, '_ovl_geo', None) != geo:
            self._ovl_geo = geo
            w.geometry(geo)

    # -- [22-10-2026] STRISCIA SFUMATA IN ALTO ---------------------------------------------------
    # Utente: "si puo' fare in modo di non vedere il bordino?" (la riga netta tra la striscia a
    # colori e il video). Tk non ha la trasparenza per pixel: con piu' colori nel campo Sfondo la
    # striscia diventa una finestrella "layered" (UpdateLayeredWindow, alpha vero) disegnata con
    # PIL: sopra la striscia una fascia alta mezza striscia passa da invisibile a piena, il video
    # sotto si vede attraverso. Il testo si disegna una volta e a ogni passo si incolla spostato.
    def _sfu_finestra(self):
        w = getattr(self, '_sfu_win', None)
        try:
            if w is not None and w.winfo_exists():
                return w
        except Exception:
            pass
        import ctypes
        u = ctypes.windll.user32
        u.GetAncestor.restype = ctypes.c_void_p
        u.GetAncestor.argtypes = [ctypes.c_void_p, ctypes.c_uint]
        w = tk.Toplevel(self.window)
        w.withdraw()
        w.overrideredirect(True)
        w.update_idletasks()
        h = u.GetAncestor(ctypes.c_void_p(w.winfo_id()), 2)
        u.GetWindowLongW.restype = ctypes.c_long
        u.SetWindowLongW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_long]
        ex = u.GetWindowLongW(ctypes.c_void_p(h), -20)
        # layered + clic che passano sotto + mai attiva + niente tasto nella barra
        u.SetWindowLongW(ctypes.c_void_p(h), -20, (ex | 0x80000 | 0x20 | 0x08000000 | 0x80) & ~0x40000)
        # ⛔ NIENTE proprietario: KaraDom ricrea la finestra del monitor quando lo si tocca e Windows
        # distrugge le finestre di proprieta' di quella vecchia (provato: spariva e non tornava)
        self._sfu_win, self._sfu_h = w, h
        self._sfu_dib = None
        return w

    def _sfu_rect(self):
        """Rettangolo del monitor pubblico ADESSO (la sua finestra Windows cambia: mai tenerla da
        parte). None se e' nascosto o non ha ancora una misura vera."""
        import ctypes
        u = ctypes.windll.user32
        u.GetAncestor.restype = ctypes.c_void_p
        u.GetAncestor.argtypes = [ctypes.c_void_p, ctypes.c_uint]

        class R(ctypes.Structure):
            _fields_ = [("l", ctypes.c_long), ("t", ctypes.c_long), ("r", ctypes.c_long), ("b", ctypes.c_long)]
        try:
            hm = u.GetAncestor(ctypes.c_void_p(self.window.winfo_id()), 2)
        except Exception:
            return None
        if not hm or not u.IsWindowVisible(ctypes.c_void_p(hm)):
            return None
        rm = R()
        if not u.GetWindowRect(ctypes.c_void_p(hm), ctypes.byref(rm)):
            return None
        if rm.r - rm.l < 50 or rm.b - rm.t < 50:
            return None
        return (rm.l, rm.t, rm.r, rm.b)

    def _sfu_davanti(self):
        self._sopra_monitor(self._sfu_h)

    def _sfu_prepara(self, height, tappe, testo, font_size, colore_testo, anelli):
        """Sfondo (sfumato in alto, gia' premoltiplicato) e testo (con gli anelli del bordo)."""
        from PIL import Image, ImageChops, ImageDraw, ImageFont
        rect = self._sfu_rect()
        if rect is None:
            raise RuntimeError("monitor pubblico non visibile")
        W = rect[2] - rect[0]
        fade = max(8, height // 2)
        H = height + fade
        self._sfu_geo = (W, H, fade, height)
        # colori da sinistra a destra (una riga, poi stirata)
        riga = Image.new('RGB', (W, 1))
        px = riga.load()
        for x in range(W):
            fr = x / max(1, W - 1) * (len(tappe) - 1)
            i = min(int(fr), len(tappe) - 2) if len(tappe) > 1 else 0
            t = fr - i
            a = tappe[i]
            b = tappe[i + 1] if len(tappe) > 1 else a
            px[x, 0] = tuple(int(a[k] + (b[k] - a[k]) * t) for k in range(3))
        rgb = riga.resize((W, H), Image.NEAREST)
        # trasparenza: dall'alto 0 -> 255 con curva morbida (niente riga dove finisce), poi piena
        col = Image.new('L', (1, H))
        pa = col.load()
        for y in range(H):
            if y >= fade:
                pa[0, y] = 255
            else:
                s = y / float(fade)
                pa[0, y] = int(255 * s * s * (3 - 2 * s))
        alfa = col.resize((W, H), Image.NEAREST)
        bg = ImageChops.multiply(rgb, Image.merge('RGB', (alfa, alfa, alfa)))  # premoltiplicato
        bg.putalpha(alfa)
        self._sfu_bg = bg
        # testo: stessa grandezza del testo Tk (punti -> pixel come fa Tk)
        try:
            pxl = int(round(font_size * self.window.winfo_fpixels('1i') / 72.0))
        except Exception:
            pxl = int(font_size * 96 / 72)
        try:
            fnt = ImageFont.truetype('arialbd.ttf', pxl)
        except Exception:
            fnt = ImageFont.load_default()
        o_max = max([off for off, _c in anelli] or [0])
        l, t0, r, b0 = fnt.getbbox(testo)
        tw, th = (r - l) + 2 * o_max + 2, height
        img = Image.new('RGBA', (max(1, tw), th), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        x0 = o_max - l + 1
        y0 = height // 2 - (t0 + b0) // 2
        for off, c in anelli:
            for dx in (-off, 0, off):
                for dy in (-off, 0, off):
                    if dx or dy:
                        d.text((x0 + dx, y0 + dy), testo, font=fnt, fill=c)
        d.text((x0, y0), testo, font=fnt, fill=colore_testo)
        self._sfu_txt = img
        self._sfu_pos = (rect[0], rect[3] - H)
        self._sfu_rect_ok = rect

    def _sfu_disegna(self, x):
        """Un passo: sfondo + testo alla posizione x -> UpdateLayeredWindow."""
        import ctypes
        from ctypes import wintypes
        W, H, fade, height = self._sfu_geo
        fr = self._sfu_bg.copy()
        txt = self._sfu_txt
        a, b = max(0, -x), min(txt.width, W - x)
        if b > a:
            fr.alpha_composite(txt.crop((a, 0, b, txt.height)), (x + a, fade))
        dati = fr.tobytes('raw', 'BGRA')
        g = ctypes.windll.gdi32
        u = ctypes.windll.user32
        if getattr(self, '_sfu_dib', None) is None or self._sfu_dib[0] != (W, H):
            class BIH(ctypes.Structure):
                _fields_ = [("biSize", wintypes.DWORD), ("biWidth", ctypes.c_long), ("biHeight", ctypes.c_long),
                            ("biPlanes", wintypes.WORD), ("biBitCount", wintypes.WORD),
                            ("biCompression", wintypes.DWORD), ("biSizeImage", wintypes.DWORD),
                            ("biXPelsPerMeter", ctypes.c_long), ("biYPelsPerMeter", ctypes.c_long),
                            ("biClrUsed", wintypes.DWORD), ("biClrImportant", wintypes.DWORD)]
            g.CreateCompatibleDC.restype = ctypes.c_void_p
            g.CreateCompatibleDC.argtypes = [ctypes.c_void_p]
            g.CreateDIBSection.restype = ctypes.c_void_p
            g.CreateDIBSection.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint,
                                           ctypes.POINTER(ctypes.c_void_p), ctypes.c_void_p, wintypes.DWORD]
            g.SelectObject.restype = ctypes.c_void_p
            g.SelectObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
            g.DeleteObject.argtypes = [ctypes.c_void_p]
            g.DeleteDC.argtypes = [ctypes.c_void_p]
            vecchio = getattr(self, '_sfu_dib', None)
            if vecchio is not None:
                g.SelectObject(vecchio[1], vecchio[3])
                g.DeleteObject(vecchio[2])
                g.DeleteDC(vecchio[1])
            bi = BIH(ctypes.sizeof(BIH), W, -H, 1, 32, 0, 0, 0, 0, 0, 0)
            bits = ctypes.c_void_p()
            dc = g.CreateCompatibleDC(None)
            bmp = g.CreateDIBSection(dc, ctypes.byref(bi), 0, ctypes.byref(bits), None, 0)
            prima = g.SelectObject(dc, bmp)
            self._sfu_dib = ((W, H), dc, bmp, prima, bits.value)
        _wh, dc, _bmp, _p, bits = self._sfu_dib
        g.GdiFlush()
        ctypes.memmove(bits, dati, len(dati))

        class PT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

        class SZ(ctypes.Structure):
            _fields_ = [("cx", ctypes.c_long), ("cy", ctypes.c_long)]

        class BF(ctypes.Structure):
            _fields_ = [("op", ctypes.c_ubyte), ("fl", ctypes.c_ubyte), ("a", ctypes.c_ubyte), ("af", ctypes.c_ubyte)]
        u.UpdateLayeredWindow.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
                                          ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.c_void_p,
                                          wintypes.DWORD]
        dove = PT(*self._sfu_pos)
        ok = u.UpdateLayeredWindow(ctypes.c_void_p(self._sfu_h), None, ctypes.byref(dove), ctypes.byref(SZ(W, H)),
                                   ctypes.c_void_p(dc), ctypes.byref(PT(0, 0)), 0,
                                   ctypes.byref(BF(0, 0, 255, 1)), 2)
        if not ok and not getattr(self, '_sfu_errore_detto', False):
            self._sfu_errore_detto = True
            print(f"⚠️ striscia sfumata: UpdateLayeredWindow errore {ctypes.GetLastError()}")

    def _sfu_passo(self):
        """Un passo della striscia sfumata. Monitor nascosto = striscia via, e ogni 250 ms si
        guarda se e' tornato; ogni quarto di secondo si rimette davanti e segue il monitor."""
        speed = 0
        try:
            rect = self._sfu_rect() if self.visible else None
            if rect is None:
                if not getattr(self, '_sfu_via', False):
                    self._sfu_win.withdraw()
                    self._sfu_via = True
                self._overlay_t = None
                self._overlay_animation_job = self.window.after(250, self._animate_overlay)
                return
            if rect[2] - rect[0] != self._sfu_geo[0]:
                # cambiata la larghezza del monitor: si rifa' tutto alla misura nuova
                c = self.overlay_config
                self.show_text_overlay(c["testo"], c["font_size"], c["speed"], c["color"], c["background"])
                return
            self._sfu_pos = (rect[0], rect[3] - self._sfu_geo[1])
            speed = max(0, int(self.overlay_config.get("speed", 3)))
            if speed > 0:
                _timer_1ms()
                adesso = time.perf_counter()
                prima = getattr(self, '_overlay_t', None)
                passo = (1.0 / 60.0) if (prima is None or adesso - prima > 0.25) else (adesso - prima)
                self._overlay_t = adesso
                self.overlay_x_pos -= speed * 16.0 * passo
                if self.overlay_x_pos + self._sfu_txt.width < 0:
                    self.overlay_x_pos = float(self._sfu_geo[0])
            nuovo = int(round(self.overlay_x_pos))
            self._sfu_conta = getattr(self, '_sfu_conta', 0) + 1
            if (nuovo != getattr(self, '_overlay_x_disegnato', None) or rect != getattr(self, '_sfu_rect_ok', None)
                    or getattr(self, '_sfu_via', False)):
                self._sfu_disegna(nuovo)
                self._overlay_x_disegnato = nuovo
                self._sfu_rect_ok = rect
            if getattr(self, '_sfu_via', False):
                self._sfu_win.deiconify()
                self._sfu_disegna(nuovo)
                self._sfu_via = False
                self._sfu_davanti()
            elif self._sfu_conta % 4 == 0:
                self._sfu_davanti()
        except Exception as e:
            print(f"⚠️ striscia sfumata: {e}")
            self._sfu_nascondi()
            return
        self._overlay_animation_job = self.window.after(16 if speed > 0 else 250, self._animate_overlay)

    def _sfu_nascondi(self):
        self._sfu_on = False
        try:
            if getattr(self, '_sfu_win', None) is not None:
                self._sfu_win.withdraw()
        except Exception:
            pass

    def show_text_overlay(self, testo, font_size=50, speed=3, color="#FFD700", background="#000000CC"):
        """Mostra overlay testo scorrevole"""
        print(f"🔍 show_text_overlay chiamato: testo='{testo[:50]}', visible={self.visible}")

        # Reset completo dell'animazione precedente prima di applicare quella nuova
        try:
            if self._overlay_animation_job is not None:
                self.window.after_cancel(self._overlay_animation_job)
        except Exception:
            pass
        self._overlay_animation_job = None

        self.overlay_enabled = True
        self.overlay_config = {
            "testo": testo if testo.strip() else "🎤 Benvenuti! 🎵",
            "font_size": font_size,
            "speed": max(0, int(speed)),
            "color": color,
            "background": background
        }
        if getattr(self, '_ovl_normale', None) is None:
            self._ovl_normale = self.overlay_canvas          # la striscia di sempre
        height = font_size + 40

        trasp = sys.platform.startswith('win') and self._sfondo_trasparente(background)
        sfumata = False
        self._sfu_nascondi()
        if trasp:
            try:
                self._ovl_finestra()
            except Exception as e:
                print(f"⚠️ testo scorrevole trasparente non disponibile: {e}")
                trasp = False
        if trasp:
            try:
                self._ovl_normale.place_forget()
            except Exception:
                pass
            canvas = self._ovl_cv
            self._ovl_geo = None
            self._ovl_posiziona(height)
            self._ovl_win.deiconify()
            self._ovl_proprietario()
            self._ovl_win.lift()
            self._ovl_davanti()
            try:
                self.window.after(1500, self._ovl_diagnosi)
            except Exception:
                pass
        else:
            try:
                if getattr(self, '_ovl_win', None) is not None:
                    self._ovl_win.withdraw()
            except Exception:
                pass
            canvas = self._ovl_normale
            # [21-10-2026] utente: "#0060FF con i bordi sfumati di rosso... il rosso lo voglio mettere
            # prima e dopo... io dicevo lo SFONDO... il blu al centro e a sinistra e destra il rosso
            # sfumato": nel campo Sfondo piu' colori separati da virgola = striscia SFUMATA da sinistra
            # a destra ("#FF0000,#0060FF,#FF0000" = rosso a sinistra, blu al centro, rosso a destra).
            tappe = []
            for p in str(background or '').replace(';', ',').replace(' ', ',').split(','):
                p = p.strip()
                if not p:
                    continue
                p = p[:7] if (len(p) == 9 and p.startswith('#')) else p
                try:
                    tappe.append(tuple(v // 257 for v in canvas.winfo_rgb(p)))
                except Exception:
                    pass
            if not tappe:
                # un valore sbagliato nel campo Sfondo mandava in errore: si usa il nero
                print(f"⚠️ sfondo del testo scorrevole non valido ({background!r}): uso il nero")
                tappe = [(0, 0, 0)]
            bg_rgb = '#%02x%02x%02x' % tappe[len(tappe) // 2]
            sfumata = sys.platform.startswith('win') and len(tappe) > 1
            canvas.configure(height=height, bg=bg_rgb)
            canvas.place(relx=0, rely=1.0, anchor='sw', relwidth=1.0)
            try:
                canvas.delete('sfondo')
                if len(tappe) > 1:
                    canvas.update_idletasks()
                    larg = max(1, canvas.winfo_width())
                    if larg <= 1:
                        larg = max(1, self.window.winfo_width())
                    passo_px = 2                                  # colonne da 2 px: sfumatura liscia
                    for x in range(0, larg, passo_px):
                        f = x / max(1, larg - 1) * (len(tappe) - 1)
                        i = min(int(f), len(tappe) - 2)
                        t = f - i
                        c = tuple(int(tappe[i][k] + (tappe[i + 1][k] - tappe[i][k]) * t) for k in range(3))
                        canvas.create_rectangle(x, 0, x + passo_px, height, fill='#%02x%02x%02x' % c,
                                                width=0, tags=('sfondo',))
                    canvas.tag_lower('sfondo')
            except Exception as e:
                print(f"⚠️ sfondo sfumato: {e}")
            canvas.place(relx=0, rely=1.0, anchor='sw', relwidth=1.0)
            self._raise_widget(canvas)  # ✅ il testo sta SEMPRE sopra l'immagine overlay
        self.overlay_canvas = canvas
        self._ovl_trasparente = trasp
        canvas.update_idletasks()

        canvas_width = canvas.winfo_width()
        if canvas_width <= 1:
            canvas_width = max(1, self.window.winfo_width())

        speed = self.overlay_config["speed"]
        anchor = 'center' if speed == 0 else 'w'
        x_pos = canvas_width // 2 if speed == 0 else canvas_width
        self.overlay_x_pos = float(x_pos)
        self._overlay_x_disegnato = int(x_pos)
        self._overlay_t = None

        # il testo si rifa' ogni volta (in trasparente ha anche il bordo nero): tutti i pezzi hanno
        # il tag 'tsc' e scorrono insieme
        for c in (self._ovl_normale, getattr(self, '_ovl_cv', None)):
            try:
                if c is not None:
                    c.delete('tsc')
            except Exception:
                pass
        font = ("Arial", font_size, "bold")
        t = self.overlay_config["testo"]
        # [21-10-2026] utente: "#0060FF con i bordi sfumati di rosso", da impostare a mano: nel campo
        # "Colore testo" si possono scrivere DUE colori, "#0060FF,#FF0000" = testo, bordo. Il bordo
        # e' SFUMATO: tre anelli, il colore pieno vicino alle lettere e sempre piu' scuro fuori.
        # Senza secondo colore: come prima (in trasparente un bordo nero per leggersi sul video).
        parti = [p for p in str(color or '').replace(';', ',').replace(' ', ',').split(',') if p.strip()]
        colore_testo = parti[0].strip() if parti else '#FFD700'
        bordo = parti[1].strip() if len(parti) > 1 else None
        if len(parti) >= 3:
            # utente: "il rosso lo voglio mettere prima e dopo": "#FF0000,#0060FF,#FF0000" =
            # bordo, TESTO, bordo (quello in mezzo e' il testo)
            colore_testo, bordo = parti[1].strip(), parti[0].strip()
        try:
            canvas.winfo_rgb(colore_testo)
        except Exception:
            colore_testo = '#FFD700'
        if bordo:
            try:
                r, g, b = (v // 257 for v in canvas.winfo_rgb(bordo))
            except Exception:
                bordo = None
        o = max(2, int(font_size) // 16)
        anelli = []
        if bordo:
            # dal piu' esterno (scuro) al piu' interno (pieno): disegnati in quest'ordine
            for k, luce in ((3, 0.30), (2, 0.60), (1, 1.0)):
                anelli.append((o * k, '#%02x%02x%02x' % (int(r * luce), int(g * luce), int(b * luce))))
        elif trasp:
            anelli.append((o, '#000000'))
        for off, col in anelli:
            for dx in (-off, 0, off):
                for dy in (-off, 0, off):
                    if dx or dy:
                        canvas.create_text(x_pos + dx, height // 2 + dy, text=t, fill=col,
                                           font=font, anchor=anchor, tags=('tsc',))
        self.overlay_text_id = canvas.create_text(x_pos, height // 2, text=t, fill=colore_testo,
                                                  font=font, anchor=anchor, tags=('tsc',))
        print(f"🔍 Testo {'TRASPARENTE' if trasp else 'su striscia'}: id={self.overlay_text_id}, x={x_pos}")

        if sfumata:
            # striscia sfumata in alto (finestrella con trasparenza vera): la striscia Tk sparisce
            try:
                self._sfu_finestra()
                self._sfu_prepara(height, tappe, t, font_size, colore_testo, anelli)
                W = self._sfu_geo[0]
                self._sfu_tx = (W - self._sfu_txt.width) // 2 if speed == 0 else W
                self.overlay_x_pos = float(self._sfu_tx)
                self._overlay_x_disegnato = int(self._sfu_tx)
                self._sfu_disegna(self._sfu_tx)        # prima il disegno, poi si mostra
                self._sfu_win.deiconify()
                self._sfu_disegna(self._sfu_tx)
                self._sfu_davanti()
                canvas.place_forget()
                self._sfu_on = True
                self._sfu_via = False
                print(f"🔍 Striscia SFUMATA in alto: {W}x{self._sfu_geo[1]}")
            except Exception as e:
                print(f"⚠️ striscia sfumata non disponibile, resta la striscia normale: {e}")
                self._sfu_nascondi()
                canvas.place(relx=0, rely=1.0, anchor='sw', relwidth=1.0)

        if speed > 0 or getattr(self, '_sfu_on', False):
            self._animate_overlay()
        self._refresh_image_for_text_bar()  # l'immagine si ferma sopra la striscia
        print(f"✅ Overlay testo pubblico attivo: {testo[:50]}...")

    def hide_text_overlay(self):
        """Nascondi overlay testo"""
        self.overlay_enabled = False
        try:
            if self._overlay_animation_job is not None:
                self.window.after_cancel(self._overlay_animation_job)
        except Exception:
            pass
        self._overlay_animation_job = None
        self._sfu_nascondi()
        try:
            (getattr(self, '_ovl_normale', None) or self.overlay_canvas).place_forget()
        except Exception:
            pass
        try:
            if getattr(self, '_ovl_win', None) is not None:
                self._ovl_win.withdraw()
        except Exception:
            pass
        self._refresh_image_for_text_bar()  # striscia via: l'immagine torna piena
        print("ℹ️ Overlay testo pubblico nascosto")

    def _animate_overlay(self):
        """Animazione scorrimento.

        [21-10-2026] utente: "il testo scorrevole scorre a scatti anziche' in modo fluido".
        Misurato: prima 3 px ogni 50 ms, che il timer di Windows (15,6 ms) faceva diventare
        62,5 ms -> 16 passi al secondo da 3 px = scatti. Ora ~60 passi al secondo da ~1 px, e
        la posizione viene dal TEMPO trascorso: un ritardo della finestra non rallenta il testo.
        Stessa velocita' che si VEDEVA prima: `speed` px ogni 62,5 ms (i 50 ms chiesti, allungati
        dal timer di Windows) = speed*16 px al secondo."""
        self._overlay_animation_job = None
        if getattr(self, '_sfu_on', False) and self.overlay_enabled:
            return self._sfu_passo()
        if not self.overlay_enabled or not self.visible:
            self._overlay_t = None
            return

        speed = max(0, int(self.overlay_config.get("speed", 3)))
        if speed <= 0:
            self._overlay_t = None
            return

        _timer_1ms()
        adesso = time.perf_counter()
        prima = getattr(self, '_overlay_t', None)
        passo = (1.0 / 60.0) if (prima is None or adesso - prima > 0.25) else (adesso - prima)
        self._overlay_t = adesso

        try:
            cv = self.overlay_canvas
            self.overlay_x_pos -= speed * 16.0 * passo
            canvas_width = cv.winfo_width()
            if canvas_width <= 1:
                canvas_width = max(1, self.window.winfo_width())
            bbox = cv.bbox('tsc')
            if bbox and bbox[2] < 0:
                self.overlay_x_pos = float(canvas_width)
            nuovo = int(round(self.overlay_x_pos))
            dx = nuovo - getattr(self, '_overlay_x_disegnato', nuovo)
            if dx:
                cv.move('tsc', dx, 0)
                self._overlay_x_disegnato = nuovo
            if getattr(self, '_ovl_trasparente', False):
                # ogni quarto di secondo: davanti al monitor (che KaraDom rialza) e lo segue se si sposta
                self._ovl_conta = getattr(self, '_ovl_conta', 0) + 1
                if self._ovl_conta % 4 == 0:
                    self._ovl_davanti()
                if self._ovl_conta % 15 == 0:
                    self._ovl_posiziona(self.overlay_config.get("font_size", 50) + 40)
        except Exception:
            pass

        if self.overlay_enabled and self.visible:
            self._overlay_animation_job = self.window.after(16, self._animate_overlay)
'''


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_234', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False



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
    if _spenta():
        return False
    try:
        import moduli.karaoke_monitor as km
        if getattr(km, '_timer_1ms', None) is not None:
            print('[234] testo scorrevole gia\' fluido nel programma')
            return True
        M = km.MonitorPubblico
        if getattr(M, '_ver234', None) == _VER:
            return True
        ns = {'tk': tk, 'sys': sys, 'time': time, '_timer_1ms': _timer_1ms}
        exec(compile(_BLOCCO, 'karaoke_monitor (patch 234)', 'exec'), ns)
        for k, v in ns['_Nuovi'].__dict__.items():
            if k.startswith('__'):
                continue
            if not hasattr(M, '_o234_' + k) and k in M.__dict__:
                setattr(M, '_o234_' + k, M.__dict__[k])
            setattr(M, k, v)
        M._ver234 = _VER
        print('[234] testo scorrevole fluido (60 passi al secondo) + sfondo trasparente (alpha 00)')
        return True
    except Exception as e:
        print('[234] %s' % e)
        return False
