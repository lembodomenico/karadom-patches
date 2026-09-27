# 012_barre_blu_notte.py
#
# BARRE DI KARADOM IN BLU NOTTE (come nel porting Linux, piaciuto molto).
#
# Due barre cambiano colore:
#   1. la menubar (Strumenti / Extra / "User: nome"): Theme.menu_bg era grigio
#      chiaro (#f0f0f0), ora #060c1c - lo stesso blu notte gia' usato per lo
#      sfondo del palco (NIGHT_BLUE in monitor.py), cosi' tutto e' coerente.
#   2. la barra icone (SMP/OVT/OVF/MIM/KMN/REC/SOT sopra Elapsed/Total/...):
#      era un teal scuro (#1a4d4d) scritto a mano su ~23 righe di monitor.py.
#
# COME si applica senza toccare 23 righe sparse: si lascia che il codice
# ORIGINALE crei tutto com'e' sempre stato, poi si scansionano i widget
# figli della barra e si ricolora chi ha ancora il vecchio sfondo. Piu'
# sicuro che riscrivere le singole righe (che potrebbero essere leggermente
# diverse tra la versione compilata e questa).
#
# Theme.menu_fg passa da nero a bianco (leggibile sul blu notte); "User: nome"
# (che era in un viola scuro illeggibile, #241178) passa a oro (#ffcc00) —
# stesso trattamento gia' fatto sul porting Linux.
#
# Il tema alto-contrasto (Theme._build_hc_palette, colori di sistema Windows
# per l'accessibilita') NON viene toccato: la patch agisce solo sul ramo
# normale (self.high_contrast == False).

import moduli.theme as _theme_mod

_ORIGINALE_INIT = _theme_mod.Theme.__init__


def _init_navy(self, *a, **kw):
    _ORIGINALE_INIT(self, *a, **kw)
    if not getattr(self, "high_contrast", False):
        self.menu_bg = '#060c1c'
        self.menu_fg = 'white'
        self.menu_hover = '#142a5c'


_theme_mod.Theme.__init__ = _init_navy

# Se un'istanza di Theme e' gia' in cache (Theme.get()) da prima che questa
# patch girasse, aggiorniamola anche a mano: __init__ patchato vale solo per
# le istanze future.
try:
    _istanza = _theme_mod.Theme.get()
    if not getattr(_istanza, "high_contrast", False):
        _istanza.menu_bg = '#060c1c'
        _istanza.menu_fg = 'white'
        _istanza.menu_hover = '#142a5c'
except Exception:
    pass


try:
    import moduli.monitor as _monitor_mod

    _VECCHIO_BG = '#1a4d4d'
    _NUOVO_BG = '#060c1c'

    if hasattr(_monitor_mod, "KaraokeMonitor") and hasattr(_monitor_mod.KaraokeMonitor, "_create_widgets"):
        _ORIG_CREATE_WIDGETS = _monitor_mod.KaraokeMonitor._create_widgets

        def _ricolora_ricorsivo(widget):
            try:
                if str(widget.cget('bg')).lower() == _VECCHIO_BG:
                    widget.configure(bg=_NUOVO_BG)
            except Exception:
                pass
            try:
                for figlio in widget.winfo_children():
                    _ricolora_ricorsivo(figlio)
            except Exception:
                pass

        def _create_widgets_navy(self, *a, **kw):
            risultato = _ORIG_CREATE_WIDGETS(self, *a, **kw)
            try:
                if hasattr(self, "info_bar"):
                    _ricolora_ricorsivo(self.info_bar)
            except Exception:
                pass
            return risultato

        _monitor_mod.KaraokeMonitor._create_widgets = _create_widgets_navy
except Exception as _e:
    print("patch 012: barra icone non aggangiata: %s" % _e)


# "User: nome" e' un ctk.CTkLabel con text_color='#241178' (viola scuro)
# scritto a mano DIRETTAMENTE in ui.py (non legge da Theme): illeggibile sul
# nuovo sfondo blu notte. Si intercetta la creazione del widget e si
# sostituisce quel colore esatto con l'oro gia' usato nel porting Linux.
try:
    import customtkinter as _ctk_mod

    _ORIG_CTKLABEL_INIT = _ctk_mod.CTkLabel.__init__

    def _ctklabel_init_navy(self, *a, **kw):
        if kw.get("text_color") == "#241178":
            kw["text_color"] = "#ffcc00"
        return _ORIG_CTKLABEL_INIT(self, *a, **kw)

    _ctk_mod.CTkLabel.__init__ = _ctklabel_init_navy
except Exception as _e:
    print("patch 012: colore 'User:' non aggangiato: %s" % _e)


print("patch 012: barre blu notte (menubar + barra icone) applicate")
