# 239 - preferiti senza blocchi

import os
import threading

_VER = 2
_ATTESA_MS = 350          # si carica il preferito su cui ci si FERMA, non quelli attraversati


def _titolare():
    """Solo sui PC del titolare: licenza FIRMATA intestata a Domenico Lembo (come la 233)."""
    try:
        from moduli.licensing import load_license
        d = load_license() or {}
        return (str(d.get('nome', '')).strip().lower(),
                str(d.get('cognome', '')).strip().lower()) == ('domenico', 'lembo')
    except Exception:
        return False


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_239', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def _log(msg):
    try:
        print('[239] %s' % msg)
    except Exception:
        pass


def _cartelle_dal_tree(self):
    """I percorsi dei nodi selezionati, SENZA toccare il disco (lo fa il thread)."""
    out = []
    try:
        for item in self.tree.selection():
            v = self.tree.item(item).get('values')
            if v:
                out.append(str(v[0]))
    except Exception:
        pass
    return out


def apply():
    if not _titolare():
        return False
    if _spenta():
        _log('spenta (patch_239=0)')
        return False
    try:
        import moduli.libreria as lib
    except Exception as e:
        _log('libreria non trovata: %s' % e)
        return False
    C = getattr(lib, 'LibreriaSlider', None)
    if C is None or not hasattr(C, 'on_tree_select'):
        return False
    if getattr(C, '_ver239', None) == _VER:
        return True
    originale = getattr(C, '_o239_on_tree_select', None) or C.on_tree_select
    C._o239_on_tree_select = originale

    def on_tree_select(self, event=None):
        # durante il ripristino del preferito all'avvio resta tutto com'era
        if getattr(self, '_restoring_preferito', False):
            return originale(self, event)
        try:
            if getattr(self, '_a239', None):
                self.parent.after_cancel(self._a239)
        except Exception:
            pass
        cartelle = _cartelle_dal_tree(self)
        if not cartelle:
            return None
        self._gen239 = getattr(self, '_gen239', 0) + 1
        gen = self._gen239

        def fermo():
            self._a239 = None
            if gen != getattr(self, '_gen239', 0):
                return
            # il controllo "la cartella esiste?" va in un thread: un disco esterno in pausa
            # bloccava la finestra (e il brano che suona) finche' non si risvegliava
            def controlla():
                ok = []
                for p in cartelle:
                    try:
                        if os.path.isdir(p):
                            ok.append(p)
                    except Exception:
                        pass

                def esegui():
                    if gen != getattr(self, '_gen239', 0) or not ok:
                        return
                    # se nel frattempo la selezione e' cambiata non si carica niente
                    if _cartelle_dal_tree(self) != cartelle:
                        return
                    originale(self, event)
                try:
                    self.parent.after(0, esegui)
                except Exception:
                    pass
            threading.Thread(target=controlla, daemon=True, name='preferito239').start()

        try:
            self._a239 = self.parent.after(_ATTESA_MS, fermo)
        except Exception:
            return originale(self, event)
        return None

    C.on_tree_select = on_tree_select
    C._ver239 = _VER
    _log('preferiti: si carica quello su cui ci si ferma, controllo disco fuori dalla finestra')
    return True


def revert():
    try:
        import moduli.libreria as lib
        C = lib.LibreriaSlider
        if getattr(C, '_o239_on_tree_select', None):
            C.on_tree_select = C._o239_on_tree_select
            C._ver239 = None
            return True
    except Exception:
        pass
    return False
