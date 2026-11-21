# 257 - syncro text salva come salva brano

_VER = 1

# [21-11-2026] Utente: "in KaraDom nella sezione Syncro Text alla fine quando salvi lo devi fare come fa il Salva
# Brano di KaraDom stesso" + "la modifica deve arrivare a tutti, anche chi ha la versione di prova" (niente filtro
# titolare). Il Syncro Text dei programmi installati scrive il testo sincronizzato UTF-16 (lang 'ita'): gli altri
# programmi karaoke non lo leggono. Salva Brano invece scrive SYLT LATIN1, lang 'XXX', desc 'KaraDom', formato 2,
# tipo 1, ID3 v2.3 senza padding. (La correzione era nel sorgente dal 22-10 ma la patch, numerata 251, non e' mai
# stata pubblicata.)
# Come: durante il salvataggio del Syncro Text si annotano i file MP3 che mutagen scrive; finito il salvataggio,
# il SYLT di quei file viene riscritto ESATTAMENTE come Salva Brano (stesse sillabe e tempi, solo la codifica).
# Sui programmi gia' corretti il risultato e' identico (riscrittura uguale).

import threading


def _log(msg):
    try:
        print('[257] %s' % msg)
    except Exception:
        pass


_SOST = {'’': "'", '‘': "'", '‚': "'", 'ʼ': "'", '“': '"',
         '”': '"', '„': '"', '–': '-', '—': '-', '…': '...', ' ': ' '}
_annota = threading.local()


def _latin(t):
    return ''.join(_SOST.get(c, c) for c in str(t)).encode('latin-1', 'replace').decode('latin-1')


def _riscrivi(percorso):
    """SYLT del file -> formato Salva Brano (LATIN1/XXX/KaraDom/fmt 2/tipo 1, v2.3, padding 0)."""
    from mutagen.mp3 import MP3
    from mutagen.id3 import SYLT, Encoding
    audio = MP3(percorso)
    if audio.tags is None:
        return False
    fr = audio.tags.getall('SYLT')
    if not fr:
        return False
    testo = [(_latin(t), int(ms)) for t, ms in (fr[0].text or [])]
    if not testo:
        return False
    audio.tags.delall('SYLT')
    audio.tags.add(SYLT(encoding=Encoding.LATIN1, lang='XXX', format=2, type=1, desc='KaraDom', text=testo))
    audio.save(v2_version=3, padding=lambda info: 0)
    return True


def apply():
    try:
        from moduli.database import Database
        if str(Database.get_config('patch_257', '1')).strip() in ('0', 'no', 'off'):
            return False
    except Exception:
        pass
    try:
        import moduli.syncro_text as st
        from mutagen.id3 import ID3FileType, ID3
    except Exception as e:
        _log('moduli non trovati: %s' % e)
        return False
    C = getattr(st, 'SyncroText', None)
    if C is None or not hasattr(C, '_save_sylt'):
        _log('Syncro Text senza _save_sylt')
        return False
    if getattr(C, '_ver257', None) == _VER:
        return True

    # mutagen: annota i file scritti SOLO mentre salva il Syncro Text
    # stato condiviso appeso a mutagen: se la patch viene eseguita piu' volte nella stessa sessione,
    # i salvataggi annotati dal primo giro e il Syncro Text del secondo devono vedere la STESSA lista
    global _annota
    if getattr(ID3FileType, '_a257', None) is None:
        ID3FileType._a257 = _annota
    _annota = ID3FileType._a257
    for K in (ID3FileType, ID3):
        if getattr(K, '_o257_save', None) is None:
            K._o257_save = K.save

            def save(self, *a, _orig=K._o257_save, **kw):
                r = _orig(self, *a, **kw)
                try:
                    lista = getattr(_annota, 'file', None)
                    if lista is not None:
                        fn = (a[0] if a and isinstance(a[0], str) else None) or kw.get('filething') \
                            or getattr(self, 'filename', None)
                        if isinstance(fn, str) and fn.lower().endswith('.mp3') and fn not in lista:
                            lista.append(fn)
                except Exception:
                    pass
                return r
            K.save = save

    salva0 = getattr(C, '_o257_salva', None) or C._save_sylt
    C._o257_salva = salva0

    def _save_sylt(self, *a, **kw):
        _annota.file = []
        try:
            return salva0(self, *a, **kw)
        finally:
            fatti, _annota.file = list(_annota.file or []), None
            for fn in fatti:
                try:
                    if _riscrivi(fn):
                        _log('SYLT come Salva Brano: %s' % fn)
                except Exception as e:
                    _log('riscrittura non riuscita (%s): %s' % (fn, e))

    C._save_sylt = _save_sylt
    C._ver257 = _VER
    _log('Syncro Text: salvataggio come Salva Brano (v%d)' % _VER)
    return True
