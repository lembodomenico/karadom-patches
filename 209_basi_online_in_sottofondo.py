# 209 - basi online: scaricamento in sottofondo quando si preme play

_VER = 1
CODICE_BASI = '\n# ── [11-10-2026] scaricamento in sottofondo (prima: dentro play_brano, finestra ferma fino a 120 s) ──\n_scaricate = {}          # db_id -> percorso gia\' scaricato in questa sessione (si riusa)\n_in_corso = set()\n\n\ndef scarica_in_sfondo(parent, db_id, quando_pronta, avvisa=None):\n    """Scarica la base online in un thread e chiama quando_pronta(percorso|None) sul thread\n    della finestra. Una base gia\' scaricata in questa sessione si riusa subito."""\n    import os\n    import tempfile\n    import threading\n    gia = _scaricate.get(db_id)\n    if gia and os.path.exists(gia):\n        quando_pronta(gia)\n        return\n    if db_id in _in_corso:\n        if avvisa:\n            avvisa("⏳ Sto gia\' scaricando questa base...")\n        return\n    _in_corso.add(db_id)\n    if avvisa:\n        avvisa("⏳ Scarico la base...")\n\n    def _lavoro():\n        res = None\n        try:\n            suffix = \'.mp4\' if is_video(db_id) else \'.mp3\'\n            fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix=\'kdm_\')\n            os.close(fd)\n            res = scarica(db_id, temp_path)\n        except Exception as e:\n            print(f"[basi_online] scarica in sfondo: {e}")\n        finally:\n            _in_corso.discard(db_id)\n        if res:\n            _scaricate[db_id] = res\n        try:\n            parent.after(0, lambda: quando_pronta(res))\n        except Exception:\n            quando_pronta(res)\n\n    threading.Thread(target=_lavoro, name=\'BaseOnline\', daemon=True).start()\n'
CODICE_PLAY = '\ndef avvolgi_play_brano(classe):\n    """Avvolge LibreriaSlider.play_brano: \'kdmonline://\' -> scaricamento in sottofondo, poi play."""\n    if getattr(classe.play_brano, \'_bo209\', False):\n        return                          # gia\' avvolta (e nessuno l\'ha rimpiazzata dopo)\n    vera = classe.play_brano            # quella che c\'e\' ADESSO (la 032 la rimette a ogni passaggio)\n\n    def play_brano(self, path, entry_ton=None, cantante="", brano="", tonalita=None, *a, **k):\n        if isinstance(path, str) and path.startswith(\'kdmonline://\'):\n            db_id = path[len(\'kdmonline://\'):]\n            # la tonalita\' della riga si legge ADESSO (la riga puo\' cambiare mentre si scarica)\n            if tonalita is None and entry_ton is not None:\n                try:\n                    tonalita = int(entry_ton.get().strip() or "0")\n                except Exception:\n                    tonalita = None\n\n            def _avvisa(testo):\n                try:\n                    ref = getattr(self, \'info_brano_ref\', None) or {}\n                    if ref.get(\'brano\'):\n                        ref[\'brano\'].config(text=testo)\n                except Exception:\n                    pass\n                print(f"[basi_online] {testo}")\n\n            def _pronta(percorso):\n                if not percorso:\n                    try:\n                        from tkinter import messagebox\n                        messagebox.showerror("Errore", "Impossibile scaricare il brano online.\\nVerifica la connessione o la licenza.",\n                                             parent=self.parent)\n                    except Exception:\n                        pass\n                    return\n                vera(self, percorso, None, cantante, brano, tonalita, *a, **k)\n\n            import sys\n            mod = sys.modules.get(\'moduli.basi_online\')\n            if mod is None:\n                from moduli import basi_online as mod\n            mod.scarica_in_sfondo(self.parent, db_id, _pronta, _avvisa)\n            return None\n        return vera(self, path, entry_ton, cantante, brano, tonalita, *a, **k)\n\n    play_brano._bo209 = True\n    classe.play_brano = play_brano\n'


# PER ORA SOLO SUI PC DEL GESTORE (DOMMSI, DOMHP, KARADOM, KaraDomOS): sugli altri non fa niente
SOLO_SERIALI = ('1A55-2CD1-3303-20EB', '64D4-81C3-65D3-C024', '0182-5846-232C-930E', '4D8E-F63F-45E1-8F06')


def _pc_del_gestore():
    import sys
    gia = getattr(sys, '_kd_pc_del_gestore', None)
    if gia is None:
        try:
            from moduli.licensing import get_hardware_id, generate_serial
            c, m = get_hardware_id()
            gia = generate_serial(c, m) in SOLO_SERIALI
        except Exception:
            gia = False
        sys._kd_pc_del_gestore = gia
    return gia


def _spenta():
    if not _pc_del_gestore():
        return True
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_209', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def apply():
    if _spenta():
        return False
    try:
        from moduli import basi_online as B
        from moduli import libreria as L
    except Exception:
        return False
    if not hasattr(B, 'scarica_in_sfondo'):
        exec(compile(CODICE_BASI, '<patch209 basi>', 'exec'), B.__dict__)
    K = getattr(L, 'LibreriaSlider', None)
    if K is None:
        return False
    if getattr(K, '_ver209_sorgente', False):
        return True
    ns = {}
    exec(compile(CODICE_PLAY, '<patch209 play>', 'exec'), ns)
    ns['avvolgi_play_brano'](K)
    return True


def revert():
    return False


try:
    apply()
except Exception:
    pass
