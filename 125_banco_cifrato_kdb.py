import os, ctypes

DWORD = ctypes.c_uint32


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_125', '1')) == '0'
    except Exception:
        return False


def _e_kdl(p):
    try:
        return p.lower().endswith('.kdl')
    except Exception:
        return False


def apply():
    if _spenta():
        return False

    # I file .kdl sono SF2 IN CHIARO con estensione diversa: FontInit diretto (C),
    # nessuna decifra/temp -> audio pulito come un .sf2 normale.
    try:
        import moduli.bass_engine as be
        BE = getattr(be, 'BassEngine', None)
        if BE and not getattr(BE, '_kdl125', False):
            _orig = BE._load_soundfont

            def _load_sf(self, sf_path):
                p = str(sf_path)
                if _e_kdl(p) and os.path.exists(p):
                    m = getattr(be, '_lib', None)
                    m = getattr(m, 'bassmidi', None) if m else None
                    if not m:
                        return False
                    m.BASS_MIDI_FontInit.restype = DWORD
                    m.BASS_MIDI_FontInit.argtypes = [ctypes.c_void_p, DWORD]
                    font = m.BASS_MIDI_FontInit(ctypes.c_wchar_p(p), 0x80000000)  # UNICODE
                    if not font:
                        font = m.BASS_MIDI_FontInit(p.encode('mbcs'), 0)
                    if not font:
                        print('[KDL125] FontInit .kdl fallito'); return False
                    self._font = font
                    self._soundfont_path = p
                    print('[KDL125] banco .kdl (SF2 in chiaro) caricato diretto (font=%s)' % font)
                    return True
                return _orig(self, sf_path)

            BE._load_soundfont = _load_sf
            BE._kdl125 = True
    except Exception as e:
        print('[KDL125] hook load:', e)

    # nascondi la scelta del banco nella finestra Expander (106)
    try:
        import moduli.expander_gui as eg
        F = getattr(eg, 'FinestraExpander', None)
        if F and hasattr(F, '_costruisci') and not getattr(F, '_kdl125', False):
            _oc = F._costruisci

            def _c(self):
                _oc(self)
                try:
                    ws = []

                    def walk(w):
                        for ch in w.winfo_children():
                            ws.append(ch); walk(ch)
                    walk(self.win)
                    for w in ws:
                        try:
                            cls = w.winfo_class()
                            txt = (w.cget('text') or '').lower() if cls in ('Button', 'Label') else ''
                        except Exception:
                            continue
                        if cls in ('Button', 'Label') and 'banco' in txt:
                            try:
                                w.pack_forget()
                            except Exception:
                                pass
                except Exception as e:
                    print('[KDL125] ui:', e)

            F._costruisci = _c
            F._kdl125 = True
    except Exception as e:
        print('[KDL125] gui:', e)

    print('[KDL125] expander: banco .kdl in chiaro, FontInit diretto; scelta nascosta')
    return True


def revert():
    pass


try:
    apply()
except Exception as _e:
    print('patch 125: %s' % _e)
