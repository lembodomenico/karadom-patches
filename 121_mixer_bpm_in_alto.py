import os


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_121', '1')) == '0'
    except Exception:
        return False


def _bpm_da_file(path):
    try:
        import mido
        mid = mido.MidiFile(path)
        for tr in mid.tracks:
            for msg in tr:
                if msg.type == 'set_tempo':
                    return int(round(mido.tempo2bpm(msg.tempo)))
    except Exception as e:
        print('[BPM121] lettura file:', e)
    return 0


def apply():
    if _spenta():
        return False
    import sys
    import tkinter as tk
    mx = sys.modules.get('moduli.mixer')
    if mx is None:
        try:
            import moduli.mixer as mx  # noqa
        except Exception:
            print('[BPM121] mixer non presente (ok)')
            return False
    P = getattr(mx, 'MIDIMixerPanel', None)
    if P is None or getattr(P, '_bpm121', False):
        return True

    def _walk(w, out):
        for c in w.winfo_children():
            out.append(c)
            _walk(c, out)

    def _find_header(self):
        root = getattr(self, 'mixer_frame', None)
        if root is None:
            return None
        allw = []
        try:
            _walk(root, allw)
        except Exception:
            return None
        for c in allw:
            try:
                if isinstance(c, tk.Label) and 'MIXER' in (c.cget('text') or '').upper():
                    return c.master
            except Exception:
                pass
        return None

    def _ensure_bpm(self):
        lbl = getattr(self, 'bpm_label', None)
        ok = False
        try:
            ok = bool(lbl) and lbl.winfo_exists()
        except Exception:
            ok = False
        if not ok:
            hdr = _find_header(self)
            if hdr is None:
                return
            self.bpm_label = tk.Label(hdr, text='♩ -- BPM', bg='#0d0d0d',
                                      fg='#ffd166', font=('Arial', 11, 'bold'))
            self.bpm_label.pack(side='right', padx=12)
        bpm = int(getattr(self, '_bpm121_val', 0) or 0)
        if not bpm:
            try:
                t = getattr(self._get_midi_player(), 'tempo', None)
                if t and t > 0:
                    bpm = int(round(60000000.0 / t))
            except Exception:
                pass
        try:
            self.bpm_label.config(text=('♩ %d BPM' % bpm if bpm else '♩ -- BPM'))
        except Exception:
            pass

    # 1) al caricamento del brano leggo i BPM dal FILE (sicuro)
    if hasattr(P, 'load_midi_file'):
        _orig_load = P.load_midi_file

        def load_midi_file(self, midi_path, *a, **k):
            r = _orig_load(self, midi_path, *a, **k)
            try:
                self._bpm121_val = _bpm_da_file(midi_path)
                # diagnostica: quale player suona davvero (serve per i bassi)
                try:
                    p = self._get_midi_player()
                    print('[BPM121] %s -> %d BPM | player=%s tempo=%s' % (
                        os.path.basename(str(midi_path)), self._bpm121_val,
                        type(p).__name__ if p else None, getattr(p, 'tempo', None)))
                except Exception:
                    print('[BPM121] %s -> %d BPM' % (os.path.basename(str(midi_path)), self._bpm121_val))
                _ensure_bpm(self)
            except Exception as e:
                print('[BPM121] load:', e)
            return r

        P.load_midi_file = load_midi_file

    # 2) il poll tiene l'etichetta creata e aggiornata
    _orig_poll = P._poll_activity

    def _poll_activity(self):
        try:
            _ensure_bpm(self)
        except Exception as e:
            print('[BPM121]', e)
        return _orig_poll(self)

    P._poll_activity = _poll_activity
    P._bpm121 = True
    print('[BPM121] attiva: BPM dal file, in alto a destra')
    return True


def revert():
    pass


try:
    apply()
except Exception as _e:
    print('patch 121: %s' % _e)
