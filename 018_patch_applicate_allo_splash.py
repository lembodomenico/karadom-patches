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


BG_SPLASH = '#1a1a2e'
FG_STATO = '#cccccc'


def _scrivi(label, finestra, testo):
    try:
        if label is not None:
            label.config(text=testo)
        if finestra is not None:
            finestra.update()
    except Exception:
        pass


def _lavora(label=None, finestra=None):
    """Scarica e applica. Se c'e' lo splash, lo racconta li' dentro."""
    import time
    if _fatto.get('si'):
        return
    _fatto['si'] = True

    _scrivi(label, finestra, "Cerco aggiornamenti...")
    try:
        _fai_partire_il_download()
    except Exception:
        pass
    try:
        _aspetta_download(ATTESA_MAX, lambda: _scrivi(label, finestra,
                                                      "Cerco aggiornamenti..."))
    except Exception:
        pass

    _scrivi(label, finestra, "Applico gli aggiornamenti...")
    quante = 0
    try:
        quante = _fai_apply_all() or 0
    except Exception:
        quante = 0
    if quante:
        _scrivi(label, finestra, "%d aggiornamenti attivi" % quante)
        time.sleep(0.5)

    try:
        _dillo_al_pannello()
    except Exception:
        pass


_fatto = {'si': False}


def _aspetta_lo_splash():
    """Si mette in ascolto della riga di stato dello splash di KaraDom.

    ⛔ Niente finestra nostra: quella si vedeva sopra il programma ed e'
    sbagliata. Il messaggio va scritto DENTRO lo splash, dove l'utente lo
    sta gia' guardando.

    Si aspetta la prima `update()` della finestra che contiene quella riga:
    a quel punto lo splash e' a schermo e nessun widget del programma e'
    ancora nato, quindi anche le patch che cambiano COME nascono i widget
    fanno in tempo.
    """
    import threading
    import time
    import tkinter as tk

    orig_label = tk.Label.__init__
    orig_update = tk.Misc.update
    visto = {}

    def label_init(self, *a, **k):
        # ⛔ Si ripassa TUTTO com'e' arrivato, senza rimettere in fila i
        #    parametri: qui davanti c'e' gia' la 013, che avvolge le Label a
        #    modo suo. Passandole `cnf` come secondo posizionale si beccava
        #    "'dict' object is not callable" e KaraDom NON PARTIVA PIU'.
        orig_label(self, *a, **k)
        try:
            if 'label' not in visto and str(k.get('bg', '')) == BG_SPLASH \
                    and str(k.get('fg', '')) == FG_STATO:
                visto['label'] = self
                visto['win'] = self.winfo_toplevel()
        except Exception:
            pass

    def update(self):
        esito = orig_update(self)
        try:
            if visto.get('win') is not None and self is visto['win'] \
                    and not _fatto.get('si'):
                tk.Label.__init__ = orig_label
                tk.Misc.update = orig_update
                _lavora(visto.get('label'), visto.get('win'))
        except Exception:
            pass
        return esito

    tk.Label.__init__ = label_init
    tk.Misc.update = update

    # Rete di sicurezza: se lo splash non arriva (build diverse, avvio strano)
    # il lavoro si fa lo stesso, senza scriverlo da nessuna parte.
    def rinuncia():
        time.sleep(12)
        if not _fatto.get('si'):
            try:
                tk.Label.__init__ = orig_label
                tk.Misc.update = orig_update
            except Exception:
                pass
            _lavora()

    threading.Thread(target=rinuncia, daemon=True, name="PatchRipiego018").start()


def _prima_della_finestra():
    try:
        _aspetta_lo_splash()
    except Exception:
        try:
            _lavora()
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
