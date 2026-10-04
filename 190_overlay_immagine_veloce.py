# 190 - overlay immagine veloce
import os
import sys
import tkinter as tk


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_190', '1')) == '0'
    except Exception:
        return False


def show_image_overlay(self, image_path, size_frac=1.0):
    print(f"🔍 show_image_overlay chiamato: path={image_path}, size={size_frac}, visible={self.visible}")

    try:
        from PIL import Image, ImageTk

        self._image_overlay_path = image_path
        self._image_overlay_size = size_frac

        try:
            size_frac = max(0.05, min(1.0, float(size_frac)))
        except Exception:
            size_frac = 1.0

        self.monitor_frame.update_idletasks()
        frame_w = self.monitor_frame.winfo_width()
        frame_h = self.monitor_frame.winfo_height()
        if frame_w <= 1 or frame_h <= 1:
            frame_w = self.window.winfo_width() or self.window.winfo_screenwidth()
            frame_h = self.window.winfo_height() or self.window.winfo_screenheight()

        bar_h = self._text_overlay_height()
        area_h = max(1, frame_h - bar_h)

        try:
            _mt = os.path.getmtime(image_path)
        except Exception:
            _mt = 0
        _chiave = (image_path, _mt, frame_w, area_h, round(size_frac, 3))
        _cache = getattr(self, '_image_overlay_cache', None)
        if _cache is None:
            _cache = self._image_overlay_cache = {}
        if _chiave in _cache:
            self.image_photo = _cache[_chiave]
        else:
            img = Image.open(image_path)
            if img.format == 'JPEG':
                img.draft('RGB', (frame_w, area_h))
            img = img.convert("RGB")
            print(f"🔍 Immagine caricata: {img.size}  frame={frame_w}x{frame_h}")

            if size_frac >= 0.999:
                ratio = max(frame_w / img.width, area_h / img.height)
                rw, rh = max(1, int(img.width * ratio)), max(1, int(img.height * ratio))
                img = img.resize((rw, rh), Image.Resampling.LANCZOS, reducing_gap=3.0)
                left = max(0, (rw - frame_w) // 2)
                top = max(0, (rh - area_h) // 2)
                img = img.crop((left, top, left + frame_w, top + area_h))
                new_width, new_height = frame_w, area_h
            else:
                max_width = int(frame_w * size_frac)
                max_height = int(area_h * size_frac)
                ratio = min(max_width / img.width, max_height / img.height)
                new_width = max(1, int(img.width * ratio))
                new_height = max(1, int(img.height * ratio))
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS, reducing_gap=3.0)

            print(f"🔍 Ridimensionata: {new_width}x{new_height} (frac={size_frac})")
            self.image_photo = ImageTk.PhotoImage(img)
            if len(_cache) >= 3:
                _cache.pop(next(iter(_cache)))
            _cache[_chiave] = self.image_photo

        if not hasattr(self, 'image_label'):
            self.image_label = tk.Label(self.monitor_frame, image=self.image_photo,
                                        bg='#000000', bd=0, highlightthickness=0)
            print(f"🔍 Label creato")
        else:
            self.image_label.config(image=self.image_photo)
            print(f"🔍 Label aggiornato")
        self.image_label.place(relx=0.5, y=area_h // 2, anchor='center')
        self.image_label.lift()
        self._lift_text_overlay()

        self.image_overlay_enabled = True
        self._image_overlay_rendered_size = (frame_w, frame_h, bar_h)
        self._bind_image_overlay_resize()
        print(f"✅ Overlay immagine pubblico attivo: {image_path}")

    except Exception as e:
        print(f"⚠️ Errore caricamento immagine overlay: {e}")
        import traceback
        traceback.print_exc()


def apply():
    if _spenta():
        return False
    try:
        M = sys.modules.get('moduli.karaoke_monitor')
        if M is None:
            import moduli.karaoke_monitor as M
        C = M.MonitorPubblico
        if getattr(C, '_p190', False):
            return True
        C.show_image_overlay = show_image_overlay
        C._p190 = True
        return True
    except Exception as e:
        print('[patch190] non agganciata: %s' % e)
        return False


def revert():
    return False


try:
    apply()
except Exception:
    pass
