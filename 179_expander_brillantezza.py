def apply():
    # Lo "scalino" (parte alto poi si abbassa) e' l'auto-reg 159: parte a volume
    # pieno, MISURA il brano per qualche secondo, poi applica tono+volume -> gradino.
    # Il per-brano per forza misura DOPO l'avvio = scalino. Quindi lo spengo e uso
    # il TONO FISSO della 109, applicato all'ISTANTE al caricamento: costante dal
    # primo secondo, niente gradino. Carattere a "sorriso": acuti brillanti + bassi
    # pieni. 109: bright shelf 7kHz (valore-50)/50*12dB, bass 80Hz *15dB; vol resta
    # pieno (nessun duck) -> volume costante.
    try:
        from moduli.database import Database

        def setk(k, v):
            Database.set_config(k, v)

        # niente per-brano (159) e niente 170: solo la 109, tono fisso istantaneo
        setk('patch_159', '0')
        setk('patch_170', '0')
        setk('patch_167', '0')
        setk('patch_157', '0')
        # carattere brillante + bassi pieni (applicato dalla 109 al caricamento)
        setk('exp_sw_vol', '100')     # volume pieno, nessuna ri-normalizzazione
        setk('exp_sw_bright', '78')   # +~6.7 dB @7kHz = brillante
        setk('exp_sw_bass', '66')     # +~4.8 dB @80Hz = bassi presenti, non gonfi
        setk('exp_sw_reverb', '30')   # riverbero ~3s (RT X-Light)
        # bersagli 159 neutri, se mai riaccesa
        setk('auto_tgt_lm159', '0')
        setk('auto_tgt_hm159', '0')
    except Exception as e:
        print('[XL179]', e)
    return True


try:
    apply()
except Exception as _e:
    print('patch 179: %s' % _e)
