# 204 - nei suggerimenti lo stesso file in due cartelle compare una volta sola

_VER = 1


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_204', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def _una_volta(posizioni, brani_ref, tetto):
    visti, tenuti = set(), []
    for p in posizioni or ():
        if not (0 <= p < len(brani_ref)):
            continue
        try:
            n = brani_ref[p]['nome'].strip().lower()
        except Exception:
            n = None
        if n is not None and n in visti:
            continue
        if n is not None:
            visti.add(n)
        tenuti.append(p)
        if len(tenuti) >= tetto:
            break
    return tenuti


def _nomi_una_volta(lista):
    visti, tenuti = set(), []
    for b in lista or ():
        try:
            n = b['nome'].strip().lower()
        except Exception:
            n = None
        if n is not None and n in visti:
            continue
        if n is not None:
            visti.add(n)
        tenuti.append(b)
    return tenuti


def apply():
    if _spenta():
        return False
    try:
        import moduli.libreria as lib
        C = getattr(lib, 'LibreriaSlider', None)
        if C is None or getattr(C, '_tit204', None) == _VER:
            return True
        if hasattr(C, '_cerca_in_tabella_016'):
            o_cerca = getattr(C, '_tit204_o_cerca', None) or C._cerca_in_tabella_016
            C._tit204_o_cerca = o_cerca

            def _cerca_in_tabella_016(self, parti, parti_ext, brani_ref, tetto):
                r = o_cerca(self, parti, parti_ext, brani_ref, tetto * 4)
                if r is None:
                    return None
                return _una_volta(r, brani_ref, tetto)

            C._cerca_in_tabella_016 = _cerca_in_tabella_016
        if hasattr(C, '_mostra_risultati_filtro'):
            o_mostra = getattr(C, '_tit204_o_mostra', None) or C._mostra_risultati_filtro
            C._tit204_o_mostra = o_mostra

            def _mostra_risultati_filtro(self, finali):
                return o_mostra(self, _nomi_una_volta(finali))

            C._mostra_risultati_filtro = _mostra_risultati_filtro
        C._tit204 = _VER
        print('[TIT204] suggerimenti: stesso file in due cartelle = una riga')
    except Exception as e:
        print('[TIT204] hook:', e)
    return True


def revert():
    pass


try:
    apply()
except Exception as _e:
    print('patch 204: %s' % _e)
