# 233 - mini console XR18 dentro KaraDom (bottone MIX accanto a SYN, compare col mixer collegato)
# [21-10-2026] utente: "voglio che crei dentro karadom una mini console per governare l'xr18 con questi
# comandi esatti e precisi, anche con la stessa grafica" (pagina "User 2" di X-Air Edit: 01-05, FX 2-4,
# 16, LR) + "di fianco voglio il meter che si aggiornera' a seconda del fader su cui sono posizionato"
# + "il meter mettilo a sx" + "non serve che sia enorme".
# Il modulo e' moduli/console_xr18.py, qui dentro compresso e IDENTICO (fai_patch_233.py).
# Col compilato che ha gia' moduli/console_xr18 la patch non fa niente: il bottone lo mette ui.py.
# [v2] utente: "deve arrivare a tutti i miei pc registrati": arriva a tutti, ma si accende SOLO sui
# PC con la licenza firmata del titolare (console_xr18.abilitata()); sui clienti non fa niente.

_VER = 3

_MODULO = """
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
Dh6XFWtYEdrJ6+FNY6c278TGelfdvtc6y2JyJm42u8fC9f2o9TFsmL3h4OOZy3bmmVWr0i6+j+qPs+G1PhsXQctt1Yub7a0o3BuP
c230vJ0W7sSHaq16pT7O+jcfD3eTWuNi2x8s23f9D6stvgjju3y+WLkQVK4wqCmNNn/dy2qt3toYlucNrrfeKBfGtTh6zjVqzzu9
9jF8sSrtzewd5EH/6bHTGBuZl8cL6K51XbrfKrW5dX+n568HFzfDhvysKqJZF1vl8dWmsKvz1c381ry87jzKd+3Ruzysa+/DqbLr
Vxs3QqG6qD/oVrd92dyW+c3ILLSE5HPBbKyXnXtA4LJ5eZGVBr1e33h6aY/1kWDc3DxuKuJLs7W9vRNLbZAZg3a1aLTnJrer3uUL
75fNer0hr/jNenxVKNfGo9JlpVQscIrW16vK6Ka/um4oNzebi/frm5fGjfZxL1g300dRLtWbt1dN7krp5tblZ61gWdvk4q4zaj4u
c5OVuJxcXpYqT2L3Nr+tgE7QLTSnz9diTV1UXpSPVedpx81b5tNtlrey4mj+si1Iq7tZ93JdfH7O9z6ubvinYc3UC9vn99b9/a3V
bxYX5upxsFKl5zyn6GZvXbnqV3bFx9tGrpnNZgXr4uVdXTelSU58EKaV+5tLXrnU758u7+5u17nkYnGVF6xdycqVtqtsJSPlcma5
dnWRl8SFklEL5UpmtxHa/fbzYF0fPgy0QrvUmQzlW/X+cgEy8rpmSPyOzy2az+IFcv98vl14qpSnBXV9O85knpPjXSk/bSYzyeeX
XSH38nKrTvTJc4W/WIpFq13P56SmqRX6texT7+FO3NUbrfnmTsg97brN0cuiKG4e3q+shnbfe59eVjrVpJWrlCR+aebUVXEtdUtz
8So3bpdm6l1bmFXynAgytVow3z8G9wtpXJi/jAvNxVN3ViwmMx213bx7us6Pb/vXpczNc3+hvze7H0nr5bKpGUNZ4a5vFi+9++F0
qfC1bMkETaqj5R5bj8UL0SzOc41RbaxcNqRy5v5+lwRux+n9YV+Y9OacaT22r4YfutK4TrYuc/PypAdySHlf8A9Pj6CD5DpXYvKp
M21fNhp6u2f1Sr2X0lCsaruHB4G/vsklrQWQzXPBaneemuPZ8mG2zkvX3aayeqoqj9nlx83DyLieNer6qrlODoez1RVX0Lbz4W1n
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
"""


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_233', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def _gia_nel_programma():
    try:
        import importlib.util
        return importlib.util.find_spec('moduli.console_xr18') is not None
    except Exception:
        return False


def _carica_modulo():
    import sys, types, zlib, base64
    m = sys.modules.get('moduli.console_xr18')
    if m is not None and getattr(m, '_da_patch233', 0) == _VER:
        return m
    import moduli
    m = types.ModuleType('moduli.console_xr18')
    m.__package__ = 'moduli'
    m.__file__ = '<patch 233>'
    codice = zlib.decompress(base64.b64decode(''.join(_MODULO.split()))).decode('utf-8')
    exec(compile(codice, 'moduli/console_xr18.py', 'exec'), m.__dict__)
    m._da_patch233 = _VER
    sys.modules['moduli.console_xr18'] = m
    moduli.console_xr18 = m
    return m


def apply():
    if _spenta():
        return False
    if _gia_nel_programma():
        print('[233] console XR18 gia\' nel programma: niente da fare')
        return True
    try:
        mod = _carica_modulo()
        if not mod.abilitata():
            print('[233] console XR18: non e\' un PC del titolare, niente bottone')
            return True
        import moduli.glow_button as gb
        G = gb.GlowButton
        if getattr(G, '_ver233', None) == _VER:
            return True
        prima = getattr(G, '_o233_init', None) or G.__init__
        G._o233_init = prima

        def __init__(self, *a, **kw):
            prima(self, *a, **kw)
            try:
                if kw.get('text') != 'SYN' or getattr(self, '_mix233', None) is not None:
                    return
                mix = G(self.master, text='MIX',
                        command=lambda w=self: mod.apri(w.winfo_toplevel()),
                        width=kw.get('width'), height=kw.get('height'),
                        corner_radius=kw.get('corner_radius'), font_delta=kw.get('font_delta', -2),
                        fg_color='#00e5ff', hover_color='#67f0ff', text_color='white',
                        font=kw.get('font'))
                self._mix233 = mix
                pack0, forget0 = self.pack, self.pack_forget

                # MIX segue SYN: compare e sparisce con lui (cioe' col mixer collegato)
                def pack(*pa, **pk):
                    r = pack0(*pa, **pk)
                    try:
                        mix.pack(side=pk.get('side', 'left'), padx=pk.get('padx', 4))
                    except Exception:
                        pass
                    return r

                def pack_forget():
                    try:
                        mix.pack_forget()
                    except Exception:
                        pass
                    return forget0()
                self.pack, self.pack_forget = pack, pack_forget
                try:
                    from moduli.ui import add_tooltip
                    add_tooltip(mix, 'Console XR18: fader, Solo, On e meter del mixer')
                except Exception:
                    pass
            except Exception as e:
                print('[233] bottone MIX: %s' % e)

        G.__init__ = __init__
        G._ver233 = _VER
        print('[233] console XR18: bottone MIX accanto a SYN')
        return True
    except Exception as e:
        print('[233] %s' % e)
        return False


def revert():
    try:
        import moduli.glow_button as gb
        G = gb.GlowButton
        if getattr(G, '_o233_init', None):
            G.__init__ = G._o233_init
            G._ver233 = None
    except Exception:
        pass
