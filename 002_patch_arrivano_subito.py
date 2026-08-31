# 002_patch_arrivano_subito.py
#
# LE PATCH ARRIVANO SUBITO. Due difetti dell'aggiornamento, tutti e due risolti qui.
#
# 1) LA CACHE DI GITHUB. I file si scaricano da raw.githubusercontent.com/.../main/,
#    che risponde con "Cache-Control: max-age=300": per CINQUE MINUTI dopo che hai
#    pubblicato, il CDN continua a consegnare la versione VECCHIA. Risultato:
#    chiudi e riapri KaraDom dieci volte e sembra che la patch non arrivi mai.
#    Rimedio: si chiede prima all'API di GitHub qual e' l'ultimo commit (quella ha
#    solo 60 secondi di cache) e si scarica dall'indirizzo per-SHA, che cambia a
#    ogni pubblicazione ed e' quindi sempre fresco.
#    (Aggiungere ?t=... NON funziona: raw ignora la query string - provato.)
#
# 2) DUE RIAVVII invece di uno. Le patch venivano applicate solo all'avvio, ma il
#    download parte 8 secondi DOPO: quella scaricata oggi serviva domani.
#    Rimedio: una patch appena scaricata viene applicata subito.
#    ⚠️ Solo se all'avvio non c'era. Una patch gia' attiva NON si riesegue: avvolge
#    la funzione che trova, quindi la seconda volta avvolgerebbe se stessa (nel
#    caso peggiore ricorsione infinita). Le patch CAMBIATE aspettano il riavvio,
#    dove si riparte dal codice pulito.

import json
import os
import urllib.request

import moduli.updater as up

API = "https://api.github.com/repos/lembodomenico/karadom-patches/commits/main"
RAW = "https://raw.githubusercontent.com/lembodomenico/karadom-patches"
INTESTAZIONI = {"User-Agent": "KaraDom Pro Updater",
                "Cache-Control": "no-cache", "Pragma": "no-cache"}


def _base_patches():
    """L'indirizzo dell'ULTIMA versione pubblicata, che la cache non puo' falsare."""
    try:
        req = urllib.request.Request(
            API, headers=dict(INTESTAZIONI, Accept="application/vnd.github+json"))
        with urllib.request.urlopen(req, timeout=10) as resp:
            sha = str(json.loads(resp.read().decode("utf-8")).get("sha") or "")
        if len(sha) >= 7:
            return RAW + "/" + sha
    except Exception as e:
        print("ℹ️ patch: SHA non ottenuto (%s), uso main" % e)
    return RAW + "/main"


def _scarica_fresco(url, timeout=30):
    try:
        req = urllib.request.Request(url, headers=INTESTAZIONI)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except Exception:
        return None


up._base_patches = _base_patches
up._scarica = _scarica_fresco


# --- l'applicazione a caldo, con la memoria di cosa e' gia' attivo -------------

def _applica_subito(percorso):
    """Esegue una patch firmata adesso. Non tocca quelle gia' attive."""
    import moduli.hotfix as hx
    nome = os.path.basename(percorso)

    applicate = getattr(hx, "APPLICATE", None)
    if applicate is None:
        # Il loader di questa build non tiene il registro: me lo faccio io, e ci
        # metto dentro tutto quello che c'era all'avvio (= gia' applicato).
        applicate = set()
        try:
            d = hx.patches_dir()
            applicate.update(f for f in os.listdir(d) if f.endswith(".py"))
            applicate.discard(nome)
        except Exception:
            pass
        hx.APPLICATE = applicate

    if nome in applicate:
        return False
    sig = percorso + ".sig"
    if not os.path.exists(sig):
        print("[HOTFIX] %s: firma mancante -> IGNORATA" % nome)
        return False
    dati = open(percorso, "rb").read()
    if not hx._verify(dati, open(sig, "rb").read()):
        print("[HOTFIX] %s: FIRMA NON VALIDA -> IGNORATA" % nome)
        return False
    ns = {"__name__": "karadom_patch_" + os.path.splitext(nome)[0], "__file__": percorso}
    exec(compile(dati, nome, "exec"), ns)
    applicate.add(nome)
    print("[HOTFIX] applicata subito: %s" % nome)
    return True


up.apply_one_hot = _applica_subito


# --- il controllo patch, rifatto ---------------------------------------------

def check_and_update_patches(parent_window=None):
    """Scarica le patch firmate (senza passare per la cache) e applica subito
    quelle nuove. Silenzioso e a prova di guaio: al minimo intoppo non tocca nulla."""
    import threading

    def _lavoro():
        try:
            if not up._is_online():
                return
            try:
                from moduli.hotfix import patches_dir, _verify
            except Exception:
                from hotfix import patches_dir, _verify
            d = patches_dir()

            base = _base_patches()
            try:
                req = urllib.request.Request(base + "/manifest.json", headers=INTESTAZIONI)
                with urllib.request.urlopen(req, timeout=15) as resp:
                    manifest = json.loads(resp.read().decode("utf-8"))
            except Exception as e:
                print("⚠️ patch: manifest non raggiungibile (%s)" % e)
                return

            elenco = [str(n) for n in (manifest.get("patches") or []) if str(n).endswith(".py")]
            attesi = set()
            nuove = []
            for nome in elenco:
                attesi.add(nome)
                attesi.add(nome + ".sig")
                try:
                    dest = os.path.join(d, nome)
                    c_era = os.path.exists(dest)
                    py = _scarica_fresco(base + "/" + nome)
                    sig = _scarica_fresco(base + "/" + nome + ".sig")
                    if py is None or sig is None:
                        continue
                    if not _verify(py, sig):
                        print("⚠️ patch %s: firma NON valida -> non salvata" % nome)
                        continue
                    if c_era and open(dest, "rb").read() == py:
                        continue                      # identica a quella in casa
                    open(dest, "wb").write(py)
                    open(dest + ".sig", "wb").write(sig)
                    print("🩹 patch aggiornata: %s" % nome)
                    if not c_era:
                        nuove.append(dest)
                    else:
                        print("   (era gia' attiva in un'altra versione: si applica al prossimo avvio)")
                except Exception as e:
                    print("⚠️ patch %s: errore (%s)" % (nome, e))

            for percorso in nuove:
                try:
                    _applica_subito(percorso)
                except Exception as e:
                    print("⚠️ patch %s: non applicata a caldo (%s)"
                          % (os.path.basename(percorso), e))

            # ritiro: via i file locali non piu' nel manifest
            try:
                for f in os.listdir(d):
                    if (f.endswith(".py") or f.endswith(".py.sig")) and f not in attesi:
                        os.remove(os.path.join(d, f))
                        print("🧹 patch rimossa (ritirata): %s" % f)
            except Exception:
                pass
        except Exception as e:
            print("⚠️ Controllo patch errore: %s" % e)

    threading.Thread(target=_lavoro, daemon=True, name="PatchUpdater").start()


up.check_and_update_patches = check_and_update_patches
print("[PATCH] updater: patch scaricate senza cache e applicate subito")
