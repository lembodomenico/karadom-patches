# 233 - mini console XR18 dentro KaraDom (bottone MIX accanto a SYN, compare col mixer collegato)
# [21-10-2026] utente: "voglio che crei dentro karadom una mini console per governare l'xr18 con questi
# comandi esatti e precisi, anche con la stessa grafica" (pagina "User 2" di X-Air Edit: 01-05, FX 2-4,
# 16, LR) + "di fianco voglio il meter che si aggiornera' a seconda del fader su cui sono posizionato"
# + "il meter mettilo a sx" + "non serve che sia enorme".
# Il modulo e' moduli/console_xr18.py, qui dentro compresso e IDENTICO (fai_patch_233.py).
# Col compilato che ha gia' moduli/console_xr18 la patch non fa niente: il bottone lo mette ui.py.
# [v2] utente: "deve arrivare a tutti i miei pc registrati": arriva a tutti, ma si accende SOLO sui
# PC con la licenza firmata del titolare (console_xr18.abilitata()); sui clienti non fa niente.

_VER = 2

_MODULO = """
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
yA0fl1V7VBU6qevRTXOnte7E5npX277Xu8tSaiZuNrvH4vX9uP0xalr90fDjmct159lVu9opvY8bj7PRtTGTSqDlthulzfZWFO7N
x7k+ft5Oi3fiQ61eu9IeZ4Obj4e7Sb15sR0Ml527wYfdEV8E6a5QKFUvBI0rDutqs8Nf93N6u782R5V5k+uvN+qFeS2On/PN+vPO
qH+MXuxqZzN7B3kweHrsNiUz+/J4AcO1r8v3W7U+t+/vjML18OJm1FSeNVW0GmK7Il1tirsGX9vMb63L6+6jctcZvyujhv4+mqq7
Qa15IxRri8aDYfc6l61thd+MrWJbSD0XreZ62b0HBC5blxc5edjvD8ynl45kjAXz5uZxUxVfWu3t7Z1Y7oDMGHZqJbMzt7hd7a5Q
fL9sNRpNZcVv1tJVsVKXxuXLarlU5FR9YNTU8c1gdd1Ub242F+/XNy/NG/3jXrBvpo+iUm60bq9a3JXay68rz3rRtrepxV133Hpc
5icrcTm5vCxXn8TebWFbBZ2gV2xNn6/Furaovqgfq+7Tjpu3rafbHG/nxPH8ZVuUV3ez3uW69Pxc6H9c3fBPo7plFLfP7+37+1t7
0CotrNXjcKXJzwVONaz+uno1qO5Kj7fNfCuXywn2xcu7tm7Jk7z4IEyr9zeXvHpp3D9d3t3drvOpxeKqINi7sp0vb1e5albO561K
/eqiIIsLNasVK9XsbiN0Bp3n4boxehjqxU65Oxkpt9r95QJk5HXdlPkdn1+0nsUL5P6FQqf4VK1Mi9r6Vspmn1PSrlyYtlLZ1PPL
rph/ebnVJsbkucpfLMWS3WkU8nLL0ouDeu6p/3An7hrN9nxzJ+Sfdr3W+GVREjcP71d2U7/vv08vq91ays5XyzK/tPLaqrSWe+W5
eJWXOuWZdtcRZtUCJ4JMrRWt94/h/UKWivMXqdhaPPVmpVIq29U6rbun64J0O7guZ2+eBwvjvdX7SNkvly3dHCkqd32zeOnfj6ZL
la/nyhZoUl09/9h+LF2IVmmeb47rknrZlCvZ+/tdCrgdZwxGA2HSn3OW/di5Gn0YavM61b7MzyuTPsgh9X3BPzw9gg6S716Jqafu
tHPZbBqdvt0v91/KI7Gm7x4eBP76Jp+yF0A2z0W7031qSbPlw2xdkK97LXX1VFMfc8uPm4exeT1rNoxVa50ajWarK66ob+ej2+7i
wRgbvfHtbbk6SmVX5Yot9XrV3LJayuXzxec+SKrGSLGHNyWrv+hI5ntHsJ9bT+8vM6s6NiqmUptlU3L/vircCdmC/fRkNMfjcsHo
5MpytnOl9Try6ilftXbXI/MhBbT+uBrLvCRPrq7K2adKzbClO5ETSu9yG/Xp2nD00B3cFOvP7fZ5giji9UbnntiHuVymSJ5cPqGv
IOQsYYhN4dgSOmMIpi1jFVT2dYMclFBDinoUPAfFP8MnhV7hpIDeTv0MDDzLQu+LqoxN2URPCzpINeGP9zMBzpk3K2k5JzxjwKGV
kTVRl+RkQgBsKGhBKlMNrLIEnnCNE3/ZcFyC1F7PFBUPobTkmGV+YQpnnv03ZlLnoaqmbC9NjRkDbrFL3RKTgiSZaeZXwZy6vcM6
WWmww8CAAyMrDT2PE7T5REevFVh1WNvvRpkwiqVoeCAhykkB6uu6yvrlLlAcTUJJ/JnChi/UKZoxBHGeTPyOc1Q0OymwrNdUVveA
Q5W/D7ZwFCxxQx8CPDkIeBIFbMkHYFgBGLjWtunN1FkWeIqrgesLH7EhfsQ2/nq94VGRkjTctTK3fncymswZRZPkTdJZdX9kCBnL
X8/kHxlJPkBa/pqiP0WG7sFW/xfm3/OhxWZ+Pyf0ZrAMUITxqpwpUJP/wfwJyS2dCGPAmR0ltNcfXpkdM15YXn8MBHU4ZAL9zP7S
wN9x4HbcyPWljV4WfwBIzjaSM3YUHjPMEioTkgoXOIAygmHImpR0iGGpBejMeH0/e8f+f7Cv3A/2zzAkWPJCCAwhQNrD5Od6mPx8
D1ZMD1Ys8t/ZY0PBbq3AIqiCrWinfHAZyFhgAay4BYgMaxwzLI3xNtgRnMZOOGaw2EL74Y6JfEMfeWRYIfoECKRA3oiyYTMN8qbo
2lm0ekfXZGdb0hO5N0lQ3/AsDNgwrZ1IJG7pYRwSmXSBvi16WiYp3jleJ0PPHskhWT7HJFXFtoGfwxwUQWOZjyUe8wIGdIUeoxHQ
AI+n52kKAM4wQ5kJnrgx5NyLsDT0V1sKOWHGI3vyDDvRZMFUmNPfoTmbSTgMPsROYtbiN1yL8esZXYYgT9CY384ZDtmBxvzO5Dgu
lge8hto4IguYSYEsza/wLmiS+/y3wONUuOhPfpNcuKNVzKB/kSYJEIwaDr1w5gH9wcYOMcdBIR7pZVR9ynPJDYtj3cCsePm0Sjg8
c8rn8KADGcgG12Llzyt+ALOYAeQCA3A73zBZBpY1BvanBAm4RY0pNpSASYpLcyWA8LZNDL5hz8jBTCZDj3qY34AO0BNOyFkavwlv
eMaUlFxKllAjIaSDz06c9YOnsOinVS7D7Y0GngWrMaeluFoADZCBAFiYeKGy1yp/uFXZacWX9lrxh1sVnVZeV07pQtGSfIZLO9Xy
7pDw3dnmiBLAjDROag5acIcshE2Sw4YeBIonjWU9RGlI41ymuDcmQofQmjklPUbq5+IbVGiD4n4DrnSgCcERtCmH2zBxeCJjcvqo
RrBE1tpBhw3asR7EhgTYCOLIWxNCJZVqprrXV+L0L8tcjpcd7oP65i8ZnuxWKdhvArpN+EL5lHwlO9H+p5gJGFVEz97/8M5EVbAs
ZugYQQ5m0Tx4UzTFfnsD0apO0oytGDoe+vsoxecZ+ph8ROJ0agWZLj4iSBRnEflLWpHTeSjNirPsL1xOInxrvxqNyCLrdbgSCRAC
mmDi/31jwlEYHA8cqLQPhp6WgwAH+mP4NLtfQ5RNcYYaay6s4XtznWyOztW0tewvn0+1+cT88slc+TJh7jFz5SuZTI7HE2KoJiw3
7JGJ8iWAkoN9qKUpRPL52MT5IxZIeK4Y7HFkjreDxMHJ5XOHFtIJ3dmPxKEBPPBQPzLdfCnN4AH14elxYSrHKMM33BTnoeG7Kw7a
QQKmSRkEmRFp/p8MUzdk0956e4oGG5Idxe7xJm8/ufBOvHYYV2Qqu91eU7SYX318pwDfgIEskcSJNLNfomt7jwOxmIn0CRO/koGK
5OAVdfDwbnL3pbeAIdWLPKXTDxOL4Nkdob6mppHFmMzEnsri2qYOfwQt+I1IhqRrTIfMLtRqDNRqkjbqipEoJTZjGaD+JsGEDCDV
IJYKwjeSLChla9lMBozEoMrqzM4gmx6W7Khl5fLYJNbEY3R231LBfgXTttaKPUsiG2G/CBKqUm+G8Zo7+8HGwv4iKGDUDqggmMP6
IMEZCJGgAMVFAHzvLVJ0Af4p0lQhoaKgqAKJa7buR/r9k4TrHfZ1ULJ6mzsqW70CoEfvc6QK0iqxDCP8U5zHFqyUFTLWpgCcKtrZ
hPDjRASSLZDIiH/9t5N9XmqF3RuBgjfcgq4u5/cOJSS6Yo/Bvql0xF5wYuYWHgR2Ha0li3FjeTOXmjepEycM7DS05GehmFqgSUPX
gEXK3po4ld0lMdIkLBKo+JzP5KILg0GykhIcHQoGEn6ZoW9J51ut+dbuNO7TbumwW795u2wNaneBxhlLtp3eks77EXaD1TUJthI6
UxN0WgkMrcFBe1Gckf0vpZk34uM1ZXE1MfVFssBVSxF7FCr4Dj+JjTI50zOIzVf+BzWj4/w8AWL6xWLg/+RkDW8sCgfS9DX3I82Q
D7z7If8jyq+iSsUebLKBE19kT3tYpJgUQXLJyUjXRwGFeF1EMkV2VXBZ0bZi9/do2t3FaX97pkNEbVFivDeXMn31CcPbKvfkUxLk
xlS2z53WiiivFPSqywtdO6ftUcSfJzCQ+dSJaj41QcJQkRMUcUdBYyy58kaH+hn4ufDT4An5vdkYx/85/I8Y8M5qEGT5PDcANqpE
fWN6JARcj2iQZ2DyMhK5RAR23xIj5BXNUuSFjG4sYGMY1C5oOr2YgAc55KgpADdJrqdgLBlXTDv+EUmh12dkensGoIvCCqCwGWaI
910UWaIxuSSmfaWrtpBm6O2LnSLYcjoA370fQRuRKzP0/hQG8crfnSh9mNhEwTtE38lz8Tt8IIjIhDzTU8UkN2xMQZvKSZ6LaB5k
oBpuvVfBP5iJCCpP05PxWIVRLCKDfkRZiabbHjz04OHdD5fo9/cbXdDQY69/B8p+I6eXI2APgPYlGd5ISAr7Hmrc1BlLlWUDHTFc
IVwjVAplvoihUiNCfPsS7AsCOx0S8wF2EpL4uBh/NBv0ZkexRcXn/hGfM2qiruxzv5PIoiUtImoUg41z6gZrh88FQ4rCK47iB/FJ
wILgSxJPt7hMMVQfFe2ADnJA6BA1yIOIvQbd0fFKTipoJR8X40GEHZHkX1DBfVMTlZDAasAzYana50ghAbQenX7QMCUYoPs6CC9A
3wHBECVyemJ8YC8GNlvCvbmUYA9XoRomMUDdq0mR6sgd3gKsrMT+g/lDaI8Xgzigcvfn5h/cE1FOabk8dH98Y5Cd88+3977qVyoW
88XY3e5oqY7Wsg8LxK6taAEl5GucYn+kn+mauDTmF/un9Ih7B4CaUUj0GPo8SCyEuZD6hMsETuXpvk4z4y1YqzFEs0D/e+TwzWnE
xlHYIp6qAoZSes9qWqSDHOtrKHA4IZlPkN397rPDwNbFI4b9gX3KCH+SGR5giNR5I4wVVQEwQtI/uoy/FE4MNu+2oUAUF9AzQE2T
FcYQYYdOyZVaW0lkmFvBuxyOtwJALXN2psL06vSWpWLrKkA6w9uY5NASjzHhXdsJTLM9uMPLt6CikSvkOraiOhxeb52ST+R+FDXD
RWExVogCSJrD3jJkk0CcKOZCAI2uBhqdquD9UBp1BEoXIOKu/UQ1MWgAY4k/DcWtymTI0IBCp4xzW0/VBemNPvVpAE9CggVJEicR
sJPdIykMApEIKXzHyXxPM9+/s2zU15Xel2x+OwcPB5qyuNeS30FrBlkg6lhLlRdj/Tv7tUNFx4gnRILeWOENoXs00u6RVSQ6+pmr
8NL7MXinA8Oq3Du8DiEAZ1BhiAuyBv5tf+TTAJ2GgBHoKx2IYbpUJIFJQjeWoBLNOQurQo0D9TvIO7zRRnRyKLBA87Tc2yJ4LQU2
MXtsMTGyhng4nbW8dL77Gg3qR0n3MeL7jTpdEe3+NVTACUU/rjK8uYsQipkxYmW5o2wdXgfPuI0Zv7icTBThjSLJmQNYJiLmYCAD
i65mqDDJ/lSgwx/vFqRXxHUm2Wvf/vEhd3i17v6tXqtfNagPixL520RHT+sGg9hU6ZzQv0PvBOl4d91BdRvvNjWhOik1Ns5hcIk6
a019iVEoG9dni5aBB9c7G52jWhQYyh72A2Wvc8rVYbuT6KzXhGAqgjqWMraNUUGJGn5lLgC+++RWGcvIi3VtCHvjNFh0Kb8LD8vw
4z3DEMdKj1GczkJdHehlIE+XwNP3O6J9sA6vBtMcL72D/apbGQPjLd51RQP9OyNrK7B9NcLfEo/tzmV7AIDMRP3sL49g2+prCx1s
CUQ9ftrjjons0jKz1gx4eRaX08ra5lK2t4acVb2hEoX1YD0JBr1aJr4C+/6+GQsr0JVz9hF0AU9IpAwsPq7mWcjwF/Gxi5+ITUH0
tAC2xHT0XFCZeDXkDYhiK2nEaBexqqk7SI+wMy4+kmABGRs2tsW+Nvk1LXTPdQcjn4Sr+aCxbF/13pvFgdEjjokiGZzD8RGGIRFh
7phYDt8Mb0wMjwmet0yAndDDhkvK1TyReekkwkDFSQgIRsZNc2ExSR5PGJj4K/JUosUfXrARCRFlVhEvhygYnDvNjG7IWlLRMxeo
a7e7SZrsIDMuFZxwPzcLCCgZMGS8HJtMDFoXtQS7D9ZyWKrnaxEMx/qlOUJAzf7yWAnjdJtRrgpqep4Nidc5MVFcBxgZQuRUcOGa
dWTaMAVjG1HnCQdXFmSxk/sW7Na3YKGSpexkdLvv07UXuBWuy8XVJRSTZqYgFdLk8NjYvIKI2Mar7zDPpFOb6nXk4i5H7+5SKyq+
Czo7Chk6cfK0pJikEImmWKeZGUUCjjnGkYOIpeQOdTCzzE5OJlHq8UGpt2Z+hQVmgUnvFc2cohi2Hf+PUudtrVN/6Q73WB0ef/gj
QwurwB3wGZEaGUM3kpq8sZMKWHjBpiwbGwDgzjhwkEVOTunFZaqRCioJpyQqr+Qlp9HcVFBUJ9XRIwu8BDMUkTwPJDDP2yH0ONY5
7gKbUwIQsF7iFszPNMkp5G4BXy+BXXROIs4wewSJ+yTupLQziJDycnCfpenbpSmsT4LMz1WEcL2CSgvhyxgOCCoD4HE81jdJcief
JSPFVucTv6pDUePxa+4Hc4rvxKAfv+adr3w4JNSdCSHnNayn/wQG4j2NLDJNjQLbDfed34JmmsH8ODRXkKgrVHsigbJKxFG8MDxm
qMlrh7mlGaDmFFPAaWBEc9pLQLAfMeAhMoMvSQDIEhwlkzl/6jl32kF8wbuiquf+xsSdHYGurR0F09lPIcSwcXOBV2+Pamt/Bse2
1CIjqMYM0+ws8Pa9LeM00AcKPYqEGGD8MJQsk2PpOMSt8zRJ4ZMilj3mKUZG6wFbkxhBJ7ULqpqBkmwgoktycLnxcel1PcOanyI2
4BiEAbn+WNhpG1jMLfxtALVb+LOcZnQ36Usb97fzba1I9uycD51XuaL7N4ZnlpqbhEt3srrwKFlWYH+vBDfHHSaxcvKxkMwUIMN3
CrV88AhpIqO7IjBzUxZtkCaqnHzdcHRHbp13pAj32YZ38ME7rNettPULfsQzXjJffPHn67zH16do2Of8+Nhl8T66CX+M4Jui2wqo
BAbwSmRoAdzOXJpHNkcqEOCfoCZIFS5W3Mcpj1jwtHufOgiLJ/fVnEVEBwfxNCUxP4gO+PGTg+gJErzi5wdhvSljkzA/j1IZ1nBn
/6ZIm7BSJNIwEzvpV0D3AodXvAJRkjZUQcWBJBF5hUa/MJUAR3XHiRuOXNupIBCEHYz5QP+EWzPmMIBsliPbJBnPDgEqdPQn7BPZ
Nv18SDof6cOlRzJVdwPmwn05SLLJ+RJihHbuKIU4wApLuUsyhxlp3Bf2s7jJz+ZOejs4Fj9ZjVuILAELgChPASgLr/41FirxSTEH
hLrhWUrBuI9T0C0bYoi+lOYLlMLxjD0geuOFNCU7R06DVA5SgStwyU7JMlymRNcuAf9RW1V2nVtRAWybumHoRLLqTkJPqAnY089I
hkKS/SVNVR+SJCfrpckJHx+kyfXHYFduVCAD0phn6XkElIrAcchTogzzdHmp0iYpK0VSiKs45uSK6lohLQtj4zOgTAuYxsjblLYb
6WFRHeuLsFIU1viLsA5QXgxkd/H4whGwNNYVDwUUcSHbM13yjUUHL3YkutLex7Q/vIVMru1iWLJcJaI1EShFa0cJnO2lnYuBEfpw
VhUAU7+F8XqmoKAOPFDOIoc2Xsd4s4J+ga0gjK0kdiHg1qHXgViybuN9DZ42ImFNzsdcUJEPZVqDfSyj4g5qiKbJfn7RJElNS04W
8CDCOe8JMHoXQpjZK7AiNl4K2aQDCUmFMI/H5GRPuLVpnrlfGSWAVxQp50wkmRkN6HChUZL3q5zEsq5bsJaBidzi7ZdymsGUaz7/
Iv2wBxo6LbzWlWjrGM4fHuERjnp7ALDL7p1Ebb7G5V9MQx6CZLEhLkLLjg+eZqNxDNguPCAHEkBwQ8r3A83dLYgD5TG5mDNm2OHl
fJocxRA+kz42IDdIGxlwQH35RrJS+n3SOHu8Pp10gR0K67ZJUPc+7uHhMaTjZQIQhpwzCcxjx3OBBQ2mFfuM3RFggI5qAdldAqeC
HLro20isx52+LGg/GyEh2CCVBFLoscfBwqQqvAM2j1npqhGC80H9/VMPZgSMmf03zKwYvGEZRzT+nYEjOxPzEGKHHpaQMl0s+ckD
g/Nz0wZGoMbOjKQ/DNzxolfGFIvsJDSFnOsVp6c48RJO3M09mGZc90Rw3pijYCmi4ZOcYmbZLPGPhCXJ3JckgA96/SMiSUQ0Hsle
LGaKOFbUfcL+ZymDd24NC0wCtFlPmSpL9SNQlKrQKPAAilPRYvfBj0MuKgfDXv7JOKYcNh291IuHQB4wp6gZFfByoJl5Fk4vnUXk
O7nIyZOcU+7vOFtxkpOfM68JHi96J4r44n+iD3PkNU8fc4kfh9aGL0cWBXVWP5+oI8+cb9HVId5aVNhKB0wBaiw6pFggliIhyiIh
bydNJ/uFtpj70GlcqB5vHBvGsQ8RUf2F4RwfCkdRQO4wE1r5bICk+i+wrueH7ae9PYysAXr01v51zmTBeviBXCND+BRNahrQHx23
YdiK+MaMFU0wFf0IJ8Lkn+WC8wUvc1VDrCiYpvMYQysFwVQPgQkOjapoq6WOqd5BZaO5r3WG5tjFbPwzEsMrLAT0r5PtgXG1R0ZR
IGk2S84XnEylelTh+RbMWR8SxXbsDaupY9fHMX7vmhV2Qc39vXOId38fFmKOFFz2mIO/d7z6m8/k8/sxvDrmPXdUjSnzL3jm9Ntv
zDvLfmKep5kCD6uCbJPPYbrVqAwNJHnFSwqkH0dNxaLP4FMlq4BZfsln/JKrHOwjF9tJLrg6Xd/vqGtR7Soqdcm5MB/Awko2JZno
4TRHLh6vao4noYpJV8nfcTFd8PTcEiZzzR1UZkhnMQpvnCZTwHTHriJaKIVdJSQfMp/jSELk0JhL8Iz+sTEdSRlDV7dTXQPJmbyl
uTKIaCwUysTxBkIy/LzEhZ7zpUiB62MjU/tc70DOVCiUiFLVJWsB9oeDlhhdil78/BrUMmF7qOqTRtSKdrNBx9tVNP1xvDrj5MgN
58AIqEf7hsabeNxo8W2EsMLjOgIdGDFOQN/rFPUE/rwfzBXnbq5uN5sBrCZJ4x3u1D1UxQNe/2j3syMF0TlQoEoOIRyaO4ylruOg
CpRE34yfa4zddy4TIfAWMcOpCS6NwwY3hqy5hr2l2zaGAYOuJOAtRMHJMEx+UIBkxQCMTZXl9zT59Y/Ar1DQel5k2SeWPM1K4cQu
4Oo5aTMq1aPR9ME18DNyoCuEZJuQxuz+kmwdbznIL6yz9RfCo44AH6O5MpyMJsmQ5ecX51xqIWyGwz/2E+m5PSA7Y93sdC2mJrnU
E/8jLt5Cu/nz30ijfee653BxfgIjzRgK/j7LYRqI7/DsUDr+NP2dDhKzKGMgo7wLnJInqXPOZS+UgDCT9Z/JOMhlnjH5nRggNdgJ
9Ocz1O9djQ3R0p7fGcUHcQgHcv1/wRMTgRNuT1IpfA1yQGT8vA+G3jr+gnuFDCNH/Ssxg81HvS0xhtTP+1/2BcZe18QBT838eNkR
Jx7+bsPexQKx7OPR8A+y8+Mn+jNWf5wp+7kjwNYNDCfA0xGSlQb1O5JUxtNBYKdvsfcVu5/aCbnbacnLt0M+rGIPm7EjPEk/XcHM
SiSdz69MEjs+xSLW73AsmIQ1ojPZ4Rw+wA25VE2Q5a4IXyRi1Wl2zjgsklYq/4ge9VTiKvOFsG0NoMfIH2RCYALIyE30woOK83fG
hyE4xCr8LTRqPzlVOLAJQ6goK4w0pA8PtdsSbdkORwiRqzNb5ndE4r71gWMk64PI3jqohgUIIj7aBgSwTIwRmOHv58wq7uYGKTnN
xYc3icx5WECRCxgUqq/14pblC/vdk1wMFH71KPyweAzBRwc2KvelOPBxV6ddsAFxHAKItlWR7MfPDKYxHmyfknNuTFyFREdEsCd1
9wFA/XMmv5c0Yw6LCmt39oUOcXsac5YKkWC/bgGx4gJO5eCvTIRdfitXMT0F/J2ip/cU7ZbTPL7gep4WSSEX43Jy2MQR3wvlp9QV
Qj9XP3Hb7DPJItVpUPSsWHQbf915QnYe8ix3oyGeyceYLRcrCApxIpoKgpAl+Y8WBGDwgZLuZePCNfVopMq5UuBv/+W/H5ADRffH
RdCRX+ECrXOudXVMSnx5mNSqSxAFC83FXDrWbvunJAnzf5zuj7+94PaE0one6XZuchmmksRbTFrobqn722JzcszJCBZ8PHGDBDxg
7r2xUFw1CQsIagAkBi+zxsQPb06IeWRvrjOSjD8Gp0y2SfbP8BVYrE0/TXRxab3Bxhejt+kcsb3+6oUYwj5p7LQzYScwOzAbDHvB
kQZDs+kDNzzbgXAwG8w+Ko+iMz4q/Wu3jWhOXIsE63x+58hJ5QPW6V4Ony/m4HC6ijSP5pshvdCclpH8TvgaOHsMZMeJ5Ni1/Mhs
9xfswsLHa0rSK/v5C6IJZ0B9BugkfU/ST9MTriMpqLE5UfdRAPCyn+zGsxbJN89k9L+QUJ5//be08xeTkYeiJB18oiPrT9RlU6S/
PouD/ttf/2ciHZMG6A2oFexLTYhNEvTm3HOLLVMWU7cgMisQyG9O1reQZ8ILmXbWAoV1Ltz20XXreEDC5bCBMGpknrnXDVUG7Lkb
kHB58nHfZghWZ/fgZWzFho2ccPYjuW+fiKlG98LSlJPj6XniG0f+BSvijQY++CN03/zLq3jJk1xgRfvdlJ1f0ku77gdi75Pf21UW
C/yNYTmBmUX4M35/HFMZKsNOBxEpbWhWQOLScvD3KwzEcWORn7gj39mY+SwwhclODrflMpVwY3wQaSyu6BLUBW0lWEkXINhWAbyk
mZkynanwZ9szRZxjhvtzEMhj6Zzbg0dTmhNtIgHqOmYdkzcGYCai1DiEJ3m+v1VGNGWwWYAYhanseCIwBEw3zxPaOrHf0xh2bzLx
2wVmPdF6GCN/yv/uZsJ7M0x5oRxuxJ/e6cjO/AaLpb5SPullIKsyEHKwHxU3nXCw3aW+HKvyKW0ebCfphqHoB9vd6UtLfpzJsuo3
MXW8zSV8MsbTArZQhcVYEhgg2FDbpIw/CMx+BqL4CYhTPo4MHRi38sSOa+85x5IeGz1ljgEaIMl9EVLqKKSREQeG/N4yav8pjBc+
3PpSX2tH258eb98zFd08PoDiUQAdeWMfH8Dx9g1LFAw5BoKb9CymqQHLrYu6mkw83oFYvwV1+Q2vUXYfXXqkjaNb2kluE0pr5VyC
cdKxRVvgWWqSPZDkDYX+UnPSSzFJ1b/ljQeYsi0zxlL/zkhLE1MJfCwFlQSNkt9iD8TXvQVzwUUz9fyd0jfkbFKFlW4KUR2W3P32
r7xHrWUoRj3YVUsy7iCVuNuWXxjqLxb+0PkvFhEkHlTUsTFNDxtJNvZJTrZAV+i6SBCNiaQ4cC/PJ3+xWOZvf/0Phvw++sdSIdf0
TYX8xrIp4yhghmSeX7qnRe3B/X7clT7SFXtsDgQ54WxLn+lFh9KZ0WUO5TDzk5V9KSvU4WyNhAKiWQj3cwy5G5T4CvTg/cMvZvOM
sW98eiYb0NFLFMHfP+Tcai8Fjn+ZyJUj1KIjZ8JBtjI7VHMmI5NPxoTdkpToReqixUs8VLFJk5sXqNEET+9Amq7cixJBE8tLw+OM
P+CSTRPnj5zBZPkWtMps8UPop0tQdyI3hZ4wjXuWKr+hQEkOD+EUxw8a1odxY2+gJKwCx+dvwDCFUyYZPvuD7bqNS6NA4ie2IXaJ
WZSUwFqFxCP+GspZnAVDMEzxuz984pRTooIhslv8Lsl5hNtdJKW47eVCosBflR+hMw56RLufAl8jh5M8l8uTDP3wHs09ijvGyVFm
xydL9tLof3EenkR1DoBl1RaOzsXFZ3hK3ui+cnbjno7sH/hHTnOlcVxyfP94OO5AmLShznRyQw6znPzOOL630+peOtfASuK00pFj
Y945N8afFCK4cU95Ux5sz7NHf/XARy0q5D+1RwGysy1hH+W5vQzNYRYPGCRM9eDN3T31Iy79HEzOYQ2umg6MRQ5nYfnSYkU11aCi
dGxHQAcVwla2+MLzHOEkOfwibfC1WNg/0eI8dHw94ts5Q4rJyebtqs+ArCI/hlXI57yRF0q5vZGXvjLyA9FUXxhubMvoGPlS0R8j
V4xE2Pzs3v08aMcJ9PEua5/h3UzPVUPTiyqguoJWjrQGyBXSNB+VgPsJA0yo9okG4QHSDnh+kgqRZT/P+Yj5G7M9Qzn13I7OPtlD
eMlN47xN5Db7wp4HvURn6O+WkFQFMtngMvMvDLfhOM6jg7Bz5k5QlpZILz6gZhPL0xQyplOEiYddW/LbLHhDjcS/gKjBvoMci5r2
cSwr1t8W1EbQto9D5lfZS8hPfpRkIzP02TVHTMJAFkPHfHdGRSLiLH3PKf3PYIB4Voqdx8OhRXgZjwiAqMyK+NF8kQ3aIiwiaR20
Jp2MUGkauFvgmIXlI4XYnhGtNkTxqK4fnWa8gv5GexWOaOfo8Jc3ER3dRJ0z8SoGHJg/3BmcOZadvPmKeSBMMLwJzz59K/vvyzr6
5gREO5SDAVJAbYD0AM4WQcbp5JEniRqxHmy2SNmbjdfcYb1o0MOP4z+vNwedUtqEIxuAMRNQceEdr1CbRChgK6qbL9jgb26Fww9n
irCSye/NUWafZuZshCDRga97/mzq6ifygTZOO3DZ2FCTVdqDAFp1JsfGGr/f0LEhSEug9X/PY+Rg1oo7kqaRG7RbtNzCgQ6YYclT
Lui5Q9wwIwcToSrcnnAjYQ0GxmB5ywmd/I7rF5NA2BnByiWS/Uk4QSTOHCJjCUyNgAo1D/yyxWrPYMQf3QteUqX77ysZjQLZS5yP
9/O93zmJ2rZAWMX436f76r/QYS8R+TPMWCLqJknpZC0FsIWspfkVsQl28ZVjsfqHB5Gzg0Agp0/y7r50E3qmGV/1R6DpPWdQiI07
kP50HtYuMPO4DE1s1yZMEOvX8Zyx8XzfOWeKSZ6CAwklTQlHgLjZMiOpUxDe0QxMeY49O75AOGG8gMpYk+VCgNUVoml34i5l5Cq4
0TF6CY2XXHXfORXKOME5WSUIwpNb4sqmV8ecyJcpSdc0jbtKCWTuRXtgkKfL7h9pWKYXPFMtpRn6dwgKPY+l/A+AEV8E3qPBIIzw
gRrGegcCF/ci6p1Q4XBgUthW86KFi97lh8MGXSiQvv214Tub4JQp0RnsO0/xUgiM0o/vOBB9491PTztH0AEZFPSYHDA7cWxeVLk3
POdit7v70gzJpeHvPCtmlu457N5xf0Svp1vyJCZnGYkFiOQsi9k3yiL4g78yveMTl77459FCwg+dczNXqfDVifiVjUTmU+yhXFVX
hGgAZuCypMX+lLOGDOh1T6wHVQFPakYvMBKnmauGsD/C8VqvURH8/wXSQ0Yket0Ja+Ki5KSC+DXm+8FQzkm/I+MyvZlu6+RLaNFd
eafY8sI/KndPbDFaHlqcewDZk/8HRzlhYA==
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
