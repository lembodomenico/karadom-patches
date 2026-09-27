# 044 - doppio invio avvia la base

import sys


def traccia(testo):
    riga = '[044] %s' % testo
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
        with open(os.path.join(d, 'patch044.log'), 'a', encoding='utf-8') as f:
            f.write('%s  %s%s' % (
                datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                riga, chr(10)))
    except Exception:
        pass


def _aggancia(obj):
    cv = getattr(obj, '_sc_cv', None)
    if cv is None or not hasattr(obj, '_doppio_invio_play'):
        return False
    if getattr(cv, '_invio044', False):
        return False

    def _invio(e, _o=obj):
        _o._doppio_invio_play(e)
        return 'break'

    cv.bind('<Return>', _invio)
    cv.bind('<KP_Enter>', _invio)
    cv._invio044 = True
    return True


def apply():
    try:
        avvolte = 0
        for nome, mod in list(sys.modules.items()):
            if not nome.startswith('moduli.') or mod is None:
                continue
            for o in list(vars(mod).values()):
                if not isinstance(o, type) or 'create_slider' not in vars(o):
                    continue
                vera = vars(o)['create_slider']
                if getattr(vera, '_invio044', False):
                    continue

                def create_slider(self, *a, _vera=vera, **k):
                    r = _vera(self, *a, **k)
                    try:
                        _aggancia(self)
                    except Exception as e:
                        traccia('tela non agganciata: %s' % e)
                    return r

                create_slider._invio044 = True
                o.create_slider = create_slider
                avvolte += 1
        gia = 0
        import gc
        for o in gc.get_objects():
            try:
                if hasattr(o, '_sc_cv') and _aggancia(o):
                    gia += 1
            except Exception:
                pass
        traccia('doppio invio sulla scaletta: %d classi, %d scalette gia aperte'
                % (avvolte, gia))
        return bool(avvolte or gia)
    except Exception as e:
        traccia('non agganciata: %s: %s' % (type(e).__name__, e))
        return False


def revert():
    return False


try:
    apply()
except Exception:
    pass
