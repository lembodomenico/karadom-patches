def apply():
    # Auto-regolazione (159) con PERSONALITA' X-Light, tarata sul brano registrato:
    # bassi low/mid=+20.3, acuti high/mid=-12.7 (misurati da xlight_ref), riverbero
    # ~3 s leggero (109). La 159 regola OGNI brano verso questi valori (congruo al
    # brano e al nuovo core.kdl), istantaneo e pulito (shelf, niente exciter).
    # Spengo il 170 fisso (niente doppio EQ) e 167/157.
    try:
        from moduli.database import Database

        def setk(k, v):
            Database.set_config(k, v)

        # carattere tonale X-Light (bersagli 159)
        setk('auto_tgt_lm159', '20.3')
        setk('auto_tgt_hm159', '-12.7')
        # riverbero leggero (il tempo 3 s lo mette la 109)
        setk('exp_sw_reverb', '20')
        # la 159 fa il tono: 109 neutra su bright/bass
        setk('exp_sw_bright', '50')
        setk('exp_sw_bass', '50')
        # un solo sistema: 159 ON, niente 170/167/157
        setk('patch_159', '1')
        setk('patch_170', '0')
        setk('patch_167', '0')
        setk('patch_157', '0')
    except Exception as e:
        print('[XL177]', e)
    return True


try:
    apply()
except Exception as _e:
    print('patch 177: %s' % _e)
