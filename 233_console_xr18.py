# 233 - mini console XR18 dentro KaraDom (bottone MIX accanto a SYN, compare col mixer collegato)
# [21-10-2026] utente: "voglio che crei dentro karadom una mini console per governare l'xr18 con questi
# comandi esatti e precisi, anche con la stessa grafica" (pagina "User 2" di X-Air Edit: 01-05, FX 2-4,
# 16, LR) + "di fianco voglio il meter che si aggiornera' a seconda del fader su cui sono posizionato"
# + "il meter mettilo a sx" + "non serve che sia enorme".
# Il modulo e' moduli/console_xr18.py, qui dentro compresso e IDENTICO (fai_patch_233.py).
# Col compilato che ha gia' moduli/console_xr18 la patch non fa niente: il bottone lo mette ui.py.
# [v2] utente: "deve arrivare a tutti i miei pc registrati": arriva a tutti, ma si accende SOLO sui
# PC con la licenza firmata del titolare (console_xr18.abilitata()); sui clienti non fa niente.

_VER = 8

_MODULO = """
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
t6yHWV8rt6zeuF8AxtZ+Pj6Xn4uPd1ezqdobdBrPTx+1bi3XGd/mD1S12byYlA5a47sXR7ba/dFFt3Z3t77q3/Urvf7dtHJ5Ne53
u3L+4e2uIRd6L/WuPLffpqerj7Gde5HenXvzPP8w1Zzy5eQZKnfn00aneeDMW6b8Mp3cPLQUpXkyfXcKnx3HGQych5PC0Hy4PLNv
nu+eD7pTs/Fw1zNuS5Xjs1Ex56wXleFQKl6onceuoazK6974epQbrU71uix/PNn9g+mq2V3e2natvioprbPlslpsH/T6nbPS0Jbm
t/cd+6H2+XFfnp52jnvTl0b//v1s6rx3e8ZZ72VuniqlyvJ2NHCumw1pMgakHhnF26I9qN87g7ZRu6ucfep2yZmq9XNHbX50RrfF
8mVpNZk1Fcdoy92b+UdVfrSerqXK251ye/F2dfHRvlg1h538y/h90u0+zO7Gb9PH6XjlvLTMs8d+/+rx0b55cczrs9P5Ylw6fjud
fQ7l8ufpeedWOnuZ9jT7fay35Pl99/y8sh7m2y93yvtLfvLQunYeulfW0/2j09Me7rTZWftuYHSqn8Xz8/bt+HktqZ1cd6Hd3jSL
T6eN6WQwfeosBg+5pxul/rmunyjre7173L+76o8vhtPpsbX+HHeuj1+uJ1Yp16h2Xw7uT/OdjvMhzc4fz9/7/c/JTFFqn53SU3Ek
a+aTYhenhZvjq/eXrtxvvNeqxYtOabRQiy/ScGi8FO9LTfX2Yt6anbwoZenivH9uHR+syneFVv6mfiHdfl5O+83PqdGfWtOzm+m8
X3jX9dbn4/miVl9O6s/XU/mxU3Mee+th473+eGUe3LwN2srqc9XRz2atG/nqaZV7PpYM3ew9KaWpUTfLZaWltN5mxZOOki8Vi7c3
t4N8TnlbVMflejV3Nhx+mP25Of04Vp/vpifzFiz+8f155fL5tKfdKs8l6/qx/3QyLj+XPvSz/LBz/qJUD97PjPPG4FxRLhafWhl0
tdtRw37szzrtm7fTG0SBef/97E46e7+70ibDfnP+ZvUfrLH0LA/u7+bn1d7V/SB3PlUftLv7XL7a+XT6xuV7tVH+OBhd6urI0PX8
491l7rJaqT87nftxqdkofDyerEp9Z6Svy8qg/nFhD/Trj97D6qC00vO1glI0Vm938udwNJLWt8Vlbnjw+VmEJbAftMUsf3p5N+hN
9MXB7d2kWZh3p8XzG/PjVK061eG1ZFw05cf1x8PF5KNWGh2UasfKRW31VlyM56vP0067sbamD2ZhVug9LupOvy63Dy77V2efxvmN
cvbx2Vi/nXQWlYOJslp9PpYv7wet9/6ZfdfvvT/nC51pbtmqtytvg+bjpH85nwwrIOW2mpXV+lqR763HqTl4Xo/LN8pD46RxYTxO
ulfvDzejk7Pjdbe3aN9035228iIPb0qlSv1YNvLl3ol+1pYu7wpm6+7D6temZ/m7j5V+bF0qg+fi2cnz5/zkvf/i1NuryRvwg+7T
Y+dsaOVeHo+hu85l9X6tn0yd+5t56bJ3fNU/054NXbGbSqs2vFiVP5tSYzW9tk8vO4/aTXvwpvWb5lt/rH92G2dXcrkxaz7Mndv2
6fm6Jq0GdrklHzyX7bOPReceJnBxfnpcUHt3d13r6aU9nA9k6+rqcVVXXs5b6+sbpdoGntFrNypWe2rnPxs3pfLb6XmzeaYtpdXH
8KJcOxkOqqf1aqWc183uvKEPrrrLyzP96mp1/HZ59XJ2Zb7fy87V+FHRqs3z64vz/IV+W/yoPZtlx1kfzG46g/PHRXG0VBaj09Nq
/Um5vS6t6yAT3JbPx8+Xyokxq7/o78vO02d+2rKfrguSU1AG05d1WV3eTG5PPyrPz6W794sr6al/Ys/L6+e31v39tdM9r8zs5WNv
aajPpbw+t+8+6hfd+mfl8fqseF4oFGTn+OXN+DhXR0XlQR7X769OJf10fv90enNz/VE8mM0uSrLzWXWK1fWyUM+pxaJdO7k4LqnK
TM8Z5Vo997mS2932c++j2X/omeV2tTPqa9fG/ekMeOTliaVKn1Jxdv6sHCP1L5Xa5ad6bVw2Pq6HudzzwfCzWhqfH+QOnl8+y8WX
l2tjNB8916XjhVJx2s1SUT23zXL3pPB093CjfDbPWtPVjVx8+rw9H7zMKsrq4e3COTPv797Gp/VO48Ap1quqtLCLxrLyod5Wp8pF
cdiuToybtjypl/IK8NRG2X57793P1GF5+jIsn8+ebieVykGuY7TPb54uS8Pr7mU1d/Xcnc3fzm/fD5yX03PT6mt6/vJq9nJ33x8v
dOmkULVBkuqYxcfWY+VYsSvT4tngZKifnqm13P395wFQu/y82+/Ko7tp3nYe2xf997l+dnnQOi1Oa6M74EP620x6eHoEGaTYuVAO
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
z4O5yaHGNw+guPf/A2gH15U=
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
    """La voce guida in cuffia (la funzione di SYN) spenta e bloccata, per TUTTI."""
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
        # [v6] utente: "SYN lo togli a tutti": SYN e voce guida via per TUTTI; la console MIX
        # resta solo sui PC del titolare
        titolare = mod.abilitata()
        _spegni_voce_guida()
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
                mix = None
                if titolare:
                    mix = G(self.master, text='MIX',
                            command=lambda: mod.apri(rif[0].winfo_toplevel(), ancora=rif[0], alterna=True),
                            width=kw.get('width'), height=kw.get('height'),
                            corner_radius=kw.get('corner_radius'), font_delta=kw.get('font_delta', -2),
                            fg_color='#00e5ff', hover_color='#67f0ff', text_color='white',
                            font=kw.get('font'))
                    rif.append(mix)
                self._mix233 = mix if mix is not None else False
                pack0, forget0 = self.pack, self.pack_forget

                # [v5/v6] utente: "disattiva il tasto SYNC e anche la sua funzione" + "SYN lo togli
                # a tutti": SYN non si mostra piu' a nessuno; al suo posto, solo dal titolare, MIX
                def pack(*pa, **pk):
                    if mix is not None:
                        try:
                            mix.pack(side=pk.get('side', 'left'), padx=pk.get('padx', 4))
                        except Exception:
                            pass
                    return None

                def pack_forget():
                    if mix is not None:
                        try:
                            mix.pack_forget()
                        except Exception:
                            pass
                    return forget0()
                self.pack, self.pack_forget = pack, pack_forget
                if mix is not None:
                    try:
                        from moduli.ui import add_tooltip
                        add_tooltip(mix, 'Console XR18: fader, Solo, On e meter del mixer')
                    except Exception:
                        pass
            except Exception as e:
                print('[233] bottone MIX: %s' % e)

        G.__init__ = __init__
        G._ver233 = _VER
        print('[233] SYN e voce guida tolti' + (' · console XR18 (MIX)' if titolare else ''))
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
