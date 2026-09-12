# 037 - col debug acceso misura se le parole vanno con la musica.

import threading
import time


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_037', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def traccia(testo):
    """Una riga a schermo (la raccoglie il diario) e una su file.

    ⚠️ Il diario cattura `print`, ma solo da quando si e' acceso: su file la
    riga resta comunque, e il diario la ripesca seguendo il registro.
    """
    riga = '[spia] %s' % testo
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
        with open(os.path.join(d, 'patch037.log'), 'a', encoding='utf-8') as f:
            f.write('%s  %s%s' % (
                datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                riga, chr(10)))
    except Exception:
        pass


def _che_motore(sistema):
    """Chi sta suonando: e' la prima cosa da sapere, perche' il tempo lo tiene
    lui. Con l'expander e con il sintetizzatore interno il difetto sarebbe in
    due posti diversi."""
    try:
        if getattr(sistema, 'is_bass_audio', False):
            return 'BASS'
        fs = getattr(sistema, 'fs', None)
        if fs is not None:
            nome = type(fs).__name__
            return 'EXPANDER' if 'Expander' in nome else 'FluidSynth'
        if getattr(sistema, 'is_vlc_audio', False):
            return 'VLC'
    except Exception:
        pass
    return 'ignoto'


def _perche_non_expander():
    """Perche' sta suonando col sintetizzatore interno invece che con
    l'expander? Le tre risposte possibili sono: e' spento nelle opzioni, la
    porta non si vede, oppure l'expander non e' acceso/collegato.

    ⛔ Qui NON si cambia niente: si GUARDA e si scrive. Cambiare il motore a
       un cliente in mezzo a una serata, per di piu' a scatola chiusa, e' come
       le sei patch dell'expander finite ritirate.
    """
    fuori = []
    try:
        from moduli.database import Database
        fuori.append('impostazione=%s' % (Database.get_config('expander_mode', 'auto') or 'auto'))
        porta = Database.get_config('expander_port', '') or ''
        if porta:
            fuori.append('porta scelta=%s' % porta)
    except Exception as e:
        fuori.append('impostazione non letta (%s)' % e)
    try:
        from moduli import expander_midi as X
        porte = None
        for nome in ('list_ports', 'elenco_porte', 'porte', 'lista_porte'):
            f = getattr(X, nome, None)
            if callable(f):
                porte = f()
                break
        if porte is None:
            fuori.append('non so chiedere le porte a expander_midi')
        else:
            # ⭐ quali porte MIDI vede il PC, e come le giudica KaraDom: e' la
            #    riga che dice se l'expander non c'e' o se c'e' e non e' stato
            #    riconosciuto
            righe = []
            for p in (porte or [])[:6]:
                try:
                    nome_p = p if isinstance(p, str) else (
                        p.get('nome') or p.get('name') or str(p))
                    giudizio = ''
                    if callable(getattr(X, 'classifica_porta', None)):
                        giudizio = ' -> %s' % X.classifica_porta(nome_p)
                    righe.append('%s%s' % (str(nome_p)[:60], giudizio))
                except Exception:
                    righe.append(str(p)[:60])
            fuori.append('porte MIDI viste: %s'
                         % ('; '.join(righe) if righe else 'NESSUNA'))
    except Exception as e:
        fuori.append('expander_midi non disponibile (%s)' % e)
    return ' | '.join(fuori)


def _come_suona_l_expander(sistema):
    """L'expander manda le note con l'orario scritto sopra, o subito?

    ⛔⛔ QUI PUO' NASCERE IL RITARDO DELLE PAROLE. Col lo stream aperto il
        programma consegna al driver i messaggi fino a **300 ms in anticipo**,
        con dentro l'orario di uscita: il driver li fa uscire al momento
        giusto, e il testo - che va sul tempo VERO - resta allineato.
        Ma se l'anticipo resta acceso mentre lo stream non c'e' piu', quei
        messaggi escono APPENA ARRIVANO: la musica si sente tre decimi prima
        del testo, cioe' le parole sembrano in ritardo. Questa riga dice quale
        dei due casi e'.
    """
    try:
        fs = getattr(sistema, 'fs', None)
        if fs is None:
            return 'nessun player MIDI'
        pezzi = ['expander=%s' % bool(getattr(fs, 'is_expander', False))]
        uscita = getattr(fs, 'out', None)
        stream = getattr(uscita, '_stream', None) if uscita is not None else None
        pezzi.append('stream=%s' % ('aperto' if stream is not None else 'NO'))
        if getattr(fs, 'is_expander', False):
            pezzi.append('anticipo=%s' % ('300 ms' if stream is not None else '0'))
            if stream is None:
                pezzi.append('(senza stream le note escono appena arrivano)')
        try:
            pezzi.append('porta=%s' % str(getattr(uscita, 'nome', '') or
                                          getattr(uscita, 'porta', ''))[:40])
        except Exception:
            pass
        return ' | '.join(pezzi)
    except Exception as e:
        return 'non leggibile (%s)' % e


def _quale_sillaba(sillabe, quando_ms):
    """A che punto del TESTO siamo, secondo il programma. Torna l'indice.

    ⛔ Si scrive l'indice e il tempo, NON le parole: il diario finisce sul
       server, e le parole di una canzone non ci devono andare.
    """
    n = 0
    for i, s in enumerate(sillabe or ()):
        try:
            t = s[1] if not isinstance(s, dict) else s.get('time')
        except Exception:
            continue
        if t is not None and t <= quando_ms:
            n = i
        else:
            break
    return n


def _guarda(sistema):
    """Ogni cinque secondi: che ora dice il motore, che ora e' davvero, e a che
    punto del testo siamo.

    ⭐ IL NUMERO CHE CONTA e' la DERIVA: la posizione che il programma usa per
       accendere le parole, meno il tempo passato per davvero. Se il motore
       "corre" le parole anticipano, se resta indietro le parole ritardano. E'
       la misura che mancava: finora si andava a orecchio.
    """
    partito = time.time()
    try:
        engine = getattr(sistema, 'engine', None)
        sillabe = getattr(engine, 'syllables_data', None) or []
        nome = ''
        try:
            import os
            nome = os.path.basename(str(getattr(sistema, 'current_file', '') or ''))
        except Exception:
            pass
        prima = None
        for s in sillabe:
            t = s[1] if not isinstance(s, dict) else s.get('time')
            if t:
                prima = t
                break
        motore = _che_motore(sistema)
        traccia('parte "%s" | motore %s | %d sillabe | prima sillaba a %s ms'
                % (nome[:60], motore, len(sillabe),
                   prima if prima is not None else '?'))
        if motore == 'EXPANDER':
            # ⭐ LA RIGA CHE MANCAVA: col programma a tempo (deriva -1 ms,
            #    misurata il 12-09) il disallineamento puo' nascere solo qui,
            #    da COME escono le note verso l'expander.
            traccia('expander: %s' % _come_suona_l_expander(sistema))
        else:
            traccia('niente expander: %s' % _perche_non_expander())
    except Exception as e:
        traccia('non riesco a leggere il brano: %s' % e)
        return

    fatte = 0
    while fatte < 120:                      # al massimo dieci minuti
        time.sleep(5)
        try:
            if not getattr(sistema, 'is_playing', False):
                traccia('finito dopo %.0f s' % (time.time() - partito))
                return
            vero = (time.time() - partito) * 1000.0
            detto = float(sistema.get_current_position_ms() or 0)
            i = _quale_sillaba(sillabe, detto)
            traccia('orologio %6.0f ms | il programma dice %6.0f ms | '
                    'DERIVA %+6.0f ms | sillaba %d di %d'
                    % (vero, detto, detto - vero, i, len(sillabe)))
        except Exception as e:
            traccia('misura saltata: %s' % e)
        fatte += 1


def apply():
    if _spenta():
        return False
    try:
        import sys
        mod = sys.modules.get('moduli.system')
        if mod is None:
            return False
        cls = getattr(mod, 'KaraokeMonitorSystem', None)
        if cls is None:
            for n in dir(mod):
                o = getattr(mod, n)
                if isinstance(o, type) and hasattr(o, 'get_current_position_ms'):
                    cls = o
                    break
        if cls is None or getattr(cls.play, '_spia037', False):
            return False

        originale = cls.play

        def play(self, *a, **k):
            esito = originale(self, *a, **k)
            try:
                if getattr(self, 'is_midi', False):
                    threading.Thread(target=_guarda, args=(self,),
                                     daemon=True, name='Spia037').start()
            except Exception:
                pass
            return esito

        play._spia037 = True
        cls.play = play
        traccia('spia delle parole agganciata')
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
