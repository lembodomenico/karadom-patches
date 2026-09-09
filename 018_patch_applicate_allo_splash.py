# 018 - aggiornamenti applicati all'avvio, prima che nasca la finestra.

ATTESA_MAX = 8
NOMI_THREAD = ("PatchUpdater", "PatchAlloSplash", "PatchAllAvvio")


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_018', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def _fai_apply_all(log=None):
    import os
    import glob
    import traceback
    from moduli import hotfix as H

    _log = log or (lambda m: print(m))
    applicate = 0
    try:
        d = H.patches_dir()
        files = sorted(glob.glob(os.path.join(d, "*.py")))
        if not files:
            return 0
        for py in files:
            nome = os.path.basename(py)
            if nome in H.APPLICATE:
                continue
            sig = py + ".sig"
            try:
                if not os.path.exists(sig):
                    _log("[HOTFIX] %s: firma mancante -> IGNORATA" % nome)
                    continue
                data = open(py, "rb").read()
                if not H._verify(data, open(sig, "rb").read()):
                    _log("[HOTFIX] %s: FIRMA NON VALIDA -> IGNORATA" % nome)
                    continue
                ns = {"__name__": "karadom_patch_" + os.path.splitext(nome)[0],
                      "__file__": py}
                exec(compile(data, nome, "exec"), ns)
                verifica = getattr(H, "_esegui_apply", None)
                if callable(verifica) and not verifica(ns, nome, _log):
                    continue
                applicate += 1
                H.APPLICATE.add(nome)
                _log("[HOTFIX] applicata: %s" % nome)
            except Exception as e:
                _log("[HOTFIX] %s: errore in applicazione (%s) -> saltata" % (nome, e))
                traceback.print_exc()
    except Exception as e:
        _log("[HOTFIX] loader errore: %s" % e)
    if applicate:
        _log("[HOTFIX] %d patch applicate" % applicate)
    return applicate


def _aspetta_download(secondi=ATTESA_MAX, battito=None):
    import threading
    import time
    fine = time.time() + max(0, secondi)
    while True:
        vivi = [t for t in threading.enumerate()
                if t.is_alive() and t.name in NOMI_THREAD]
        if not vivi:
            return True
        if time.time() >= fine:
            return False
        if battito is not None:
            try:
                battito()
            except Exception:
                pass
        time.sleep(0.05)


def _apri_splash():
    """La finestrella che si vede mentre si scarica e si applica.

    Serve perche' senza di lei quei secondi sono SCHERMO NERO: lo splash della
    licenza e' gia' stato chiuso e la finestra di KaraDom deve ancora nascere.
    Torna (finestra, radice creata qui o None, etichetta dello stato).

    ⚠️ Se una radice Tk non c'e' ancora se ne crea una e la si distrugge dopo:
    e' la stessa cosa che fa lo splash della licenza, e `demo()` costruisce
    comunque la sua subito dopo.
    """
    import tkinter as tk
    radice = None
    padre = getattr(tk, '_default_root', None)
    if padre is None:
        radice = tk.Tk()
        radice.withdraw()
        padre = radice

    w = tk.Toplevel(padre)
    w.overrideredirect(True)
    w.configure(bg='#1a1a2e')
    w.attributes('-topmost', True)

    tk.Label(w, text="KaraDom", font=('Segoe UI', 26, 'bold'),
             bg='#1a1a2e', fg='#ffffff').pack(padx=60, pady=(30, 0))
    stato = tk.Label(w, text="Aggiornamenti in corso...",
                     font=('Segoe UI', 11), bg='#1a1a2e', fg='#aaaacc')
    stato.pack(padx=60, pady=(10, 30))

    w.update_idletasks()
    lw, lh = w.winfo_reqwidth(), w.winfo_reqheight()
    x = (w.winfo_screenwidth() - lw) // 2
    y = (w.winfo_screenheight() - lh) // 2
    w.geometry("%dx%d+%d+%d" % (lw, lh, x, y))
    w.update()
    return w, radice, stato


def _chiudi_splash(w, radice):
    try:
        if w is not None:
            w.destroy()
    except Exception:
        pass
    try:
        if radice is not None:
            radice.destroy()
    except Exception:
        pass


def _riassunto_patch():
    from moduli import hotfix as H
    fuori = {}
    stato = getattr(H, "STATO", None)
    if stato:
        for nome, st in stato.items():
            corto = str(nome).split("_", 1)[0] or str(nome)
            fuori[corto[:16]] = [1 if st.get("ok") else 0,
                                 str(st.get("nota") or "")[:120]]
    else:
        for nome in getattr(H, "APPLICATE", ()):
            corto = str(nome).split("_", 1)[0] or str(nome)
            fuori[corto[:16]] = [1, ""]
    return fuori


def _dillo_al_pannello():
    import json
    import threading
    import urllib.parse
    import urllib.request

    def lavora():
        try:
            from moduli.licensing import get_hardware_id, generate_serial
            cpu, mb = get_hardware_id()
            serial = generate_serial(cpu, mb) if (cpu and mb) else ""
            if not serial:
                return
            # versione.APP_VERSION per prima: updater.CURRENT_VERSION e' una
            # costante rimasta indietro ("5.3") e sovrascriverebbe nel pannello
            # la versione vera con una sbagliata.
            ver = ""
            for dove, come in (("moduli.versione", "APP_VERSION"),
                               ("moduli.ui", "APP_VERSION"),
                               ("moduli.updater", "CURRENT_VERSION")):
                try:
                    ver = str(getattr(__import__(dove, fromlist=[come]), come) or "")
                except Exception:
                    ver = ""
                if ver:
                    break
            p = json.dumps(_riassunto_patch(), ensure_ascii=False,
                           separators=(",", ":"))[:3000]
            if not p or p == "{}":
                return
            q = urllib.parse.urlencode({"serial": serial, "v": str(ver), "p": p})
            for base in ("https://karadom.it/heartbeat.php",
                         "https://www.karadom.it/heartbeat.php"):
                try:
                    req = urllib.request.Request(
                        base + "?" + q, headers={"User-Agent": "KaraDom/patch"})
                    urllib.request.urlopen(req, timeout=8).read()
                    return
                except Exception:
                    continue
        except Exception:
            pass

    threading.Thread(target=lavora, daemon=True, name="PatchStato").start()


def _fai_partire_il_download():
    """Fa partire il download ADESSO, se non e' gia' in corso.

    ⚠️ Senza questo la 018 non poteva funzionare sul programma compilato: li'
    il controllo delle patch parte con `root.after(8000, ...)`, cioe' OTTO
    SECONDI DOPO che la finestra e' gia' aperta - nel sorgente c'e' scritto
    "per il PROSSIMO avvio". Quindi qui si aspettava un thread che non era
    ancora nato: l'attesa finiva subito, non c'era niente da applicare, e la
    patch appena pubblicata entrava solo al riavvio successivo.
    """
    import threading
    vivi = [t for t in threading.enumerate()
            if t.is_alive() and t.name in NOMI_THREAD]
    if vivi:
        return                      # sta gia' scaricando: non se ne lancia un altro
    try:
        from moduli.updater import avvia_controllo_patch
        avvia_controllo_patch()     # versioni nuove: ha la sua guardia, e' innocuo
        return
    except Exception:
        pass
    try:
        from moduli import updater
        updater.check_and_update_patches()
    except Exception:
        pass


def _prima_della_finestra():
    import time

    finestra = radice = stato = None
    try:
        finestra, radice, stato = _apri_splash()
    except Exception:
        finestra = radice = stato = None

    def dillo(testo):
        """Scrive sullo splash e lo tiene vivo: senza update() la finestra
        resterebbe bianca e Windows la darebbe per bloccata."""
        try:
            if stato is not None:
                stato.config(text=testo)
            if finestra is not None:
                finestra.update()
        except Exception:
            pass

    def respira():
        try:
            if finestra is not None:
                finestra.update()
        except Exception:
            pass

    try:
        dillo("Cerco aggiornamenti...")
        try:
            _fai_partire_il_download()
        except Exception:
            pass
        try:
            _aspetta_download(ATTESA_MAX, respira)
        except Exception:
            pass

        dillo("Applico gli aggiornamenti...")
        quante = 0
        try:
            quante = _fai_apply_all() or 0
        except Exception:
            quante = 0
        if quante:
            dillo("%d aggiornamenti attivi" % quante)
            time.sleep(0.8)          # il tempo di leggerlo
    finally:
        _chiudi_splash(finestra, radice)

    try:
        _dillo_al_pannello()
    except Exception:
        pass


def apply():
    if _spenta():
        return False
    try:
        from moduli import hotfix as H
        import moduli.ui as U

        if not hasattr(H, "_orig_018_apply_all"):
            H._orig_018_apply_all = H.apply_all
        H.apply_all = _fai_apply_all

        if not hasattr(U, "_orig_018_demo"):
            if not callable(getattr(U, "demo", None)):
                return False
            U._orig_018_demo = U.demo

            def demo(startup_file=None, _orig=U._orig_018_demo):
                _prima_della_finestra()
                return _orig(startup_file)

            U.demo = demo
            try:
                import moduli as M
                if getattr(M, "demo", None) is not None:
                    M.demo = demo
            except Exception:
                pass

        return True
    except Exception:
        return False


def revert():
    try:
        from moduli import hotfix as H
        import moduli.ui as U
        fatto = False
        if hasattr(H, "_orig_018_apply_all"):
            H.apply_all = H._orig_018_apply_all
            del H._orig_018_apply_all
            fatto = True
        if hasattr(U, "_orig_018_demo"):
            U.demo = U._orig_018_demo
            try:
                import moduli as M
                M.demo = U._orig_018_demo
            except Exception:
                pass
            del U._orig_018_demo
            fatto = True
        return fatto
    except Exception:
        return False


try:
    apply()
except Exception:
    pass
