# 233 - mini console XR18 dentro KaraDom (bottone MIX accanto a SYN, compare col mixer collegato)
# [21-10-2026] utente: "voglio che crei dentro karadom una mini console per governare l'xr18 con questi
# comandi esatti e precisi, anche con la stessa grafica" (pagina "User 2" di X-Air Edit: 01-05, FX 2-4,
# 16, LR) + "di fianco voglio il meter che si aggiornera' a seconda del fader su cui sono posizionato"
# + "il meter mettilo a sx" + "non serve che sia enorme".
# Il modulo e' moduli/console_xr18.py, qui dentro compresso e IDENTICO (fai_patch_233.py).
# Col compilato che ha gia' moduli/console_xr18 la patch non fa niente: il bottone lo mette ui.py.
# [v2] utente: "deve arrivare a tutti i miei pc registrati": arriva a tutti, ma si accende SOLO sui
# PC con la licenza firmata del titolare (console_xr18.abilitata()); sui clienti non fa niente.

_VER = 5

_MODULO = """
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
y/mmWpymitVz6bK6fSusZsb246LXre/MxYOeX+aHj6uaPaqJ3dTV6Lr1obVvpdbmo757a/RW5dRc2m4/HktX9+PO+6hl3Y2G78+5
fG+RXXdq3fLbuPk4H10Z80kZpNxOs7zd3Ujivfm40MfPu1npVnqoN+qX2uN8cP3+cDtttM53g+Gqezt4t7vSizi5LRbLtXNRy5WG
DbXVFa7u8nrnbmOOqotW7m6zVc/NK2n8XGg1nj+Mxvvoxa51t/M34AeDp8dea2JmXx7Pobn2VeV+pzYW9v2tUbwanl+PWsqzpkpW
U+pUJ5fb0kdTqG8XN9bFVe9Rue2O35RRU38bzdSPQb11LZbqy+aDYfe7F+1dVdiOrVJHTD2XrNZm1buHAVy1L87z8vDubmA+vXQn
xlg0r68ftzXppd3Z3dxKlS7wjGG3Xja7Cyv3Ub8tlt4u2s1mS1kL283kslRtTMaVi1qlXMqp+sCoq+PrwfqqpV5fb8/frq5fWtf6
+71oX88eJaXSbN9ctnOXar+wqT7rJdvepZa3vXH7cVWYrqXV9OKiUnuS+jfFXQ1kgn6pPXu+khrasvaivq97Tx+5Rcd6uskLdl4a
L152JXl9O+9fbMrPz8W798tr4WnUsIzS7vmtc39/Yw/a5aW1fhyuNfm5mFMN625TuxzUPsqPN61CO5/Pi/b5y5u2acvTgvQgzmr3
1xeCemHcP13c3t5sCqnl8rIo2h8Vu1DZrfO1rFwoWNXG5XlRlpZqVitVa9mPrdgddJ+Hm+boYaiXupXedKTcaPcXS+CRVw1TFj6E
wrL9LJ0j9S8Wu6WnWnVW0jY3k2z2OTX5qBRn7VQ29fzyUSq8vNxoU2P6XBPOV1LZ7jaLBblt6aVBI/9093ArfTRbncX2Viw8ffTb
45dlWdo+vF3aLf3+7m12UevVU3ahVpGFlVXQ1uWN3K8spMvCpFuZa7ddcV4r5iTgqfWS9fY+vF/Kk9LiZVJqL5/683I5le1p3fbt
01VxcjO4qmSvnwdL463df0/ZLxdt3Rwpau7qevlydz+arVShka9YIEn19MJj57F8LlnlRaE1bkzUi5Zczd7ff6SA2uWMwWggTu8W
Oct+7F6O3g21dZXqXBQW1ekd8CH1bSk8PD2CDFLoXUqpp96se9FqGd07+65y91IZSXX94+FBFK6uCyl7CWjzXLK7vaf2ZL56mG+K
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


def _spegni_voce_guida():
    """La voce guida in cuffia (la funzione di SYN) spenta e bloccata sui PC del titolare."""
    try:
        from moduli.cuffia_guida import guida
        guida.set_enabled(False)
        cls = type(guida)
        if not getattr(cls, '_o233_set', None):
            cls._o233_set = cls.set_enabled
            cls.set_enabled = lambda self, on: cls._o233_set(self, False)
            cls._o233_play = cls.play
            cls.play = lambda self, *a, **k: False
    except Exception as e:
        print('[233] voce guida: %s' % e)


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

                # [v5] utente: "disattiva il tasto SYNC" + "e anche la sua funzione": sui PC del
                # titolare SYN non si mostra piu' e al suo posto compare MIX (col mixer collegato)
                def pack(*pa, **pk):
                    try:
                        mix.pack(side=pk.get('side', 'left'), padx=pk.get('padx', 4))
                    except Exception:
                        pass
                    return None

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
        _spegni_voce_guida()
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
