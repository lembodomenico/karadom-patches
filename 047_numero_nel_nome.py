# 047 - numeri nel nome dell-artista

import sys


def traccia(testo):
    riga = '[047] %s' % testo
    try:
        print(riga)
    except Exception:
        pass
    try:
        import datetime
        import os
        d = os.path.join(os.environ.get('LOCALAPPDATA') or
                         os.path.expanduser('~'), 'KaraDom')
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, 'patch047.log'), 'a', encoding='utf-8') as f:
            f.write('%s  %s%s' % (
                datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                riga, chr(10)))
    except Exception:
        pass


CODICE = '_TESTA_NUMERO = re.compile(r"^\\s*(\\d+)\\s*(?:([_.\\-)])\\s*|(\\s+))(.*)$", re.S)\n\ndef _senza_numero_davanti(s):\n    """Via il numero di catalogo in testa, ma SOLO se e\' davvero un numero.\n\n    "110 Gloria Gaynor" e "1_Claudio Baglioni" si\', "10cc" no — e\' la stessa\n    regola di `pulisci_archivio.py`, dove era gia\' stata pagata.\n\n    ⛔⛔ IL NUMERO PUO\' ESSERE L\'ARTISTA (utente, 13-09: "non ha importato\n        brani con artisti tipo 883 e simili"). La vecchia regola toglieva\n        qualunque numero staccato: "883 - Come mai" restava "Come mai" e\n        SENZA ARTISTA finiva fra gli scartati (769 file solo degli 883);\n        "99 Posse", "2 Unlimited", "3 Doors Down", "50 Cents" perdevano la\n        prima parte del nome. Si toglie solo quando il numero NON puo\' essere\n        un nome d\'arte:\n          * comincia per zero          "01 - Bambina Mia", "05_-_Alicia..."\n          * ha quattro cifre o piu\'    "1028-Rui_Veloso-PAIXAO"\n          * tre cifre e poi uno spazio "110 Gloria Gaynor - Ti amo"\n          * segno e ancora un separatore dopo, cioe\' l\'artista viene dopo:\n            "10___B_WITCHED___I_SHALL_BE", "1) MARIO Little Tony-Stasera"\n    """\n    m = _TESTA_NUMERO.match(s or "")\n    if not m:\n        return s or ""\n    numero, segno, spazio, resto = m.group(1), m.group(2), m.group(3), m.group(4)\n    togli = (numero.startswith(\'0\')\n             or len(numero) >= 4\n             or (spazio and len(numero) >= 3)\n             or (segno and re.search(r"[-_]", resto)))\n    return resto if togli else (s or "")\n\n'

PROVE = (('883 - Come mai.mp3', '883', 'Come mai'),
         ('3 Doors Down - Kryptonite.mp3', '3 Doors Down', 'Kryptonite'),
         ('110 Gloria Gaynor - Ti amo.mp3', 'Gloria Gaynor', 'Ti amo'))


def apply():
    try:
        mod = sys.modules.get('moduli.catalogo_remoto')
        if mod is None:
            import moduli.catalogo_remoto as mod
        if getattr(getattr(mod, '_senza_numero_davanti', None), '_s047', False):
            return True
        exec(compile(CODICE, '<patch047>', 'exec'), mod.__dict__)
        mod._senza_numero_davanti._s047 = True
        buone = 0
        for nome, artista, titolo in PROVE:
            try:
                if mod.artista_titolo(nome) == (artista, titolo):
                    buone += 1
            except Exception:
                pass
        traccia('numeri nel nome: %d prove su %d' % (buone, len(PROVE)))
        return True
    except Exception as e:
        traccia('non agganciata: %s: %s' % (type(e).__name__, e))
        return False


def revert():
    return False


try:
    apply()
except Exception:
    pass
