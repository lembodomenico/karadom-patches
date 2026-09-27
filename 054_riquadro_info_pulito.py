# 054 - riquadro informazioni: torna il Formato

# Nel riquadro info in basso (cantante + brano + box "Formato") era stata
# infilata anche una riga con lo stato del catalogo in sottofondo. Quella
# riga, quando il testo era lungo, allargava la parte sinistra del riquadro
# (che ha larghezza fissa) e spingeva fuori il box "Formato": restava solo
# il suo bordo, cioe' "una riga sotto il brano". Qui la riga del catalogo
# NON viene piu' messa nel riquadro info: lo stato del catalogo resta
# visibile nella finestra Opzioni. Cosi' il riquadro torna com'era:
# cantante, brano e Formato.

import sys


def apply():
    try:
        m = sys.modules.get('moduli.catalogo_sfondo')
        if m is None:
            try:
                from moduli import catalogo_sfondo as m
            except Exception:
                return False
        if getattr(getattr(m, 'aggancia_barra', None), '_pulita054', False):
            return True

        def aggancia_barra(contenitore):
            # niente etichetta nel riquadro info: lascia stare cantante,
            # brano e Formato. Lo stato del catalogo si legge nelle Opzioni.
            return None

        aggancia_barra._pulita054 = True
        m.aggancia_barra = aggancia_barra
        return True
    except Exception:
        return False


try:
    apply()
except Exception:
    pass
