# 021 - voce nel menu Extra per cercare subito gli aggiornamenti.

import tkinter as tk

NOMI_THREAD = ("PatchUpdater", "PatchAlloSplash", "PatchAllAvvio")
ATTESA_MAX = 40


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_021', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def _elenco_locale():
    import os
    from moduli import hotfix
    d = hotfix.patches_dir()
    fuori = {}
    try:
        for f in os.listdir(d):
            if f.endswith('.py'):
                p = os.path.join(d, f)
                fuori[f] = (os.path.getsize(p), int(os.path.getmtime(p)))
    except Exception:
        pass
    return fuori


def _finestra_attesa(parent):
    f = tk.Toplevel(parent)
    f.title("Aggiornamenti")
    f.configure(bg='#1a1a2e')
    f.resizable(False, False)
    try:
        f.transient(parent)
        f.grab_set()
    except Exception:
        pass
    tk.Label(f, text="Cerco aggiornamenti...", bg='#1a1a2e', fg='#ffffff',
             font=('Arial', 13, 'bold')).pack(padx=40, pady=(24, 6))
    tk.Label(f, text="Un momento, sto guardando se c'e' qualcosa di nuovo.",
             bg='#1a1a2e', fg='#aaaaaa', font=('Arial', 10)).pack(padx=40, pady=(0, 24))
    f.update_idletasks()
    try:
        x = parent.winfo_rootx() + (parent.winfo_width() - f.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - f.winfo_height()) // 3
        f.geometry("+%d+%d" % (max(0, x), max(0, y)))
    except Exception:
        pass
    f.update()
    return f


def cerca_aggiornamenti(parent):
    import threading
    import time
    from tkinter import messagebox
    from moduli import hotfix

    attesa = None
    try:
        attesa = _finestra_attesa(parent)
    except Exception:
        pass

    prima = _elenco_locale()

    def lavora():
        errore = ''
        try:
            from moduli import updater
            updater.check_and_update_patches()
        except Exception as e:
            errore = str(e)

        # il download gira in un thread suo: qui lo si aspetta davvero
        fine = time.time() + ATTESA_MAX
        while time.time() < fine:
            vivi = [t for t in threading.enumerate()
                    if t.is_alive() and t.name in NOMI_THREAD]
            if not vivi:
                break
            time.sleep(0.15)

        dopo = _elenco_locale()
        nuove = [f for f in dopo if f not in prima]
        cambiate = [f for f in dopo if f in prima and dopo[f] != prima[f]]
        tolte = [f for f in prima if f not in dopo]

        # ⚠️ Solo le patch NUOVE si applicano a caldo: apply_one salta quelle
        #    gia' attive. Una patch CAMBIATA non si riesegue - avvolgerebbe se
        #    stessa - e vale dal riavvio.
        applicate = 0
        for f in sorted(nuove):
            try:
                import os
                if hotfix.apply_one(os.path.join(hotfix.patches_dir(), f)):
                    applicate += 1
            except Exception:
                pass

        def racconta():
            try:
                if attesa is not None:
                    attesa.grab_release()
                    attesa.destroy()
            except Exception:
                pass

            if errore and not nuove and not cambiate:
                messagebox.showwarning(
                    "Aggiornamenti",
                    "Non sono riuscito a controllare gli aggiornamenti.\n\n"
                    "Controlla la connessione a internet e riprova.\n(%s)" % errore,
                    parent=parent)
                return

            if not nuove and not cambiate and not tolte:
                messagebox.showinfo("Aggiornamenti",
                                    "KaraDom e' gia' aggiornato.\nNon c'e' niente di nuovo.",
                                    parent=parent)
                return

            righe = []
            if nuove:
                righe.append("%d nuove" % len(nuove))
            if cambiate:
                righe.append("%d aggiornate" % len(cambiate))
            if tolte:
                righe.append("%d ritirate" % len(tolte))

            testo = "Trovate novita': " + ", ".join(righe) + ".\n\n"
            if applicate:
                testo += ("%d sono gia' attive adesso.\n" % applicate)
            if cambiate or tolte or applicate < len(nuove):
                testo += "Per le altre chiudi e riapri KaraDom."
            else:
                testo += "Se qualcosa non cambia, chiudi e riapri KaraDom."
            testo += "\n\nPer vedere cosa e' attivo: menu Extra, Patch applicate."

            messagebox.showinfo("Aggiornamenti", testo, parent=parent)

        try:
            parent.after(0, racconta)
        except Exception:
            racconta()

    threading.Thread(target=lavora, daemon=True, name="CercaAggiornamenti021").start()


def _aggancia():
    """Mette 'Cerca aggiornamenti...' nel menu Extra, sotto 'Aggiorna'."""
    originale = tk.Menu.add_command
    fatto = {"si": False}

    def add_command(self, cnf={}, **kw):
        esito = originale(self, cnf, **kw)
        if fatto["si"]:
            return esito
        etichetta = str(kw.get("label") or (cnf or {}).get("label") or "")
        if etichetta.strip().lower() in ("aggiorna", "update", "actualizar",
                                         "mettre a jour", "aktualisieren"):
            try:
                originale(self, {}, label="Cerca aggiornamenti...",
                          command=lambda m=self: cerca_aggiornamenti(m.master))
                fatto["si"] = True
                # Come la 007: NON si rimette a posto tk.Menu.add_command,
                # o si spezzerebbe la catena delle altre patch.
            except Exception:
                pass
        return esito

    tk.Menu.add_command = add_command


def apply():
    if _spenta():
        return False
    try:
        if getattr(tk.Menu.add_command, '_patch021', False):
            return True
        _aggancia()
        tk.Menu.add_command._patch021 = True
        return True
    except Exception:
        return False


def revert():
    # La voce sparisce al prossimo avvio: qui non si tocca la catena dei menu.
    return False


try:
    apply()
except Exception:
    pass
