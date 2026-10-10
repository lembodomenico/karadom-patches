# 196 - avvio piu' rapido, aggiornamenti controllati dopo l'apertura

_VER = 1


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_196', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def _non_aspettare(secondi_max=8):
    return False


def apply():
    if _spenta():
        return False
    try:
        import moduli.updater as up
    except Exception:
        return False
    if getattr(up, '_patch_196', None) != _VER:
        if not hasattr(up, '_orig_196_aspetta_patch'):
            up._orig_196_aspetta_patch = getattr(up, 'aspetta_patch', None)
        up.aspetta_patch = _non_aspettare
        up._patch_196 = _VER
    try:
        import moduli.ui as U
        g = getattr(getattr(U, 'demo', None), '__globals__', None)
        if isinstance(g, dict) and 'ATTESA_MAX' in g and '_aspetta_download' in g:
            g['ATTESA_MAX'] = 0
    except Exception:
        pass
    return True


def revert():
    try:
        import moduli.updater as up
        o = getattr(up, '_orig_196_aspetta_patch', None)
        if o is not None:
            up.aspetta_patch = o
        up._patch_196 = None
    except Exception:
        pass
