# 234 - testo scorrevole del monitor pubblico FLUIDO + SFONDO TRASPARENTE
# [21-10-2026] utente: "il testo scorrevole scorre a scatti anziche' in modo fluido" (PC KARADOM .214)
# + "voglio vedere se e' possibile su sfondo trasparente".
# Fluido (misurato, D:\\Claude\\testo_scorrevole): prima 16 passi/s da 3 px (after(50) = 62,5 ms col
# timer di Windows), ora ~60 passi/s da ~0,8 px dal tempo trascorso + timeBeginPeriod(1); stessa velocita'.
# Trasparente: nel campo "Sfondo (HEX con alpha)" alpha 00 (es. #00000000) -> niente striscia, testo
# col bordo nero direttamente sul video (finestrella figlia del monitor con -transparentcolor).
# Codice preso dal sorgente moduli/karaoke_monitor.py (fai_patch_234.py): col compilato nuovo non serve.

_VER = 7

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
        self._ovl_proprietario()
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
        """Anche "sempre davanti" (una volta, senza prendere il fuoco): se per qualche motivo il
        legame col proprietario non bastasse, il testo non finisce comunque sotto il monitor."""
        try:
            import ctypes
            h, _hm = self._ovl_hwnd()
            ctypes.windll.user32.SetWindowPos(ctypes.c_void_p(h), ctypes.c_void_p(-1), 0, 0, 0, 0,
                                              0x0001 | 0x0002 | 0x0010)
        except Exception as e:
            print(f"⚠️ testo trasparente, davanti: {e}")

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

        if speed > 0:
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
                # ogni mezzo secondo: la finestrella segue il monitor se si e' spostato
                self._ovl_conta = getattr(self, '_ovl_conta', 0) + 1
                if self._ovl_conta % 30 == 0:
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


def apply():
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
