# 001 - ogni aggiornamento resta in funzione

import os

_VER = 1


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_001', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def apply():
    """Ogni patch si esegue UNA volta per avvio, comunque sia andata.

    Prima: una patch entrava nell'elenco delle eseguite (hotfix.APPLICATE) solo se rispondeva
    "si'". Se rispondeva "no" - anche solo perche' un pezzo non le era riuscito - al giro
    successivo (splash, aggiornamenti scaricati) veniva RIESEGUITA da capo e rimetteva le sue
    funzioni sopra quelle delle patch venute dopo, cancellandole (es. la 034 rimetteva il suo
    play_brano sopra la 198). Ora la si segna come eseguita in ogni caso: nessuna patch puo'
    piu' scavalcare le altre nello stesso avvio. Le versioni NUOVE scaricate entrano al
    riavvio (avviso della 219), le patch nuove si applicano subito come prima."""
    if _spenta():
        return False
    try:
        from moduli import hotfix as H
    except Exception:
        import hotfix as H
    if getattr(H, '_ver001', None) == _VER:
        return True
    if not hasattr(H, 'APPLICATE'):
        H.APPLICATE = set()
    orig = getattr(H, '_o001_esegui', None) or getattr(H, '_esegui_apply', None)
    if orig is None:
        return False
    H._o001_esegui = orig

    def _esegui_apply(ns, nome, _log, *a, **k):
        try:
            return orig(ns, nome, _log, *a, **k)
        finally:
            try:
                H.APPLICATE.add(os.path.basename(str(nome)))
            except Exception:
                pass

    H._esegui_apply = _esegui_apply
    H._ver001 = _VER
    print('[001] ogni patch si esegue una volta sola per avvio')
    return True


try:
    apply()
except Exception:
    pass
