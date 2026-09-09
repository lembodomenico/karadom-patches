# 032 - la tonalita' funziona anche sulle basi prese da internet.
#
# Con una base online l'audio da trasporre si estrae con ffmpeg in un file
# temporaneo, il cui nome veniva ricavato dall'indirizzo. Ma l'indirizzo di
# YouTube e' lungo oltre mille caratteri e contiene '?': ne usciva un nome di
# file impossibile, la creazione falliva e - senza dire niente - la tonalita'
# non si muoveva piu'.
#
# SE NON VA BENE: `patch_032 = 0` la spegne su una macchina sola.

CODICE = 'def _extract_video_audio(self, video_path):\n    """Estrai traccia audio da un video → temp WAV per Pedalboard pitch shift."""\n    import tempfile\n    temp_dir = tempfile.gettempdir()\n\n    # ⛔ SE ARRIVA UN INDIRIZZO, IL NOME NON SI RICAVA DALL\'INDIRIZZO.\n    #    Le basi online passano di qui con l\'indirizzo diretto di YouTube:\n    #    1145 caratteri con dentro \'?\' e \'&\'. Con basename() ne usciva un\n    #    nome di 603 caratteri, col \'?\' che Windows non ammette e oltre il\n    #    limite dei 260: la creazione falliva con "Invalid argument",\n    #    ffmpeg non estraeva niente, BASS restava senza audio e la\n    #    tonalita\' non funzionava — tutto in silenzio, senza un errore\n    #    visibile. Con un indirizzo si usa un\'impronta corta: nome sempre\n    #    valido, e sempre lo STESSO per lo stesso brano, cosi\' la seconda\n    #    volta l\'audio gia\' estratto si riusa invece di rifarlo.\n    _e_indirizzo = str(video_path).lower().startswith((\'http://\', \'https://\'))\n    if _e_indirizzo:\n        import hashlib\n        import re as _re\n        # dell\'indirizzo si tiene solo la parte stabile: cambiando la\n        # scadenza (expire=...) il brano e\' sempre quello\n        _chiave = _re.sub(r\'[?&](expire|ei|ip|met|mh|mm|mn|ms|rms|initcwndbps|\'\n                          r\'bui|spc|sig|lsig|pcm2cms)=[^&]*\', \'\', str(video_path))\n        base = \'yt_\' + hashlib.sha1(_chiave.encode(\'utf-8\', \'replace\')).hexdigest()[:16]\n    else:\n        base = os.path.splitext(os.path.basename(video_path))[0]\n    output = os.path.join(temp_dir, f"{base}_extracted_audio.wav")\n    \n    if os.path.exists(output) and os.path.getsize(output) > 1000:\n        print(f"🎬 Audio video cache: {output}")\n        return output\n    \n    # Estrai audio con ffmpeg\n    # ⚠️ IL PERCORSO VA CERCATO, non si scrive \'ffmpeg\' e basta: sui PC dei\n    # clienti ffmpeg NON e\' nel PATH di sistema (sta in dipendenze\\, spedito\n    # con il programma). Chiamandolo nudo l\'estrazione falliva in silenzio,\n    # l\'audio non arrivava a BASS e la tonalita\' sui video non funzionava:\n    # si ricadeva sulla velocita\' e il video rallentava.\n    try:\n        import subprocess\n        # ⚠️ Nel COMPILATO la cartella non si ricava da __file__ (Nuitka lo\n        # mette altrove): si parte da sys.argv[0], come fa gia\' yt2mp3.\n        ffmpeg = \'ffmpeg\'\n        try:\n            from .yt2mp3 import _dep as _dip\n            _f = _dip(\'ffmpeg.exe\' if os.name == \'nt\' else \'ffmpeg\')\n            if os.path.exists(_f):\n                ffmpeg = _f\n            else:\n                from .normalizzazione import _get_ffmpeg_path\n                ffmpeg = _get_ffmpeg_path()\n        except Exception:\n            pass\n        print(f"🎬 Estrazione audio da: {Path(video_path).name} (con {ffmpeg})...")\n        subprocess.run([ffmpeg, \'-y\', \'-i\', video_path, \'-vn\', \'-acodec\', \'pcm_s24le\',\n                       \'-ar\', \'48000\', \'-ac\', \'2\', output],\n                      capture_output=True, timeout=120,\n                      creationflags=0x08000000 if os.name == \'nt\' else 0)\n        if os.path.exists(output) and os.path.getsize(output) > 1000:\n            print(f"🎬 Estratto con ffmpeg: {os.path.getsize(output)/(1024*1024):.1f}MB")\n            return output\n    except Exception as e:\n        print(f"⚠️ ffmpeg: {e}")\n    \n    return None'


def _spenta():
    try:
        from moduli.database import Database
        if str(Database.get_config('patch_032', '1')).strip() in ('0', 'no', 'off'):
            traccia('spenta a mano (patch_032 = 0)')
            return True
    except Exception:
        pass          # la configurazione non risponde: non e' un motivo per spegnersi
    return False


def traccia(testo):
    try:
        import datetime
        import os
        d = os.path.join(os.environ.get('LOCALAPPDATA') or
                         os.path.expanduser('~'), 'KaraDom')
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, 'patch032.log'), 'a', encoding='utf-8') as f:
            f.write('%s  %s' % (
                datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                testo) + chr(10))
    except Exception:
        pass


def apply():
    if _spenta():
        traccia('non mi accendo (vedi la riga qui sopra)')
        return False
    try:
        import moduli.system as m
        C = m.KaraokeMonitorSystem
        if hasattr(C, '_orig_032'):
            traccia('gia' + chr(39) + ' agganciata')
            return True
        C._orig_032 = C._extract_video_audio
        spazio = m.__dict__
        exec(compile(CODICE, "<patch032>", "exec"), spazio)
        setattr(C, '_extract_video_audio', spazio['_extract_video_audio'])
        traccia('AGGANCIATA: audio estraibile anche da un indirizzo')
        print("patch 032: tonalita' anche sulle basi online")
        return True
    except Exception as e:
        traccia('NON agganciata: %s: %s' % (type(e).__name__, e))
        print("patch 032: %s" % e)
        return False


def revert():
    try:
        import sys
        m = sys.modules.get('moduli.system')
        C = getattr(m, 'KaraokeMonitorSystem', None) if m else None
        if C is not None and hasattr(C, '_orig_032'):
            setattr(C, '_extract_video_audio', C._orig_032)
            del C._orig_032
            print("patch 032: rimesso l'originale")
            return True
    except Exception as e:
        print("patch 032: %s" % e)
    return False


try:
    apply()
except Exception:
    pass
