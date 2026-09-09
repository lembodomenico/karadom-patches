# 019 - responsabilita' sui dati: avviso nel tab Backup e prima del ripristino.

AVVISO_TAB = (
    "Le copie di sicurezza sono un aiuto, non un backup vero e proprio: stanno "
    "sullo stesso computer del programma e si perdono insieme a esso. La cura "
    "dei propri dati resta di chi usa KaraDom, che e' tenuto a farne copie su "
    "un altro disco o supporto.\n"
    "KaraDom e il suo staff declinano ogni responsabilita' per la perdita dei "
    "dati e per le conseguenze di un ripristino eseguito o non eseguito."
)

TESTO = (
    "RIPRISTINO DEI DATI\n\n"
    "Stai per riportare KaraDom a una copia salvata in precedenza. Tutto quello "
    "che c'e' adesso nel programma - il database dei brani, le scalette, le "
    "impostazioni - viene sostituito da quello che c'era il giorno di quella "
    "copia, e il lavoro fatto da allora in poi va perso. Il programma non ha un "
    "modo per tornare indietro da solo: prima di procedere mette da parte una "
    "copia della situazione attuale, che trovi insieme alle altre in "
    "%APPDATA%\\KaraDomPro\\backups, ma sta a te andarla a riprendere se serve.\n\n"
    "La decisione e' di chi usa il programma, in tutti e due i sensi: farlo o "
    "non farlo, quale copia usare, quando usarla e controllare che il risultato "
    "sia quello giusto. KaraDom e il suo staff non rispondono ne' dell'una ne' "
    "dell'altra strada: ne' dei danni di un ripristino fatto - per sbaglio, nel "
    "momento sbagliato o sulla copia sbagliata - ne' di quelli di un ripristino "
    "non fatto, fatto troppo tardi o diventato impossibile perche' le copie non "
    "c'erano piu' o erano state cancellate, e nemmeno dei problemi che nascono "
    "da copie rovinate, incomplete o modificate dall'esterno.\n\n"
    "Se prosegui, vuol dire che hai letto questo avviso, che lo hai capito e "
    "che ti prendi la responsabilita' della scelta che stai facendo.\n\n"
    "Vuoi continuare?"
)


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_019', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def _aggiungi_avviso(tab):
    import tkinter as tk
    from moduli.ui_scale import S, F
    from moduli.i18n import _

    cornice = tk.Frame(tab, bg='#2a2118', highlightthickness=1,
                       highlightbackground='#7a5c1e')
    cornice.pack(fill='x', padx=S(30), pady=(S(14), S(10)))

    tk.Label(cornice, text=_("RESPONSABILITA' SUI DATI"),
             bg='#2a2118', fg='#ffa500',
             font=F('Arial', 10, 'bold')).pack(anchor='w', padx=S(12), pady=(S(8), S(2)))

    tk.Label(cornice, text=_(AVVISO_TAB), bg='#2a2118', fg='#d8cbb4',
             font=F('Arial', 9), justify='left',
             wraplength=S(640)).pack(anchor='w', padx=S(12), pady=(0, S(10)))


def apply():
    if _spenta():
        return False
    try:
        from moduli.opzioni import OpzioniWindow as C

        # 1) l'avviso scritto, sempre visibile nel tab Backup
        if hasattr(C, 'create_tab_database') and not hasattr(C, '_orig_019_tabdb'):
            C._orig_019_tabdb = C.create_tab_database

            def create_tab_database(self, notebook, _orig=C._orig_019_tabdb):
                _orig(self, notebook)
                try:
                    schede = notebook.tabs()
                    if schede:
                        _aggiungi_avviso(notebook.nametowidget(schede[-1]))
                except Exception:
                    pass

            C.create_tab_database = create_tab_database

        # 2) il messaggio quando si preme Ripristina
        if hasattr(C, '_mostra_restore_dialog') and not hasattr(C, '_orig_019_restore'):
            C._orig_019_restore = C._mostra_restore_dialog

            def _mostra_restore_dialog(self, _orig=C._orig_019_restore):
                try:
                    from tkinter import messagebox
                    ok = messagebox.askokcancel("KaraDom - Ripristino dati", TESTO,
                                                icon='warning', default='cancel',
                                                parent=getattr(self, 'window', None))
                    if not ok:
                        return
                except Exception:
                    pass
                return _orig(self)

            C._mostra_restore_dialog = _mostra_restore_dialog

        # ⚠️ True anche se erano gia' a posto: rieseguire la patch non e' un
        #    fallimento, e chiamarla due volte non deve farla risultare spenta.
        return hasattr(C, '_orig_019_tabdb') or hasattr(C, '_orig_019_restore')
    except Exception:
        return False


def revert():
    try:
        from moduli.opzioni import OpzioniWindow as C
        fatto = False
        if hasattr(C, '_orig_019_tabdb'):
            C.create_tab_database = C._orig_019_tabdb
            del C._orig_019_tabdb
            fatto = True
        if hasattr(C, '_orig_019_restore'):
            C._mostra_restore_dialog = C._orig_019_restore
            del C._orig_019_restore
            fatto = True
        return fatto
    except Exception:
        return False


try:
    apply()
except Exception:
    pass
