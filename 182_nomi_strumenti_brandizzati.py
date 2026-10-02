def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_182', '1')) == '0'
    except Exception:
        return False


def apply():
    if _spenta():
        return False
    try:
        import moduli.expander_midi as EX
    except Exception as e:
        print('[BRAND182] import:', e)
        return False
    if not hasattr(EX, 'nome_suono_expander') or getattr(EX, '_brand182', False):
        return True
    _orig = EX.nome_suono_expander
    GM = None
    try:
        from moduli.mixer import GM_INSTRUMENTS as GM
    except Exception:
        GM = None

    def nome_suono_expander(program, bank_msb=0, is_drum=False):
        # Nomi strumenti del mixer TUTTI brandizzati "KDL ...": col banco
        # dell'expander (software mio) ogni canale passa di qui. Niente piu'
        # nomi "---" o GM nudi. Solo display: la rimappa usa i NUMERI, non il
        # nome, quindi non si rompe nulla.
        n = None
        try:
            n = _orig(program, bank_msb, is_drum)
        except Exception:
            n = None
        if not n:
            try:
                if is_drum or int(bank_msb) == 128:
                    n = 'Drums'
                elif GM and 0 <= int(program) < len(GM):
                    n = GM[int(program)]
                else:
                    n = 'Program %d' % (int(program) + 1)
            except Exception:
                n = 'Strumento'
        n = str(n).strip()
        if not n.upper().startswith('KDL'):
            n = 'KDL ' + n
        return n

    EX.nome_suono_expander = nome_suono_expander
    EX._brand182 = True
    print('[BRAND182] nomi strumenti expander brandizzati KDL')
    return True


try:
    apply()
except Exception as _e:
    print('patch 182: %s' % _e)
