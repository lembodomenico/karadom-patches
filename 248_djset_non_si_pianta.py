# 248 - djset non si pianta

import sys
import threading
import time

_VER = 1
_OGNI = 0.5           # ogni quanto il thread a parte chiede a Windows dov'e' il riquadro video

# [25-10-2026] Utente: "ANCHE DJ-SET SI PIANTA". SPIA-FREEZE: finestra ferma 6, 12, 30 s in
#   karadom_dj.py _lento -> _aggancia_anteprima -> Riconosci.zona_video -> uiautomation BoundingRectangle
# cioe' una domanda di UI Automation alla finestra di KaraDom DJ (Mixxx) fatta DAL thread della finestra: se Mixxx
# e' occupato non risponde e KaraDom resta fermo con lui. Ora quella domanda la fa un thread a parte (con la sua
# inizializzazione UI Automation e i SUOI oggetti: quelli COM non si passano fra thread) e la finestra legge solo
# l'ultimo rettangolo saputo: non aspetta mai.


def _titolare():
    try:
        from moduli.licensing import load_license
        d = load_license() or {}
        return (str(d.get('nome', '')).strip().lower(),
                str(d.get('cognome', '')).strip().lower()) == ('domenico', 'lembo')
    except Exception:
        return False


def _log(msg):
    try:
        print('[248] %s' % msg)
    except Exception:
        pass


def _sistema(m):
    """Mette la zona video 'senza attesa' sulla classe Riconosci del modulo KaraDom DJ (se c'e')."""
    R = getattr(m, 'Riconosci', None)
    if R is None or getattr(R, '_v248', None) == _VER:
        return R is not None
    orig = getattr(R, '_o248_zona', None) or R.zona_video
    R._o248_zona = orig

    def lavora(st):
        try:
            from uiautomation import UIAutomationInitializerInThread
            with UIAutomationInitializerInThread():
                mio = R()                     # oggetti UI Automation di QUESTO thread
                while not st['stop'] and time.time() - st['chiesto'] < 30:
                    t = time.time()
                    try:
                        st['rect'] = orig(mio)
                    except Exception:
                        st['rect'] = None
                    d = time.time() - t
                    if d > 2:
                        _log('Windows ha risposto dopo %.1f s (la finestra non ha aspettato)' % d)
                    time.sleep(_OGNI)
        except Exception as e:
            _log('thread zona video: %s' % e)
        st['thread'] = None

    def zona_video(self):
        st = self.__dict__.get('_z248')
        if st is None:
            st = self.__dict__['_z248'] = {'rect': None, 'thread': None, 'stop': False, 'chiesto': 0}
        st['chiesto'] = time.time()
        th = st.get('thread')
        if th is None or not th.is_alive():
            th = threading.Thread(target=lavora, args=(st,), daemon=True, name='DJ-zona-video-248')
            st['thread'] = th
            th.start()
        return st['rect']

    R.zona_video = zona_video
    R._v248 = _VER
    _log('DJ: la posizione del video si chiede in un thread a parte (la finestra non si pianta piu\')')
    return True


def apply():
    if not _titolare():
        return False
    try:
        from moduli.database import Database
        if str(Database.get_config('patch_248', '1')).strip() in ('0', 'no', 'off'):
            return False
    except Exception:
        pass
    m = sys.modules.get('moduli.karadom_dj')
    if m is not None:
        _sistema(m)

    def sorveglia():
        # rete di sicurezza: il modulo puo' nascere da altre strade; appena c'e' si sistema (solo un attributo)
        while True:
            time.sleep(1.0)
            KD = sys.modules.get('moduli.karadom_dj')
            R = getattr(KD, 'Riconosci', None) if KD is not None else None
            if R is not None and getattr(R, '_v248', None) != _VER:
                try:
                    _sistema(KD)
                except Exception as e:
                    _log('sistemazione non riuscita: %s' % e)
    if not getattr(sys, '_sorveglia248', False):
        sys._sorveglia248 = True
        threading.Thread(target=sorveglia, daemon=True, name='DJ-sorveglia-248').start()
    # il modulo di KaraDom DJ nasce quando si apre il DJ-set (patch 191): si sistema subito dopo
    try:
        import moduli.djset as D
    except Exception as e:
        _log('djset non trovato: %s' % e)
        return m is not None
    if getattr(D, '_v248', None) == _VER:
        return True
    apri0 = getattr(D, '_o248_apri', None) or D.apri_djset
    D._o248_apri = apri0

    def apri_djset(*a, **k):
        esito = apri0(*a, **k)
        try:
            KD = sys.modules.get('moduli.karadom_dj')
            if KD is not None:
                _sistema(KD)
        except Exception:
            pass
        return esito
    D.apri_djset = apri_djset
    D._v248 = _VER
    return True


def revert():
    return False
