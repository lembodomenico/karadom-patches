import os
import threading
from concurrent.futures import ThreadPoolExecutor


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_134', '1')) == '0'
    except Exception:
        return False


_POOL = ThreadPoolExecutor(max_workers=3, thread_name_prefix="pref134")


def _drive_montato(path):
    # ISTANTANEO (niente I/O): il disco c'e' o no? Se l'unita' non e' montata NON si
    # tocca proprio (niente os.path.exists che si pianta sul disco assente).
    try:
        import ctypes
        d = os.path.splitdrive(os.path.abspath(path))[0]  # "D:"
        if not d or len(d) < 2 or d[1] != ':':
            return True   # UNC/rete o path strano: decide os.path.exists (col timeout)
        letter = d[0].upper()
        if not ('A' <= letter <= 'Z'):
            return True
        mask = ctypes.windll.kernel32.GetLogicalDrives()
        return bool(mask & (1 << (ord(letter) - ord('A'))))
    except Exception:
        return True


def _exists_timeout(path, t=2.0):
    # os.path.exists in un worker: se il disco (esterno/rete) e' scollegato e si pianta,
    # NON blocca oltre `t` secondi (il worker resta appeso ma noi proseguiamo).
    try:
        return bool(_POOL.submit(os.path.exists, path).result(timeout=t))
    except Exception:
        return False


def _disco_esterno_timeout(path, t=2.0):
    try:
        from moduli.disco_lento import disco_esterno
        return bool(_POOL.submit(disco_esterno, path).result(timeout=t))
    except Exception:
        return False


def apply():
    if _spenta():
        return False
    try:
        import moduli.libreria as lib
        from moduli.database import Database
        C = getattr(lib, 'LibreriaSlider', None)
        if C is None or getattr(C, '_pref134', False):
            return True

        def _popola(self):
            # UI (veloce): pulisci l'albero + tag colore
            try:
                for item in self.tree.get_children():
                    self.tree.delete(item)
            except Exception:
                return
            try:
                self.tree.tag_configure("disco_esterno", foreground="#ff9800")
            except Exception:
                pass
            try:
                prefs = Database.get_preferiti()
            except Exception:
                prefs = []

            def _lavoro():
                # thread di fondo: i controlli su disco NON bloccano la UI
                pronti = []
                for pref in prefs:
                    path = pref.get('path', '')
                    if not _drive_montato(path):
                        continue  # disco non collegato: si salta SUBITO (non si carica)
                    if not _exists_timeout(path, 2.0):
                        continue  # disco c'e' ma il percorso no/lento: lo salto (come prima)
                    tags = ()
                    mark = ""
                    if _disco_esterno_timeout(path, 2.0):
                        tags = ("disco_esterno",)
                        mark = "💾 "
                    pronti.append((pref.get('nome', path), path, tags, mark))

                def _inserisci():
                    try:
                        for nome, path, tags, mark in pronti:
                            node = self.tree.insert('', 'end', text="📁 %s%s" % (mark, nome),
                                                    values=(path,), open=False, tags=tags)
                            self.tree.insert(node, 'end', text='...')
                    except Exception as e:
                        print('[PREF134] insert:', e)
                try:
                    self.tree.after(0, _inserisci)
                except Exception:
                    pass

            threading.Thread(target=_lavoro, daemon=True).start()

        C.popola_albero = _popola
        C._pref134 = True
        print('[PREF134] preferiti caricati in background: avvio non si blocca sui dischi offline')
    except Exception as e:
        print('[PREF134] hook:', e)
    return True


def revert():
    pass


try:
    apply()
except Exception as _e:
    print('patch 134: %s' % _e)
