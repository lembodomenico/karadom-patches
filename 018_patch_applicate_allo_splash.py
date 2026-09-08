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


def _aspetta_download(secondi=ATTESA_MAX):
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
        time.sleep(0.05)


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


def _prima_della_finestra():
    try:
        _aspetta_download(ATTESA_MAX)
    except Exception:
        pass
    try:
        _fai_apply_all()
    except Exception:
        pass
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
