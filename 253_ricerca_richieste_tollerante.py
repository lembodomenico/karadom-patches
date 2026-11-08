# 253 - richieste remote: ricerca che trova la base anche con parentesi, accenti, apostrofi, trattini, punti
# [08-11-2026] utente: "verifica che i brani di brani_memorizzati2 siano ricercabili e diano un risultato con il
# modulo richieste remote". Misurato: 1.118 richieste su 21.321 davano ZERO risultati e 1.117 avevano la base sul
# disco. Cause: la ricerca (016) vuole ogni parola scritta dentro il nome del file, ma la richiesta portava
# "(Upside Down)", "Ac-Dc", "così", "E'", "24.000", "caldo,", "Want?". Qui il testo che la 160 mette nel filtro si
# spezza nei pezzi alfanumerici (cosi' "cos" trova cosi/così/cosi', "ac" "dc" trova AC DC/ACDC/AC-DC) e le
# parentesi si tolgono. Ogni pezzo e' parte di una parola di prima: quello che si trovava prima si trova ancora.
# Non tocca la 160 (pubblicata): sostituisce _filtro_pulito nel suo spazio, preso da una funzione che lei aggancia.
import re

_VER = 1
_CONTRATTE = re.compile(r'^(don|can|won|isn|didn|doesn|aren|wasn|weren|couldn|wouldn|shouldn|ain|haven|hasn)t$')


def tollerante(testo):
    t = str(testo or '')
    senza = re.sub(r'\([^)]*\)|\[[^\]]*\]', ' ', t)
    if senza.strip():
        t = senza
    # accento scritto con l'apostrofo ("saro'", "perche'"): sul file puo' essere "sarò" -> si cerca "sar"
    t = re.sub(r"([A-Za-z])[AEIOUaeiou]'(?=[\s,.;:!?)]|$)", r"\1", t)
    pezzi, visti = [], set()
    for p in re.split(r'[^0-9A-Za-z]+', t):
        if not p:
            continue
        pl = p.lower()
        m = _CONTRATTE.match(pl)
        if m:
            pl = m.group(1)                     # "dont" trova "don't" e "dont"
        elif pl in ('its', 'thats', 'whats', 'lets', 'hes', 'shes', 'theres', 'heres'):
            pl = pl[:-1]                        # "its" trova "it's" e "its"
        elif len(pl) >= 4 and pl.endswith('s') and not pl.endswith('ss') and not pl.isdigit():
            pl = pl[:-1]                        # "girls" trova "girl's" e "girls"
        if (len(pl) >= 2 or pl.isdigit()) and pl not in visti:
            visti.add(pl)
            pezzi.append(pl)
    return ' '.join(pezzi) or str(testo or '').strip()


def _spazio_160():
    import sys
    lib = sys.modules.get('moduli.libreria')
    if lib is None:
        import moduli.libreria as lib  # noqa
    C = getattr(lib, 'LibreriaSlider', None)
    for nome in ('__init__', 'crea_riga', 'toggle_slider', '_aggiungi_da_playlist'):
        f = getattr(C, nome, None)
        f = getattr(f, '__func__', f)
        g = getattr(f, '__globals__', None)
        if g and '_VER160' in g and callable(g.get('_filtro_pulito')):
            return g
    return None


def _titolare():
    """Solo sui PC del titolare: licenza intestata a Domenico Lembo (come 205/233/242)."""
    try:
        from moduli.licensing import load_license
        d = load_license() or {}
        return (str(d.get('nome', '')).strip().lower(),
                str(d.get('cognome', '')).strip().lower()) == ('domenico', 'lembo')
    except Exception:
        return False


def apply():
    if not _titolare():
        return False
    try:
        from moduli.database import Database
        if str(Database.get_config('patch_253', '1')).strip() in ('0', 'no', 'off'):
            return False
    except Exception:
        pass
    g = _spazio_160()
    if g is None:
        print('[RICERCA253] patch 160 non trovata: niente da fare')
        return False
    orig = g.get('_o253_filtro') or g['_filtro_pulito']
    g['_o253_filtro'] = orig

    def _filtro_pulito(brano, artista, _o=orig):
        return tollerante(_o(brano, artista))
    g['_filtro_pulito'] = _filtro_pulito
    print('[RICERCA253] richieste remote: ricerca tollerante (parentesi, accenti, apostrofi, trattini)')
    return True


def revert():
    g = _spazio_160()
    if g and g.get('_o253_filtro'):
        g['_filtro_pulito'] = g['_o253_filtro']
    return True
