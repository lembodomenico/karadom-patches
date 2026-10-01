def apply():
    # Il 171 (DSP numpy pesante: doppio exciter) gracchia in tempo reale su CPU
    # normali. Torno all'EQ X-Light LEGGERA (170, DX8 nativi): riaccendo il 170 e
    # spengo il 171 (che aveva messo patch_170=0). La 174 esiste solo per rimettere
    # i flag giusti sui PC che avevano gia' preso il 171.
    try:
        from moduli.database import Database
        Database.set_config('patch_171', '0')
        Database.set_config('patch_170', '1')
        Database.set_config('patch_167', '0')
    except Exception:
        pass
    return True


try:
    apply()
except Exception as _e:
    print('patch 174: %s' % _e)
