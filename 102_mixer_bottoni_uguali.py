# 102 - Mixer: i bottoni EXPANDER e CARICA SF2 hanno la stessa larghezza
def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_102', '1')) == '0'
    except Exception:
        return False


def apply():
    if _spenta():
        return False
    import sys
    mod = sys.modules.get('moduli.mixer')
    if mod is None:
        try:
            import moduli.mixer as mod  # noqa
        except Exception:
            print('patch 102: mixer non presente (ok)')
            return False
    P = getattr(mod, 'MIDIMixerPanel', None)
    if P is None or getattr(P, '_btn_uguali_102', False):
        return True
    if not hasattr(P, '_create_ui'):
        return True

    import tkinter as tk

    def _equalizza(root):
        try:
            for w in root.winfo_children():
                try:
                    if isinstance(w, tk.Button):
                        t = w.cget('text') or ''
                        if ('EXPANDER' in t) or ('CARICA SF2' in t) or ('SF2' in t):
                            w.configure(width=12)
                except Exception:
                    pass
                _equalizza(w)
        except Exception:
            pass

    _orig = P._create_ui
    def _create_ui(self, *a, **k):
        r = _orig(self, *a, **k)
        try:
            _equalizza(self.mixer_frame)
        except Exception as e:
            print('patch 102:', e)
        return r
    P._create_ui = _create_ui
    P._create_ui_orig_102 = _orig

    # etichetta SF: col software expander scrive "KaraDom Expander" (non "loopMIDI Port")
    if hasattr(P, '_update_soundfont_display'):
        _orig_sf = P._update_soundfont_display
        def _update_soundfont_display(self, *a, **k):
            r = _orig_sf(self, *a, **k)
            try:
                lbl = getattr(self, 'sf_label', None)
                if lbl is not None:
                    t = lbl.cget('text') or ''
                    if 'loop' in t.lower() or 'expander software' in t.lower():
                        lbl.config(text="Expander Software", fg='#c77dff')
            except Exception:
                pass
            return r
        P._update_soundfont_display = _update_soundfont_display
        P._update_sf_orig_102 = _orig_sf

    P._btn_uguali_102 = True
    print('[MIX] patch 102: bottoni uguali + etichetta "KaraDom Expander"')
    return True


def revert():
    try:
        import sys
        mod = sys.modules.get('moduli.mixer')
        P = getattr(mod, 'MIDIMixerPanel', None) if mod else None
        if P is not None and getattr(P, '_btn_uguali_102', False):
            if hasattr(P, '_create_ui_orig_102'):
                P._create_ui = P._create_ui_orig_102
            del P._btn_uguali_102
    except Exception:
        pass


try:
    apply()
except Exception as _e:
    print('patch 102: %s' % _e)
