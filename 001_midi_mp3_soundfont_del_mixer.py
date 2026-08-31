# 001_midi_mp3_soundfont_del_mixer.py
#
# COSA CORREGGE
#   Il modulo "MIDI/KAR -> MP3" chiedeva di indicare il SoundFont a ogni
#   conversione, anche quando KaraDom ne aveva gia' uno impostato nel Mixer.
#
#   Il motivo: leggeva il percorso salvato in config ('soundfont_path') e, se
#   quel percorso non esisteva piu' sul disco, rinunciava e lasciava il campo
#   vuoto. Succede sempre quando la configurazione e' stata fatta su un'altra
#   cartella o su un altro PC: nel database resta il percorso di prima.
#
# COSA FA ADESSO
#   Se il percorso salvato non c'e' piu', cerca un file CON LO STESSO NOME nelle
#   cartelle del programma (soundfonts\, cartella dell'app, %LOCALAPPDATA%) e solo
#   se non trova nemmeno quello prende il primo SoundFont disponibile.
#   Cosi' l'MP3 esce con gli stessi suoni che si sentono dentro KaraDom, senza
#   dover indicare niente.
#
#   In piu': se si sceglie un SoundFont a mano, quella scelta viene salvata in
#   config, cosi' Mixer e conversione restano d'accordo e non lo richiede piu'.
#
# NOTA sull'expander: se il Mixer sta suonando con un expander, l'MP3 viene
#   comunque creato col SoundFont. Non e' una scelta: l'expander e' un apparecchio
#   esterno e il suo audio esce dalle sue prese, non passa dal computer, quindi non
#   puo' finire in un file. (I synth software di Windows non contano come expander.)

import os
from pathlib import Path

import moduli.midi_mp3_exporter as mme


def _cartelle_soundfont():
    """Dove puo' stare un SoundFont, in ordine di preferenza."""
    base = mme._app_base_dir()
    cartelle = [base / "soundfonts", base, Path.cwd() / "soundfonts", Path.cwd()]
    try:
        local = os.environ.get("LOCALAPPDATA", "")
        if local:
            cartelle.append(Path(local) / "KaraDom" / "soundfonts")
    except Exception:
        pass
    return cartelle


def _find_soundfont_dal_mixer():
    nome_cercato = ""
    try:
        from moduli.database import Database
        sf = Database.get_config("soundfont_path", "")
        if sf:
            if os.path.exists(sf):
                return sf
            nome_cercato = os.path.basename(sf)
    except Exception:
        pass

    cartelle = _cartelle_soundfont()

    if nome_cercato:
        for folder in cartelle:
            try:
                p = folder / nome_cercato
                if p.exists():
                    return str(p)
            except Exception:
                continue

    for folder in cartelle:
        try:
            if not folder.exists():
                continue
        except Exception:
            continue
        for pat in ("*.sf2", "*.SF2", "*.sf3", "*.SF3"):
            try:
                found = sorted(folder.glob(pat))
            except Exception:
                found = []
            if found:
                return str(found[0])
    return ""


mme._cartelle_soundfont = _cartelle_soundfont
mme._find_soundfont = _find_soundfont_dal_mixer
print("[PATCH] midi_mp3_exporter._find_soundfont: uso il SoundFont del Mixer")


# La scelta manuale (quando proprio non si trova nulla) diventa quella del
# programma, cosi' non va rifatta a ogni conversione.
try:
    _pick_sf_originale = mme.MidiMp3Window._pick_sf

    def _pick_sf_e_ricorda(self):
        _pick_sf_originale(self)
        try:
            path = self.sf_var.get().strip()
            if path and os.path.exists(path):
                from moduli.database import Database
                Database.set_config("soundfont_path", path)
        except Exception:
            pass

    mme.MidiMp3Window._pick_sf = _pick_sf_e_ricorda
    print("[PATCH] midi_mp3_exporter: il SoundFont scelto a mano viene ricordato")
except Exception as e:
    print("[PATCH] _pick_sf non aggiornata (%s) - il resto della patch vale lo stesso" % e)
