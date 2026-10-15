# 224 - campo filtro pronto

_VER = 1
ATTESA_CON_TABELLA = 250


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_224', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def _tabella_pronta(self):
    try:
        brani = self.brani_pc
        pronta = getattr(self, '_tabella016', None)
        return bool(brani) and bool(pronta) and pronta[0] is brani and pronta[1] == len(brani)
    except Exception:
        return False


def _archivi_senza_errori():
    try:
        import moduli.carica_basi as cb
    except Exception:
        return
    vera = getattr(cb, 'cerca_nei_db', None)
    if vera is None or getattr(vera, '_da224', False):
        return
    stato = {'rotta': False}

    def cerca_nei_db(*a, **k):
        if stato['rotta']:
            return []
        try:
            return vera(*a, **k)
        except Exception as e:
            stato['rotta'] = True
            print('[224] archivi nei suggerimenti non disponibili: %s' % e)
            return []
    cerca_nei_db._da224 = True
    cb.cerca_nei_db = cerca_nei_db


def apply():
    if _spenta():
        return False
    try:
        import moduli.libreria as lib
    except Exception:
        return False
    C = getattr(lib, 'LibreriaSlider', None)
    if C is None or not hasattr(C, '_debounce_suggerimenti'):
        return False
    if getattr(C, '_ver224', None) == _VER:
        return True
    prima = C._debounce_suggerimenti

    def _debounce_suggerimenti(self, event=None):
        r = prima(self, event)
        try:
            valori = getattr(self, '_attese_ricerca', None)
            did = getattr(self, '_debounce_id', None)
            if did and valori and len(self.brani_pc or ()) >= valori[2] and _tabella_pronta(self):
                self.parent.after_cancel(did)
                self._debounce_id = self.parent.after(ATTESA_CON_TABELLA, self.aggiorna_suggerimenti_live)
        except Exception:
            pass
        return r

    C._debounce_suggerimenti = _debounce_suggerimenti
    _archivi_senza_errori()
    C._ver224 = _VER
    print('[224] campo filtro: attesa corta quando la tabella di ricerca e\' pronta')
    return True


def revert():
    return False


try:
    apply()
except Exception:
    pass
