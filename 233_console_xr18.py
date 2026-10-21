# 233 - mini console XR18 dentro KaraDom (bottone MIX accanto a SYN, compare col mixer collegato)
# [21-10-2026] utente: "voglio che crei dentro karadom una mini console per governare l'xr18 con questi
# comandi esatti e precisi, anche con la stessa grafica" (pagina "User 2" di X-Air Edit: 01-05, FX 2-4,
# 16, LR) + "di fianco voglio il meter che si aggiornera' a seconda del fader su cui sono posizionato"
# + "il meter mettilo a sx" + "non serve che sia enorme".
# Il modulo e' moduli/console_xr18.py, qui dentro compresso e IDENTICO (fai_patch_233.py).
# Col compilato che ha gia' moduli/console_xr18 la patch non fa niente: il bottone lo mette ui.py.
# [v2] utente: "deve arrivare a tutti i miei pc registrati": arriva a tutti, ma si accende SOLO sui
# PC con la licenza firmata del titolare (console_xr18.abilitata()); sui clienti non fa niente.

_VER = 7

_MODULO = """
eNq9vdty6tqSKPjur1CxYpXRMgbEHe81VxxsYxtfwAbj26wZLiEEyAgJSwKDT50T9dhvJ6LjdHRER0dHP51fqO7XOn+yf6B/oTNz
DN0FZu7ae8+1bIM0Ro5bjryNzBy/CIe/HQqKOdSM8ZGwcEaHNXyyl0ql9hTTsE1dfV1ZUi07Xwt//tf/Lsw0QxP4C2GuWsLYXKqW
IVuqoOnCsTqxABA8fupKNWEoC0PVcCxTuJIt+dScZff2vhekQyl/WMgXKj+gPXitHgmppTnWNVNQJqqgWKrmVptCtaE5ExaGvK1l
fR+7iC/33heq7WC5mWwMNUG1ZQe+QgVLVTRbywiyQY2YhqDLgu2oti0LY0seaYqcEtI2tK4a9sR0oAs6lJjLYw0aT/VtaLGQ2gOY
T4cNzRKaQ80RhQMhBU9GGkA1BT4ImIeZ6kBxbMjWBHk81kzLUC15X4AmVWibJkYXRvIQitkLQVlogm0a5t7ctLVPzTRkx0whcNZb
TTAWM9XCccDYHVmBh46Do5jBuGxqUllYtolzgZO3hD7hxCzGC1nXUjDt102hd99t9U6aQhrmSAc4OEBT8EecEQx4sm9agAuqeLQn
wL+8JOQLQr4o5EtCviz8+78JZ09Cgf8t8r8l/CtV8Pd1d69tzlQB+6a73YFxQwdvWk/NrpDOwfBH2jhnyDM1I7jfqLR4RJMgUP80
d/qW6hAfagab+OxeZ2wAPhwJBjYEbfagLv4dHuNvNqewkDKsnpTPZst57A2bHRFLsMWBD2NrMZ9rwgywEL92DPxNM21m9xpCr9Vu
wZw1/AU97zbap01aOkU2ZJhDW9VVvl5CWtE1BVcTsdV2LM1WNDkjjADzFByJocFDOTdU8Y+Ia9JAiGetk4bQ3If56fW7jfsGQIit
C2CrLJiw7Jp5BChpw5KXq5myMF9lODoI5hi2h1TIVAvwdC/9TZBysCQMiRXTsmHC1H3EeV0dj3HxNT5VNKsZ4UDKC3kBtqZwWIQf
mLVDzRgJ6vtCG0LHZQO2EWDtQhXkPfgtZgRLe1/IQ8JKWj4NN5mN6w2ftJWqZ4WWLpz0u71Ot4mNW5ojww7BuRrK4TGynWjupU8a
t6/HlZIo0NpbGkGG6cQ1hs5b2phtHY5e/lJkhfuFA5CxA5qtjg2ZNvlt61qAtuS9mWYvANBAtlWhmq+tSrWyMDN1R5vDqsmOTCQF
SQIhDpu3EWwEXKwMgLK1fQJkjYGwmAKMFOpoSKegj7CYt93Ofeekc33dEdKd3gniQf/0FjAwXyhlBBwsjVAIERCBjcCRB7rq0JbL
rWDWTdzCqgDb9bYDCAezl+bgkKrhxkaMWC5MHcDBN9mytCU8Fv8E9S11ZjocH2qCLTiaaqgAGdARFgBXETf/DCg+0DxAnJGMpAQo
EmDXwoC9B0AI3W33b07yoY1krzUgS7q2xK0K0NOlvLCUEQuOkBTQmgC1LeOiA/HTcPiWagryYnUwWkmHMCcVYbCwM0A9aFDQhxFg
83U3A30zsBJsEQExaGRaM8IZmKmBbg5cxDBMW1EJkwCpF8Z4on5+ApZrhiNVcoVyBQlCmuZaFMz5fAE9Humm7CDYP/8f//f/9//8
N0BYc4lrD9gE/GUFGHDWat/DCtKL1wgDBPoE0wRMB2cOJwB2qjBSLWBU+r4G7Eah5QTwRJKwv9dI8Q4BVZwcorD9kSsWELe14LA0
Rl6yxHS12dy0HMLTSsn9ppnuJ6gycT+btvvJNpWp6njfHGuh+N/WXjFnYqkycnrvgTZT9/aQV7/edrr3wjeGr3t7v3ACBrw5va9M
9oEGicK/wOfRyv+sW/A5L+5xxvJ62jxr9K8RSkrKFDLFTClTzoxWBfgpwk8pI1UyupVC6Id/y38An3a7ynZ7mohRjN0JlWIeqcCf
cDHmsmHQe0bokQDgxkeqBWgGooj4N+/0baPX68DclavZshD49wsiXZCl4Abel3XoHnCQ7nnn9aZ5D5wVatb8OrEBudwMaBHQMBNl
BzUMNp1CqgJyDpAexnth/AZgqZoS957y0ECwuQNg/9TSAAQG02Vvpis2WdrMB71337l9vW+cAKMDDKuVvAH+QmxneMwG7xcpZIGN
sQJRNrZ3BiQR56lYq2XzoXlChrV30un2EAYrdih4Te81ru+xHiw5YiBnWYwtONreySvVeL1oNk6hVFqqZwT2I8I7huItBJwuFjMC
+wm+ee01r/FtpQCUjX7wLbxod+hxJSMUSvC8UKQX7lDTErIHqVDBX1V80+7fNLstelWE8lIR3xcr1FbnGiap2aNxpKVqHt7wX97r
4073lL2WqvCG/wq/LuD7qpQR2A++PD1+dSc2XaoB4Qaw5QJ/48GsADT2w994nSkUqzg29otG3uyeXLToHXaR/eCLh2YXZCicRxhY
oVyGiSx542Y9L5ZxyOwXvrrr8zVJekGDAbKVEdxf7pvXbodtqXShUA6uiv+SVS5X+IBpKo5b7UaX9Rye5YnEeU9fr/snrPfAuQBg
sSYiNmnE9BhKIbLuk/6TDom3AgijUhmYSP6wCgKSagB/rB1KZSGlGcBUHM3RQAMZmShegLZgZpAKE8+Gfci3GROHHI2EudQNyJsN
C3QEzUxlhJQFQoM1wE/QBXmdipE8ce8e2Bt2/3twUTK4fIAJJZikUgW/lou4jvSI3pYRcUtFnIoMzUq9QmsnZva8/efDgA9YjD4i
dvPvtNbuL/EHTZuvt2wRDo+EQmWF0FwBkM8CkWcS9VAUM4A3jkEckwFuGooBBQNVs0Ci5ESmpphSKUOvSHamhpCSmjAjrual+prZ
HhdGkaFpD7AJPvJX52OzAf/avf6k2R/Dp2P67pw0nuHPyUf7aTmAD63nvN68e+iWCtbj89NzTVl1H8+NnPVeWVReioP+xHGG9uXJ
6fTD0c7HQFcX962r2sVtqZO/uLovNhcf+mP/pHQ3Oek1nz7u3i8bpty4Lb4U5+9Lq3LQ015mo6e7Zm+6vi7KhZeZ+m4UrYfL4udy
UZ8fnB4szj+Hi/VtrfIwvlCWhjQYLZ8eH+uLQbFezq2v88vq8ty4LeZujLvcUumM3t5yb9UDU6sucwennbdl2XgaqdPHprJ4Gkid
94Ncre+oC6PSHk3G5VGhcmsZN2bpulgc2YVqtVqxqqe3t7cnnaf6cngsd0/vzuflSmWy+uw5q1LuTlJHo76k2Eb/qfH2eXne7Fyd
nd9o5bPJY+fEXg3MjrSaVazZcDksqZPqx4nZWNyUFOP4o3X20lTa8kn75OPs8SpfXlz0jj+kp/HBxeRMe7uZv4zmq/LJ3VT+KMqP
l+vPxVXlrf5ZfCtdXDy2Tlqm1H8pFK3R6vJzYbbXjVXXrNy+5S7Um6J2rRSdG2V9pc8ezKvWtOUcP9r2pwGi08tbJ6/pZ+vn6Ycl
zyTb6nzerZpnM6mTb5zM9Gr/XZKcLiiw6ov8Mm8cN8+PpdsX9coB6bLdH58rs4e+dnV/cqKdSXPr7Nk8680m4/tVZSkVnrXmYqw/
nddu1eKb3rzqN+7Gg/dL05zfvVdgIKUH7e18Zj28n0h372etRfey17p5aFqjfr9ymcsdmJeLx9Zlb3I8ebGGarPzcGmZL90by+w/
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
njrj9unZ2bx959xV716qfaVhfj48yNLlVfHAmQHaPJeddufpfDhZPEw+Surl7bm+fGroj4XF+9XDwLqcnDXny/OPg35/srzIl831
tH/dmT3MB/PbwfV1td4/yC2rNWd4e1svLOqVQrFYfr4DTtXsa07vqmLfzdpD660tO8/nT28vE7s+mNcsrTHJHah393X5Rs6VnKen
+dlgUC3N24WqmmtfGLdtdflUrNufl33r4QBw/XE5UKWhOrq4qOaeao25M7xR8nLlTW2hPN3o9R863avyyXOr9S1FgvhJs31P+mGh
kC3Tk9MntBWEjCUC6RRclzCFuWw5KhZBYd+c00EJU6SYRcEzUPw9bFJoFU7LaO00j0DBs220vujawFIttLSggdSQ//Z2Jphz4dVO
2/yEZwBzaGdVQzGHajolw2xoqEFqYwO0shSecA1S/7TK51NU+mOi6XgIZaQHovCrUDry9L+BcPAtVNRSnYVlCAOYW2zStJW0PBxa
GeE32Rq7rcM62RnQw0CBAyUrAy0PUqz6yESrFWh1WNpvRhsJmq0ZeCChqGkZypumLvrvXaDYm5SW+hODDV+YUTQ7l5VpOvUHjlEz
nLQsil5VVY8BhyJ/GWx5K1gyQ28CPNoIeBQFbKsbYNgBGLjWjuWNlC8LPMXVwPWFj1gRP2Idf71e8ahIS8/dtbLWfnMqqsxZzRiq
qzRfdb9nCBnffz9Sf2SH6gbU8tcU7SkqNA+6+j8K/7UYWmzhj2+Eb3NRAIyYf9eONCgp/RD+AdEtkwrPAB8dQ7TvP7x3TkJ/YXn9
PtDUYZcJ+pGzU8ffsONOUs/NhYNWFr8DiM4OojM2FO4zjBIKE0qFX3BAWXk+V41hmiPDwgjg2fz729Ebtv9D/J7/If4JugRLXgqB
IQRkLYx+roXRz7dgJ7RgJ07+m7itK9isHVgEXXY041AKLgP1BRbATlqASLcGCd0yBG+DbZnTxAEndBZrGD/cPtE3tJFHuhXCT4BA
L9SVos4doUl/NNM4ihZvm4bKtyU7kXsdyvornoUBGWalU6nUNTuMQyQbHqNti52WDTXvHK+dZWePdEhWLAhpXXMcoOcwBk02ROF9
gce8MAOmxo7RCDTAk9h5mgaAs0JPFYInbgKdexFJQ3u1rdEJMx7Z0zNsxFBlSxMO/4DqYjbFCXyInCSsxe+4FoPvR2wZgjTBEH7/
JuSRHBjCH0Ihn0+kAd9DdTjLAmJSoqX5Df7KxtB9/nvg8UH41T/4VQrhhpYJnf51OEoBYzSw66UjD+gPMbGLhTy8xCO9rG6OpXx6
JWJfVzAqST2sE4UXDqUCHnQgAVnhWiz9cSV3YJLQgUKgA27jKyEnwLImwP4SIWFuUWJKdCUQ0srCWsrAvB0LnW/EIzqYyWbZUY/w
O+ABWsIJnYeDV/kVz5jSQxeThyiREOrgsz2+fvAUFv2wns/mY72BZ8FiwmElqRRAg8lAACIMvFSL1SpurlXltaRKrJa0uVaZ1/Ka
4m9nmpGWsvkML1Z0u4R/+TbHKYGZGQ7SBp8W3CEzeZXOY0UPApsnQxS9iTIQx/PZcqxPhIdQWzikFiPlC8kVaqxCOV4hX9lQheYI
6lTDdYSkeaI+8TbqkVmitebT4YB0bAZnYwizEZwjb00IS2r1bD3WVurwnxaFgqRy6oPy5q9ZiXbrMNhuCppN+Uz5kL7STnT+LmoC
ehWxs/e/eWOKLtu20ONKEJ9ZVA9eNUNzXl+BteqjjOBocxMP/f0pxedZ9pg+InLyUkGii49oEpVJhP9SLTqdh7c5ZZL7NV8YEt2K
F2MeWbRemwuRgxDghJD87xch7IWRl4ACVeJg2Gk5MHDAP0HKiPESimopE5RYC2EJ3xvraLV1rJZj5H79eqhnT8KvX4xVqhJxTxir
VMtmCxKeEEMxebEStwxUqgCUAuxDI8Mg0udtA5e2aCDhsaKzx5YxXndTGwdXLGxaSO66E/fEYQ488NDcMtxiJSPgAfXm4eXDWI5e
hq+4Kb6Fuu+uOEgHKRgmIxA0Iqr+n+aWOVctZ+3tKeZsSDtKjNEmbz+58Pa8euhXZGmfn7GqqDF/9+f7AOYbZiBHnDiVEeJvTCP2
OOCLmcrsCckrGShIB68og4d3k7svvQUMiV70lA0/jCyyp3eE2hpb8xz6ZAY1xFFgihIJyi/CWNaMI/LlsVR5NsezYXIkZbae/Vb7
vNtEdwAYA8gteM4se26c3kE9aOmWkmEn9RH4WNIca4oGMj5IwjYgH/lxcRCGsLBl8gMbW+ToF964pIp/T5xUapMmdaLKQ+g6zGdx
mMPx4KSmOYUFeiT+iCkSnEFyjgF6wSvxyrRrXggpoijnzVHOSzsoPUf8tsSsPQeFIA1KdQDN5qS7Ifx5WgQx9UO10gG1OSjE85Wa
0woBEm/VNV2uk8aS6FggxnU3bFe2HPtDcyZpJKzijiChKLPvzL8Xjn6IibB3BAWYxkEFwWyWkGnOgK0GRQpcBJjv2CJFF+DvIl9o
ursFZqrhmL7v499J3LjBtjbKGh65i0ob3gvAR+9zpAjiKunKEY6iTBNfLLUlspozGWh3tLERcahUBJIjk6/If/4ve3HuYocNPoEX
r7gFXenWbx3ekL9JjOW86qzHnrtm9hoeBHYdK6UqSX15tRaGN6g97hh3GFryo5CXMeDk3DSAaajemvDC7pLMM+QoClj8TcoWoguD
bsNDLdg7ZJXkkJplf9L8W+PstdVu3mfct73OydXr6Xm3cROonLVVh7eW5n+3kBssbgxhK6F5OcWGlUJnI+y059ca2f/DjPBKVm9L
VZYjy5ylS/l6JaKhQwHfBDoUo0TO8kwE1nfpBzMsJFm+Asj0qy3A/+nRB/wRibJj1e+FHxmBPkjuh+KPKL2Kilkx2LSBUzuSp9gs
splUgJer6UjTWwGFaF2EM0V2VXBZUdsMr6nw9b9fhEfY9uaHfSQYGkYNCeh4DaKflM+XSyQAMrRCP/kIjmim4uguFvZanVco8nrS
abdBIkB8pL7+NHEPEZiMS4IyPm3JhHakzXbSvbVQ2W9/Brx9fk+f0sD0xqrzjdfWFHWp4SGJOjONb6w+SmzfUuiXfsid1A8tYI+M
Xwb581bQGBqgvbKufgV+Kv80eNo7rw6GZXwN/z0BPEclmiyfYQTARmXiX4Rb8ug3IwrBkVDOC0OKCQM1foEBDyB1aepMRask0GCM
UZANk8WZ4LkcnRwG4KYp2ghdA/PlDDd3gRRI0VAqC4YC6Iq8BChiVuhh+JKmDpmLNYUoLE3dkTMCC6b51GRHzQTgu+EurBIXXNEL
G32yQZRlQRcwsJGGIWH79FzZhw80EdnQQcNYsyhgypKNsZqW8hGxiTpqIN34LvvnbBEu6wnuKp6SCZpNDPRHlA4apuPBQ4MshvK4
SB8nFmxBQ4+99jmUeCXeyhawG0D7bBgDTNJy/MABKVLW1lV1jna1fClcIvQW3vn8kbG8CPLF2e8O0kYmJKMEyElIXMHF+FvTcG90
bLYY74+f2PJek6wVp357kUVL28QntbmYZKMPlg4f84aknO/Yix9kYoIFwV9pPKzMZ8MqGmoJAQFqA8ckGc6DiK0GTxeSJbSDoNFj
uwwSnLAtYsgOLMa3HKAEFVgNeCYvdOcbYkhgWrcOP2hnoBlg+zoIL4DfAcYQRXLmALBhLwY2W8oNREuJm4sw8ZhUXzfSLFIcqcNr
gJRVxL8yfQjt8XJwDhjf/bnxB/dElFLaLg2N928AvHP69faOy62VcrlYTtztXNjhIlccFrBdRzMCQkig7olpGKqCaNlVQWxropwV
hxAQyGwyhDB2a2Oon6woGLMk4PnPzOTMS9D3IyKbQNHaptvZhCbajPvxWMwjhM57Dlx1KMi2glzVwiAvijiCbjCZRJiZ1CZGddoq
hkmL2Z+ahC3kMr5cX2kLiJ/WjovANiUSEABqRSEx14pvwR1DFJbKE6kNeJow4pYRBmtHtRN2zgzPlCIHyrySmLTNZslbK6DqZmJ6
7ywTJNu7TQFnBzSeIM3/w+cJAfqFx2bxjn3JDX6SI2zgCsz8Jg80XQMwcto/jk9OdEAqtxdBK5P0BsIWbB5VE+YKkKkxhYk7Wior
XMtewgOMdAHZlJMnTbg9YZHDmmPqAOkII4zpIB6P5uGv8SkLZ63uDQaUg5zKNxrUYoIshmyP6RPF/DFDiiLPBhpJwVQdCAzsHpVt
Pmsmg1jbgO2no/alMU86kDxhIm5aT0wchQrQl+QTfqRXQpa6Bhg6FngEqm7Kw1f21McBPN0LvkiT70/A0uEes6Jj05BQYR8Hs58R
9vdFMWqtzMTZu1+Pz8OGqiLutfQ+qA7AEBUTS+nqbGDui7sdlHMzDCEJnjDIrwjdw5HWLa0iUc4jV+pnMV8Yp4Sugm5cOkcEoAw6
dHFGa+BnsEBmBdCZWyNBX5qADOOFNpSFNDRjyzqpDzlYFaYh6fvA9JFmkmICL2wQv203AgpDrWATi9sWE73FyJjN1/KUf/fFOhQS
0+5jnO9XZvPGafdDq2FO2PTjKsMfdxFCfmDzRIGGS5yb18HT1hP6ryxGI01+ZZPExwDqmYJ5Rahj0dUMvUyLP+W887c37LK0B6aQ
vm1d/+3dSDFc9P71pHFy0WRWSIbkryMTbeUrdMzUh9+YZYXNCU065mPgU93CeL0zKE5v5yvu4FBh5nbLXKBn1cq1uqN65MH1zvun
KBsGuhKb/cC771NG1WG7k8fh95RsabI+GGYdBz3dUg38KhwDfPfJtTZQkRabRg/2xmHw1an6Jj8swo9j2jH2lR0N8sZCTW1opauO
F0DT4w2xNkROqy2HsriAEm/a2Tn6EL2ZmgFKSFY1lpplGkTfUo+t9mmrC4Cs1MnRP3GRDU2kKZx6/BSjjqncwrZy9gRoeQ6X0845
1kJ11nM1p3tdJal9Y7khdHq5SO0C+/7+LBFWoCl+ehU04o/I+wsWH1fzKGT9UPCxOz8RxYrktMBsKZnoWbc28kqoK2DFdnqeIF0k
yuduJz3EzrrzkQY1cL4SE2vEpcndpNCYLRJ6PgoX80Hju7j+ERvFht7jHJMgGRzD9h6GIREz53omp5vhjYkuX8ETsxGQE3ZcdMqo
mscyT3lyFxSc5ABjFNzULbaQlvCMSEhO+8A4WvLxkxjhEFFiFTH1KPI87w4za85VI62Z2WOUtVudNEvgkR1UStyF1c1sA0IGdBkD
vtOp7vlxIyXGwdqcpHoGJ3nOTQAs7w2I2Tv3lQinW41RVRDTi2KIvU5JRXGtgNSFyLnuzNVtadgwhPk6Is4TBddmtNjpuBq/9tV4
KGRrnyoenMTx2nNGDJfNJ5UljMkIY+AKGXKImK++A4tYJ4vvMM40L83kOgpGz7N4dKZFJTfBRscgQyM899CBkJYjHkIfGWHCJgH7
nGDNwoll6A5lMFvSp5pOI9eTglzvQ/gNFlgEIh17NeGvEsh28j+GndeN9slLpxcjdXiA5fcMNaxSfoPhjEpk5+Y8bagrJ62Bhhes
KoqJTi3uiANHkXT2zYLxmUQq6+QiTCLv0Eu4ZLjpzZhMaqJZGmgJ+lpQ7hJyNvV2CDtQ5weWoHMOAQSsl7IG9TNDebLcLeDLJbCL
vpEXJWZEIV9msqlleCdCwsvGfZZhf04t+WMvSPxcQQjXKyi0EF1GF1cQGWAeBwNzlaY8EyL1FGt9G/lFOUYNBt8LP4RD/EsK/eB7
kX+Vwm7O7kgInT9gPf0n0BHvaT7qPYMiN2w33Hd+DZY9CXM+sfxXiqkx6Ymcv7WItXw294ihoX5w4pYRAJsPhBIOA730M15SjbjP
hzeRWfyVBoAizVE6XfCHXnCHHZwv+Kvp+jd/Y+LOjkA3PriAyfdTaGLEpLHAb2+PGh/+CLZtqVlW1ucTTB01w4wSjorDQEMwtKgQ
MkD/oSs5oSCyfihr/jTN4NMrUdxmLkdC6wH7IL9Xnq4IRc3Am1zAS3HI53Llz6XX9ARLfjmxAesodMg1SsNOW8FiruFnBVO7hh+b
V2O7yVw4uL/5tw9t6Ey+SaFDO5d1/y5IaDXkieVMnqlIQs6yBP17Kbt5G9EYyHMMkXMX8PBPjWk+aCIcqWiuCIzcUhUHuImupr+v
8mxHrvlfxAj32Uri8yFx0usWWvsvfiQTXhov/vLHy/8ml2fTEKf8+Ngl8f50E32MzDebbjsgEsyBViJBC8ztxMV5JHNUgIB/MTVB
rHBnxX184CEL+ivEsYNIPMVg8kVEAwdZmtKY88aE+fET3pgpcj/yc96I3pCxSpieR7EMS7ijf9WGq7BQpDBHISftF0DzQh7DFgOe
vw4UQcGBEuN8h0q/CrUARXX7iRuOQtFqCARhB7120D7hlkw4EaHNsmWbpJPJIUCFhv4B20SyzT5v4s5b2nDxkYbqbsBCuC0+SQ4d
suGMsMa5UIgdrImMuqQLmGXJ/SV+5Qv81diptY198RMwuS+RJOALQMpDACrCbz80i3F8ep0HRF1JIsNg3McH0KwYIog+l5ZKDMPR
0SDAepOZNEM7zqeBKwexwGW4tFNyQj5bYWuXgv+Yrqq6xq0oA3Yscz43ibOaPEktlITZM48o6yZlNMow0YcSP+W81E/h44MMhfQG
m3L9OgXgxpLIziPgrQIUh56SMCyx5WVC21BbakONTMUJx3dM1gpJWRjvkQVhWsbUXN6mdFx3F5vJWDvCOmCwBjvC2oB5CZDdxZNK
W8Ay/208FNCUmepMzKGvLPJ5cSL+sU58pv3uzVQKRUdXe7VOrDUVeIvajhY44MzwYNcIfvBVBcDMbjH/fqQhow480I4ihzZewxgt
xL7AVpAHdhqbkHHrsBA3kdZtEJfgWSVyTOMfC0FBPpQ9EPaxioI7iCGGofo5c9OUbplOFvAggp/3BAi9CyFM7DVYEQcDnVaZQJJd
OUzjMeHeE25tljvxN0ELzCuylG9CJEEf82pxoTGU94vsJZKua9CWgYhcY0RXNSNgGkGfflE74oaKvIZXuxatnUD5wz3cQlGvNwB2
yT1PPuhLXH6wJdIQRIsVmQhtJzkgQIw6c2C9cIc4JIDghknEgyfcLYgdlTBhHu8z7PBqMUNHMURnMts65AYeIAEOiC+/UKZVv00W
O4IpAdIusE2hCg4FKsTnHh5um3QMkAFmmOeDwNyMUj6woMFUeV+ROwIG01EvIblL4VCQQpd9HUn0qNPOjParHhLCBrEkkBZS3A4W
BlWTONgiZlqsRxDOB/WXDz2Y5TJh9L9gttBg1HAS0vhxMFt2JubWxAa9WULMdGfJT4gZHJ+bCjMCNXFklNIzELfIwiA1m3YSqkI8
ZOjwEAdewYG7+TS5Q2pk3Jh3Y6Gg4pMeY7bkHNlHwpxk6nMSmA8W0hThJAoqj7QXy9ky9hVln7D9eZjFOPK5DSoB6qyHQl1k8hEI
SnWoFHgArw+ir90HPzaZqPgMezlVk4hyWHX00oluArlBnWJqVMDKgWrmUThleg4nn+fXpycF/t7fcY7GE+5/E76nJExekCrjL/8T
e1ig30X2OJ/6sWltpGpkUVBm9XPkcn7Gv0VXh6y1KLBVNqgCTFnkqFgiTZGQskzozVPPijvUxXyevHKpvr1yohtHHCJO9Q7d2d6V
PJsCissnXPmqg1T8V1jXb5v1p9geRtIALXpr/30q5EB7+IFUI0t0iiXqDciP3GwY1iJ+EQaaIVuauYUSYULbaol/wQDFeogUBVPP
biNolSCY+iYwwa4xEW25MPH6AhDZWD53U2B5o/GGiQk5MsszGe3rtD3QuXhLL0qUOrbCv+BgavWtAs8vwXsYQqzYSYwaHHO9Ponw
e6GD2ART92PnEG/+PiwlHCm45LEAP28Yzl7MFotxR2YTQ/y4qDEW/hHPnH7/XXgTxS/U84xQkmBVkGxKBUwhHOWhgcTFGGZC7XAx
FV99BZ8JWSXMXE2f8UuhtrGNQmIjheDqdHy7o2lEpaso16VzYSkwC0vVGqokh7O8z3i8anBLQh0TCdPPdjZd8uTcCiYoLmwUZqix
BIE3SZIpYQpvVxAtVcKmEsrxLRXylOQ71OcKPGM/YkJDw+zc1Ndj0wDOmb5m+V+INZZKVTK8AZMMP6/kQ8+lSuSFa2OjoX0tdyBl
KpUqJFR1aC1A/+DTkiBLsWDm3aBWieyhqE+VmBbtZjhP1qtYSu9kcYbnfQ7ndQmIR3FF41XZrrT4OkJY4HENgRxGghHQtzpFLYE/
bwdz2bmbf97N0AGrSanpw426h6p4wOsf7X51pKDwAwUm5BDisHx4IjMdB0WgNNpm/Px5Yty4TEzgNaKGMxV8OAgr3Oiy5ir2tuk4
6AuNvr4Gi6YmmZsuyaBMLzBjY22xn6EbbQI3q7BynmfZF5o8y7TCfRdw9XgqmFp9a0hBcA38LDNoCqEMKsOBGF+SNbeWA//CMmt/
ITzsCNAxlv+FZ+lJhzQ//3XBxRYiM3n8Eb/gnusNvDPRzM7WYmxRZFPyxUR+eZh+B3M9GWwZMMJcSPMbEOTYvUNCqkEh70LLmC+c
lHdzzRH6bwN3KZQ5nzhvtNqvjxn294JdIoKH6oVttjRs/HXtp/0JmJ0K+RplhKGD8UOp4Ga8qfgrh9yTZc2pwl9k01I1W94LHAfT
MF+xlbBhCY+C52vcISxOP47koUVxi8+Rm9Ibd7TzdejJRUDIoUsX6EcM8JRAxv1thJxawtsIqAEk5KFlyBBPT0t5VFn5LzGJxEaG
wXQBgolWVXpQr/MnpcJftfco/hHcAhly/aneUc9lV2ah/GkvckhCCF29E6W0f/6/gfVSL2olVy9lfQGuKHrMlo3/yxK1erhEXgxx
ZX8sP9OR2pcdqX3VkWL56458hVoVWhw0QERoLDNM/HqQleDxMSVIGrjGmW1rl4BxBd4W0jF6UnFRDjZ5AOcCd6qEcMG/8QtIEzKV
I+QzwAb5fVCuLKIS42gIvc79fQerDWTLkgX583OBfxMxJqxlUu8K1eC+5iQKJT16i7qV7Wt+YpxFJQsvW+Yl2A4Qtq2TxGWtsMVn
SXIJSqR4a0uRbpnJkGoBhDPByhBrdfmVqY51mOnfaKxdii4JCt0/4yPEBkV4w5TjWNfhCQ4qBluXy5tGmqcQCDJOkuFTgnn4elOQ
HZLBQpWMTtjOMQMLk3M3DjYgR7lXLr0ST46fXXvnGfzWNGhPwyv9NotYyfz8aNMNThl2tRuFBKgYJ6B+BpzQ0uzsy90xTD7Dy0/+
RP2ggOEBXS0Y3GH6fscQQ6Ja7FgXtTM6bw1cD7XDQUcETrg+Zd/aDXJAI/v5Iw6WlmWH0wvqRoEdXyR0thg9zEiwU/788UYcWWNN
0/k2s6Inq2ZJhPovtpu7s0CG8+Rp+CuZ0ZMH+jNG9SRL8dfyh2PO0VsPnQ8kJm+WCpSH0GPvsNPX2PpSjGcDJYG14qVopA/LRF8u
bAgd1Q6XMLIKZYD8TUhjw4f4SvQbRE6GuIxntZxy+ABXlHWGJstdEalMWiuv9k3gGggrVP0R9aSoJRWWSmHTNYAeIH1QCcFkUEFX
0XhCHcfP+4cermR0/T3Uaz+fadhvGD2UGSmMVGQPN9VbkzHKCTvgUnjuWvgDJzFu3MM+0vrgZK/5VMMCBCc+Wgf0W5VsfTDCP74J
y6TASHpzWEj2HlaEb2H9j+IbGVTfqIRbVirFm6dkVQx+fSv8sPYZgo/nw2g7qySBT8ot44INaLshgChflGk/fmWPHKDf2CG5kWGu
U0Q6Jkm4Sm0cAJT/JhRjWcWmsKiwdkc7NIjbcz4VGRMJtuu+ICNp4Mw2eDFZknwF63NYQZEKP6BZ8LCIv3A9D8v0Mp8ga3EysUUC
YvSUnTSwz/UvTkXiRLJcDItm+d3PJmjnIc1yNxrOM31M2HKJjKCUxKIZIwgZav/ajKBUAkk97SVwxTX1cKSed7nAn/+X/2sDHyi7
99HhOXktH6hdcI2XX2o6u3STGU1TJGClmFyeZBb9u+SV9e8z/tsHB7otIXdieWP29tzrdIPPKHh6bmlpDBw2HO4jjLepW64zPsqx
lhH2xgd5tDFnockuUNimHSBW143nrPDPDMA/o+E3FKZ8FKzBw5UF25xb5JukL7SMm/GcS8J83yBI1o1/pmwH6r4w1vA6d8zxKfOL
CSkrDBBHDIeWsXcqSxQTCKJFmupOgxtkHgrCQnNzSJ4hz8/sh2bgz8h85TFpYizrIu9fQpKBeIa2pAjVcBVscKjiJcvaaJ0W/wSP
XkcLUzHTicIMVdg1EpcYC5sDvuzuivPIMH+C0O2WPXMRij/02gt1wI0Z49A3JhnchGyBWXUvSJ6SX5sg2/AxvP1ZPcwYQB+2BNXt
FixNdSk05pvwdcg0zyW5n4ll8dw1CRxvKlI9mvCQWmFp5iMJRvF3wAQSSM8YufbC9gPL3Eulw8jrVaUbT/wcVNGMh6CeAHTKH5n2
80SGyww1lIh50GAUAPyKZ1v0tHH65qnk/hfyRP7P/yXDfxJSQrIpyQSfmMhaUyeqpZhebpQ//+v/SGUS8lC+Al6D/m7IiVkqX3mY
fuI7bTZ2X0RGBQLPK0/EHDpY8SK++FqgMFQI1310T6U8IOH3sNXQ6XWavTfnugqzx7cx46L0Ma6TBYuLMXhZR3OAHKT4zqWcSamE
YmwvLCw1PRh/S/2Sp3+poMkwOe3GjBL2LjVLHQyIV2AYvy6vKcUaYwQaGk2ClH/FOYMW9OUgXqJhdMgY77SYo3GauDvl30BQmJMN
6EHKy1OIF04RRmE0mzDEFHF4yUY5/yvUCMCmlHOYeCOdwuvnNXnGkrNCwRRQ4BPH0g8s02FXYTOHWvjEjn4oWotlkIPWZDHDznoQ
F2WMiHExLPtXIVMMf/LePQ07kCs8+8MkD/lsmeV5oGxLu5Eqv7lgyi//KbsWoexei1B2N2LQIBTP2uWiFGKCpWH+U6AoquKkN5gt
sazswKYZAFbZ6f1D0BZnpu3sR+MGfjZ95KuN1jZ2BVZC3jj+Onn/u7cWy9E9pSzZFj2RjaVsp90RZITgvskIE2080eHHcSaaMsVL
yb6BQDwYfsvH4LFbqEiaT8E2wLTI6moOyBdRKjhhGnpH28usYqmyowKxkscqtwRihINpfUsZH6l4SwOg7unU78eY2dC4xbOjQ+kP
N3n5K+yimba5knR4Y+K0+xVmC9hNX7TSVXUVMDjYjo5bRt5Y79RcDHT1kFUP1hua87lmbqx3Yy5s9XGiqrpfhW/rL/p4WMIaOmz9
oSxgMqxg3TSIMgeS+BWI8hcgDmMgEO85jGt15CTV94zTaY/NHgrbAHUR5XaEdLAVUn+eBAY3GZkIDzAcbnPtU/PD2Fr/cHv9W0sz
re0dKG8F0FZXzvYObK/fBMI6V5MgMKGfHYCLXjZP+h5nzqFEztGtTFUY9dmQmdcLAuHhmTEnA6YnJcANij4JtC8w0it1TZTA3zSO
HJJAvQrAPB3QVPR06vEGxNprUMdfMQtK59GtykYaHSdP0BlKzevtDwwU8r/IisJSeoNKH8jrHZE+UsB3oY8aJccCrm+YKVJA6aGK
x5MsLx6FLVCOWE9tRrGEXVpPWlc20MS1iQwdiCB6fNAF9ji5C4y9oZB6jHuhnO5IZwTVddtUdE3JbiIOTVRykrCI6XwgxX+6CnjC
hMsjPO8iV6hArY0Fi35BlmeSxKxYFgyegzyGjZqFcr2v2vksMJLCA0/Sooq80OvcdhuC5gpyIDSRjAc6Ozo7xDV/L3/IRLVmZugg
zE32YLBIaBCbf/MED+aBhSdVgYeh+O11lKHHJBTZ5aARBdNV+GN2ApnbCDR7htcYDNNJiWtQYeXlnLg8Huyhw4tZpumsKOOq+4T8
HtMihZgfCrUEC67fCNZeU9kJ/FR2lJISZ4iuRktMomnDWtgTd758awlzZuLdzSS/najIjCJzgKk+ENwHHyMa7uwJH0Q1H7uYxJPh
jhLBhNtdJfRlTRMceeh2DduN76axas5UwJp06tfh6tfhAf1PeeURM1kAO0bcit7HdcjvL7j7EvZOsiKFpAzj7o2gFpXKCleyJZ+C
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
