import os
import re
import threading


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_136', '1')) == '0'
    except Exception:
        return False


_DELTA_EXT = {'.mp3','.mp4','.avi','.mkv','.flv','.wav','.flac','.aac','.ogg',
              '.wma','.m4a','.webm','.mov','.wmv','.mpg','.mpeg','.mid','.midi',
              '.kar','.kfn','.mkf','.m4v','.aiff','.aif','.opus','.ape','.m4b',
              '.mp2','.ra','.rm','.mka','.3gp'}


def _file_mtimes(self, cartella):
    f = self._file_cache_brani(cartella)
    return (f[:-7] + ".mtimes.gz") if f and f.endswith(".txt.gz") else None


def _delta_preferito(self, cartella):
    def _lav():
        import gzip, json, time as _t
        try:
            base = self._leggi_cache_disco(cartella)
            if base is None:
                return  # prima volta: ci pensa carica_brani (scansione completa)
            base_set = set(base)
            mf = _file_mtimes(self, cartella)
            vecchie = {}
            if mf and os.path.exists(mf):
                try:
                    with gzip.open(mf, "rt", encoding="utf-8") as h:
                        vecchie = json.load(h)
                except Exception:
                    vecchie = {}
            nuove = {}; nuovi = []; viste = 0
            stack = [cartella]
            while stack:
                d = stack.pop()
                try:
                    st = os.stat(d).st_mtime
                except Exception:
                    continue
                nuove[d] = st
                cambiata = (vecchie.get(d) != st)
                try:
                    with os.scandir(d) as it:
                        for e in it:
                            viste += 1
                            if viste % 3000 == 0:
                                _t.sleep(0.002)
                            try:
                                if e.is_dir(follow_symlinks=False):
                                    stack.append(e.path)
                                elif cambiata and e.is_file(follow_symlinks=False):
                                    if os.path.splitext(e.name)[1].lower() in _DELTA_EXT and e.path not in base_set:
                                        nuovi.append(e.path)
                            except Exception:
                                continue
                except Exception:
                    continue

            if mf:
                try:
                    with gzip.open(mf, "wt", encoding="utf-8") as h:
                        json.dump(nuove, h)
                except Exception:
                    pass

            if not nuovi:
                return

            aggiornata = base + nuovi
            voci_nuove = [self._voce_brano(p) for p in nuovi]
            idx_nuovo = {}
            for p in nuovi:
                senza = os.path.splitext(os.path.basename(p))[0].lower()
                idx_nuovo[p] = re.findall(r"[a-zA-Z0-9àèéìòóù]+", senza)

            def _appl():
                if os.path.normpath(getattr(self, 'percorso_attivo', '') or '').lower() \
                   != os.path.normpath(cartella).lower():
                    return
                try:
                    self.brani_completi = (self.brani_completi or []) + nuovi
                    self.brani_pc = (self.brani_pc or []) + voci_nuove
                    if getattr(self, 'indice_preferiti', None) is None:
                        self.indice_preferiti = {}
                    self.indice_preferiti.update(idx_nuovo)
                    cache = getattr(self, "_cache_brani", None)
                    if cache is not None:
                        chiave = os.path.normpath(cartella).lower()
                        cache[chiave] = (self.brani_completi, self.brani_pc, self.indice_preferiti)
                    print("[DELTA136] +%d brani nuovi in %s" % (len(nuovi), cartella))
                except Exception as e:
                    print("[DELTA136] applica:", e)

            try:
                self.parent.after(0, _appl)
            except Exception:
                pass
            try:
                self._scrivi_cache_disco(cartella, aggiornata)
            except Exception:
                pass
        except Exception as e:
            print("[DELTA136]", e)

    threading.Thread(target=_lav, daemon=True).start()


def apply():
    if _spenta():
        return False
    try:
        import moduli.libreria as lib
        C = getattr(lib, 'LibreriaSlider', None)
        if C is None or getattr(C, '_delta136', False):
            return True
        C._delta_preferito = _delta_preferito
        _oc = C.carica_brani

        def _wrap(self, cartella, forza=False, *a, **k):
            r = _oc(self, cartella, forza, *a, **k)
            if not forza:
                try:
                    _delta_preferito(self, cartella)
                except Exception:
                    pass
            return r

        C.carica_brani = _wrap
        C._delta136 = True
        print('[DELTA136] posizionandoti su un preferito aggiorna solo il delta (background)')
    except Exception as e:
        print('[DELTA136] hook:', e)
    return True


def revert():
    pass


try:
    apply()
except Exception as _e:
    print('patch 136: %s' % _e)
