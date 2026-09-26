def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_127', '1')) == '0'
    except Exception:
        return False


def _secondi():
    # tempo massimo per aprire la porta dell'expander fisico (una volta sola).
    try:
        from moduli.database import Database
        v = Database.get_config('exp_open_timeout', '8')
        return max(3.0, min(20.0, float(v)))
    except Exception:
        return 8.0


def _preapri_bg():
    # Apre e mette in CACHE la porta dell'expander FISICO fuori dal thread UI,
    # cosi' al primo Play e' gia' pronta (niente ritardo del primo brano).
    try:
        import moduli.expander_midi as ex
        if hasattr(ex, 'get_mode') and str(ex.get_mode()) == 'off':
            return
        if getattr(ex, 'is_active', None) and ex.is_active():
            return  # gia' aperta
        porta = ex.detect_expander() if hasattr(ex, 'detect_expander') else None
        nome = (porta or {}).get('nome', '') or ''
        if not porta or porta.get('id', -1) == -1 or 'software' in nome.lower():
            return  # niente expander FISICO: non pre-apro (non tocco il software)
        p = ex.get_expander_player()   # apre la porta e la mette in cache
        if p is not None:
            print('[EXP127] porta expander pre-aperta in background: %s '
                  '(nessun ritardo al primo brano)' % nome)
    except Exception as e:
        print('[EXP127] pre-apertura bg:', e)


def apply():
    if _spenta():
        return False
    t = _secondi()

    # 1) apertura dello STREAM winmm (midi_stream): timeout a livello di modulo
    try:
        import moduli.midi_stream as ms
        ms.ATTESA_DRIVER = t
        print('[EXP127] midi_stream.ATTESA_DRIVER = %.1fs' % t)
    except Exception as e:
        print('[EXP127] midi_stream:', e)

    # 2) apertura della PORTA winmm diretta (_UscitaMIDI in expander_midi)
    try:
        import moduli.expander_midi as ex
        cls = getattr(ex, '_UscitaMIDI', None)
        if cls is not None:
            cls.ATTESA_APERTURA = t
            print('[EXP127] _UscitaMIDI.ATTESA_APERTURA = %.1fs' % t)
        else:
            print('[EXP127] _UscitaMIDI non trovata (ok)')
    except Exception as e:
        print('[EXP127] expander_midi:', e)

    # 3) pre-apertura in background: al primo Play la porta e' gia' pronta.
    #    Due tentativi (6s e 15s) per dare tempo al rilevamento porte (062/115).
    try:
        import threading
        threading.Timer(6.0, _preapri_bg).start()
        threading.Timer(15.0, _preapri_bg).start()
        print('[EXP127] pre-apertura porta expander programmata (6s / 15s)')
    except Exception as e:
        print('[EXP127] scheduling pre-apertura:', e)

    print('[EXP127] expander fisico: piu\' tempo per aprire la porta al primo colpo '
          '(poi resta in cache) + pre-apertura in background; nessun effetto sui PC '
          'che aprono subito ne\' sul software')
    return True


def revert():
    pass


try:
    apply()
except Exception as _e:
    print('patch 127: %s' % _e)
