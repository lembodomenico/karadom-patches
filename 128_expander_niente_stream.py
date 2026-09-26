def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_128', '1')) == '0'
    except Exception:
        return False


def apply():
    if _spenta():
        return False

    # torna all'INVIO DIRETTO (metodo 5.3.10): la modalita' stream, aggiunta con
    # l'expander, su alcuni X-Light fa suonare male (i cambi strumento/SysEx dei
    # banchi M-Live arrivano dopo le note pre-consegnate). expander_stream=0 =
    # tutto in ordine, come prima dell'expander.
    try:
        from moduli.database import Database
        Database.set_config('expander_stream', '0')
        print('[EXP128] stream MIDI expander DISABILITATO -> invio diretto (metodo 5.3.10)')
    except Exception as e:
        print('[EXP128] set config:', e)
        return False

    # se un player expander e' gia' aperto in stream, lo chiudo: al prossimo brano
    # si riapre in diretto.
    try:
        import moduli.expander_midi as ex
        if hasattr(ex, 'reset_player'):
            ex.reset_player()
    except Exception as e:
        print('[EXP128] reset_player:', e)

    return True


def revert():
    try:
        from moduli.database import Database
        Database.set_config('expander_stream', '1')
    except Exception:
        pass


try:
    apply()
except Exception as _e:
    print('patch 128: %s' % _e)
