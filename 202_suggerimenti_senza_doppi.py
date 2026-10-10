# 202 - nei suggerimenti ogni brano una volta sola

import os
import re
import threading

_VER = 1


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_202', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


_EXT = {'.mp3', '.mp4', '.avi', '.mkv', '.flv', '.wav', '.flac', '.aac', '.ogg',
        '.wma', '.m4a', '.webm', '.mov', '.wmv', '.mpg', '.mpeg', '.mid', '.midi',
        '.kar', '.kfn', '.mkf', '.m4v', '.aiff', '.aif', '.opus', '.ape', '.m4b',
        '.mp2', '.ra', '.rm', '.mka', '.3gp'}


def _k(p):
    return os.path.normcase(os.path.normpath(p))


def _senza_doppi(brani):
    visti, puliti = set(), []
    for p in brani:
        k = _k(p)
        if k not in visti:
            visti.add(k)
            puliti.append(p)
    return puliti


def _file_mtimes(self, cartella):
    f = self._file_cache_brani(cartella)
    return (f[:-7] + ".mtimes.gz") if f and f.endswith(".txt.gz") else None


def _delta_preferito(self, cartella):
    def _lav():
        import gzip, json, time as _t
        try:
            base = self._leggi_cache_disco(cartella)
            if base is None:
                return
            base_set = {_k(p) for p in base}
            mf = _file_mtimes(self, cartella)
            vecchie = {}
            if mf and os.path.exists(mf):
                try:
                    with gzip.open(mf, "rt", encoding="utf-8") as h:
                        vecchie = json.load(h)
                except Exception:
                    vecchie = {}
            nuove = {}
            nuovi = []
            viste = 0
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
                                    if os.path.splitext(e.name)[1].lower() in _EXT:
                                        k = _k(e.path)
                                        if k not in base_set:
                                            base_set.add(k)
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
                        cache[os.path.normpath(cartella).lower()] = (
                            self.brani_completi, self.brani_pc, self.indice_preferiti)
                    print("[DOPPI202] +%d brani nuovi in %s" % (len(nuovi), cartella))
                except Exception as e:
                    print("[DOPPI202] applica:", e)

            try:
                self.parent.after(0, _appl)
            except Exception:
                pass
            try:
                self._scrivi_cache_disco(cartella, aggiornata)
            except Exception:
                pass
        except Exception as e:
            print("[DOPPI202]", e)

    threading.Thread(target=_lav, daemon=True).start()


def apply():
    if _spenta():
        return False
    try:
        import moduli.libreria as lib
        C = getattr(lib, 'LibreriaSlider', None)
        if C is None:
            return True
        if getattr(C, '_doppi202', None) != _VER:
            o_leggi = getattr(C, '_doppi202_o_leggi', None) or C._leggi_cache_disco
            C._doppi202_o_leggi = o_leggi

            def _leggi_cache_disco(self, cartella):
                brani = o_leggi(self, cartella)
                if not brani:
                    return brani
                puliti = _senza_doppi(brani)
                if len(puliti) < len(brani):
                    print("[DOPPI202] elenco salvato: tolti %d brani doppi" % (len(brani) - len(puliti)))
                    try:
                        self._scrivi_cache_disco(cartella, puliti)
                    except Exception:
                        pass
                return puliti

            C._leggi_cache_disco = _leggi_cache_disco
            C._doppi202 = _VER
        # il controllo dei brani nuovi: il metodo della classe E quello che la 136 chiama dal suo modulo
        C._delta_preferito = _delta_preferito
        f = C.carica_brani
        for _ in range(10):
            g = getattr(f, '__globals__', None)
            if g is not None and '_delta_preferito' in g and g.get('_delta_preferito') is not _delta_preferito:
                g['_delta_preferito'] = _delta_preferito
            clo = getattr(f, '__closure__', None) or ()
            dentro = [c.cell_contents for c in clo if callable(getattr(c, 'cell_contents', None))]
            if not dentro:
                break
            f = dentro[0]
        print('[DOPPI202] suggerimenti senza brani doppi')
    except Exception as e:
        print('[DOPPI202] hook:', e)
    return True


def revert():
    pass


try:
    apply()
except Exception as _e:
    print('patch 202: %s' % _e)
