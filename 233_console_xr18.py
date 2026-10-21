# 233 - mini console XR18 dentro KaraDom (bottone MIX accanto a SYN, compare col mixer collegato)
# [21-10-2026] utente: "voglio che crei dentro karadom una mini console per governare l'xr18 con questi
# comandi esatti e precisi, anche con la stessa grafica" (pagina "User 2" di X-Air Edit: 01-05, FX 2-4,
# 16, LR) + "di fianco voglio il meter che si aggiornera' a seconda del fader su cui sono posizionato"
# + "il meter mettilo a sx" + "non serve che sia enorme".
# Il modulo e' moduli/console_xr18.py, qui dentro compresso e IDENTICO (fai_patch_233.py).
# Col compilato che ha gia' moduli/console_xr18 la patch non fa niente: il bottone lo mette ui.py.
# [v2] utente: "deve arrivare a tutti i miei pc registrati": arriva a tutti, ma si accende SOLO sui
# PC con la licenza firmata del titolare (console_xr18.abilitata()); sui clienti non fa niente.

_VER = 4

_MODULO = """
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
vFjGIdMPfHQ3ZGuS9IAMBshWlnM/3Cev/R7dUnyhUA6uiv+QVi5X2IDJVJx2uo0+7TncEwiJ8+6+Xg+btPfAuQBgsZZGbFIJ06Mo
hch6SPQfPiTeciCMimVgIsJRFQQkRQf+WDsSy1xK1YGpOKqjggYyMVC8AG3ByCIVJjwb9iHbZlQcclQizKVuQN5sWKAjqEYqy6Us
EBqsEV5BF6RtKkby0gf3wN6w+9+Ci5LF5QNMKMEklSr4s1zEdSS3yNMyIm6piFORJbNSr5C1S2cPvP3nw4ALLEYuEbvZb7LW7kf6
O5k2X2/ZIxwec4XKBqG5AiCbBUKeiaiHopgOvHEK4pgEcHkoBhQMVM0CESVnEmmKKpUS9IrIzqQhpKQGzIireSm+ZnbAhFFkaOoD
bIK1cHU+NRrwrzsYzlrDKVydkt9Os/EMX81192k1govOs6C17h76pYL1+Pz0XJM3/cdzPW+9V5aVl+JoOHOcsX3ZPJuvHfV8CnR1
ed+5ql3clnrCxdV9sbVca4/DZulu1hy0ntZ375cNQ2rcFl+K5vvKqmQG6sti8nTXGsy310Wp8LJQ3vWi9XBZ/Fgt62bmLLM8/xgv
t7e1ysP0Ql7p4miyenp8rC9HxXo5v70WVtXVuX5bzN/od/mV3Ju8veXfqhlDra7ymbPe26qsP02U+WNLXj6NxN57Jl8bOspSr3Qn
s2l5UqjcWvqNUbouFid2oVqtVqzq2e3tbbP3VF+NT6X+2d25Wa5UZpuPgbMp5e9EZTIZirKtD58abx+X563eVfv8Ri23Z4+9pr0Z
GT1xs6hYi/FqXFJm1XXTaCxvSrJ+uu60X1pyV2p2m+v245VQXl4MTtfi0zRzMWurbzfmy8TclJt3c2ldlB4vtx/Lq8pb/aP4Vrq4
eOw0O4Y4fCkUrcnm8mNpdLeNTd+o3L7lL5SbonotF50beXulLR6Mq86845w+2vaHDqLTy1tPULX29nm+tqSFaFu9j7tNq70Qe0Kj
udCqw3dRdPqgwCov0ovZOG2dn4q3L8qVA9Jldzg9lxcPQ/XqvtlU26JptZ+N9mAxm95vKiux8Ky2llPt6bx2qxTftNbVsHE3Hb1f
GoZ5916BgZQe1LfzhfXw3hTv3tudZf9y0Ll5aFmT4bBymc9njMvlY+dyMDudvVhjpdV7uLSMl/6NZQyfO9bDYqiWO9ZgOiwAY+s+
n55Lz8XHu6vFXBmMeo3np3WtX8v3prdCRlFarYtZKdOZ3r04ktUdTi76tbu77dXwblgZDO/mlcur6bDfl4SHt7uGVBi81PuSab/N
zzbrqZ1/Ed+de+NceJirTvly9gyV++a80WtlHLNjSC/z2c1DR5Zbzfm7U/joOc5o5Dw0C2Pj4bJt3zzfPWf6c6PxcDfQb0uV0/ak
mHe2y8p4LBYvlN5jX5c35e1gej3JTzZnWl2S1k/2MDPftPqrW9uu1TcludNerarFbmYw7LVLY1s0b+979kPtY31fnp/1Tgfzl8bw
/r09d977A709eDGNM7lUWd1ORs51qyHOpoDUE714W7RH9Xtn1NVrd5X2h2aXnLlSP3eU1ro3uS2WL0ub2aIlO3pX6t+Y66r0aD1d
i5W3O/n24u3qYt292LTGPeFl+j7r9x8Wd9O3+eN8unFeOkb7cTi8eny0b14c47p9Zi6npdO3s8XHWCp/nJ33bsX2y3yg2u9TrSOZ
9/3z88p2LHRf7uT3F2H20Ll2HvpX1tP9ozNQH+7URbt7N9J71Y/i+Xn3dvq8FZVevr9Ub29axaezxnw2mj/1lqOH/NONXP/Y1pvy
9l7rnw7vrobTi/F8fmptP6a969OX65lVyjeq/ZfM/ZnQ6zlrcXH+eP4+HH7MFrJc++iVnooTSTWeZLs4L9ycXr2/9KVh471WLV70
SpOlUnwRx2P9pXhfaim3F2Zn0XyRy+LF+fDcOs1syneFjnBTvxBvPy7nw9bHXB/OrXn7Zm4OC++a1vl4PF/W6qtZ/fl6Lj32as7j
YDtuvNcfr4zMzduoK28+Nj2tvejcSFdPm/zzqahrxuBJLs31ulEuyx2587YoNnuyUCoWb29uR0JefltWp+V6Nd8ej9fG0DTm61Pl
+W7eNDuw+Kf355XL57OBeis/l6zrx+FTc1p+Lq21tjDunb/I1cx7Wz9vjM5l+WL5oZZBV7udNOzH4aLXvXk7u0EUMIfv7Tux/X53
pc7Gw5b5Zg0frKn4LI3u78zz6uDqfpQ/nysP6t19Xqj2PpyhfvlebZTXmcmlpkx0TRMe7y7zl9VK/dnp3U9LrUZh/djclIbORNuW
5VF9fWGPtOv14GGTKW00oVaQi/rm7U76GE8m4va2uMqPMx8fRVgC+0FdLoSzy7vRYKYtM7d3s1bB7M+L5zfG+kypOtXxtahftKTH
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
                rif = []
                mix = G(self.master, text='MIX',
                        command=lambda: mod.apri(rif[0].winfo_toplevel(), ancora=rif[0], alterna=True),
                        width=kw.get('width'), height=kw.get('height'),
                        corner_radius=kw.get('corner_radius'), font_delta=kw.get('font_delta', -2),
                        fg_color='#00e5ff', hover_color='#67f0ff', text_color='white',
                        font=kw.get('font'))
                self._mix233 = mix
                rif.append(mix)
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
