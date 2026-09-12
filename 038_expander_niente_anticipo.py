# 038 - le note all'expander escono quando devono, senza i 300 ms di anticipo.

def _gia_a_posto(valore):
    return str(valore).strip() in ('0', 'no', 'false', 'off')


def traccia(testo):
    riga = '[038] %s' % testo
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
        with open(os.path.join(d, 'patch038.log'), 'a', encoding='utf-8') as f:
            f.write('%s  %s%s' % (
                datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                riga, chr(10)))
    except Exception:
        pass


def apply():
    """Spegne la consegna anticipata dei messaggi MIDI all'expander.

    Come stanno le cose, misurato sul PC del cliente il 12-09:
      * suona sull'expander (non col sintetizzatore interno);
      * il programma e' A TEMPO: la posizione che accende le parole coincide
        con l'orologio a un millesimo su dieci secondi (spia 037).
    Se il testo va col tempo giusto e chi canta sente le parole in ritardo,
    allora e' la musica che esce PRIMA. E c'e' un solo punto che la manda
    avanti: con lo stream aperto i messaggi si consegnano al driver fino a
    **300 ms prima**, con dentro l'orario di uscita, fidandosi che sia lui a
    farli uscire al momento giusto. Su questo expander quella strada era gia'
    stata bocciata sul campo a settembre (patch 011, ritirata perche' non
    portava benefici): qui si smette di usarla.

    ⭐ Si tocca UNA impostazione, `expander_stream`, che esiste apposta. Il
       resto del programma non cambia: senza stream le note partono nel
       momento in cui il brano le chiede, come prima della 011.
    ⭐ Reversibile: basta rimettere `expander_stream = 1`.
    """
    try:
        from moduli.database import Database
    except Exception as e:
        traccia('non riesco a leggere le impostazioni: %s' % e)
        return False
    try:
        adesso = Database.get_config('expander_stream', '1')
        if _gia_a_posto(adesso):
            traccia('gia- spento: niente da fare')
            return True
        Database.set_config('expander_stream', '0')
        controllo = Database.get_config('expander_stream', '1')
        if not _gia_a_posto(controllo):
            traccia('NON e- stato spento (rileggo "%s")' % controllo)
            return False
        traccia('anticipo spento: le note all-expander escono quando devono')
        return True
    except Exception as e:
        traccia('%s: %s' % (type(e).__name__, e))
        return False


def revert():
    """Rimette com'era: l'anticipo torna."""
    try:
        from moduli.database import Database
        Database.set_config('expander_stream', '1')
        traccia('anticipo rimesso')
        return True
    except Exception:
        return False


try:
    apply()
except Exception:
    pass
