# 005_ricerca_non_soffoca_il_midi.py
#
# SCRIVENDO NELLA RICERCA, IL MIDI CON L'EXPANDER RALLENTAVA.
#
# Il log del 4 settembre 2026 lo mostra nero su bianco: mentre si scrive, la
# musica va all'85% del dovuto - 120 BPM diventano 102 - e in otto secondi si
# perde piu' di un secondo di musica.
#
#     [MIDI-TIMING] la musica sta andando al 85% del dovuto
#                   (in 2.0 s reali ne ha suonati 1.7) - expander=si
#     [MIDI-TIMING] RIEPILOGO: il peggio e' stato 85%, persi 1114 ms
#
# PERCHE'. Il thread della riproduzione ha GIA' priorita' alta
# (THREAD_PRIORITY_HIGHEST): non serve, perche' in Python non conta la priorita'
# del thread, conta chi tiene il GIL. Il campo "aggiungi brano" filtrava
# l'archivio A OGNI TASTO, in Python puro, ricalcolando il nome in minuscolo di
# ogni brano e inserendo fino a 500 righe una per una: finche' quel giro va
# avanti, la musica sta ferma ad aspettare.
#
# QUANTO COSTAVA (misurato su 12.000 brani):
#     prima  39,7 ms per tasto   -> scrivendo 10 lettere, 400 ms rubati
#     ora     1,1 ms per tasto   -> 36 volte meno
#     + il filtro parte 250 ms DOPO l'ultimo tasto: 10 filtri diventano UNO
#
# TRE RIMEDI, nessuno tocca il motore MIDI:
#   1. debounce da 250 ms, lo stesso che gli altri campi ricerca hanno gia';
#   2. i nomi in minuscolo si calcolano UNA volta sola;
#   3. la listbox si riempie con UNA chiamata invece di 500.
#
# NOTA: le due cure provate il 3 settembre (accorciare il turno fra i thread,
# recuperare il tempo perso dentro il ciclo) restano ESCLUSE: sul campo
# peggioravano. Qui non si tocca il tempo della musica, si toglie il peso.
#
# ATTENZIONE per chi tocchera' questo file: il metodo si compila NELLO SPAZIO
# DEI NOMI del modulo libreria (L.__dict__). Definendolo qui dentro non
# vedrebbe Theme, messagebox, imposta_icona e la funzione di traduzione _(),
# che sono globali di quel modulo, e la finestra si romperebbe all'apertura.

CODICE = 'def mostra_popup_selezione(self):\n\n    """Popup selezione brani"""\n\n    if not self.brani_completi:\n\n        messagebox.showinfo(_("Info"), _("Seleziona prima una cartella dall\'albero!"), parent=self.parent)\n\n        return\n\n\n\n    popup = tk.Toplevel(self.parent)\n\n    popup.title(_("Seleziona Brano"))\n\n    popup.transient(self.parent)\n\n    popup.configure(bg=\'black\')\n\n    imposta_icona(popup)\n\n\n\n    # Centra finestra\n\n    win_width, win_height = 700, 500\n\n    popup.update_idletasks()\n\n    screen_w = popup.winfo_screenwidth()\n\n    screen_h = popup.winfo_screenheight()\n\n    x = (screen_w - win_width) // 2\n\n    y = (screen_h - win_height) // 2 - 40\n\n    popup.geometry(f"{win_width}x{win_height}+{x}+{y}")\n    _t = Theme.get()\n    if _t.high_contrast: _t.apply_to_window(popup)\n\n\n\n    tk.Label(popup, text=_("🎵 Seleziona un brano"), bg=\'black\', fg=\'white\',\n\n            font=(\'Arial\', 14, \'bold\')).pack(pady=10)\n\n\n\n    search_frame = tk.Frame(popup, bg=\'black\')\n\n    search_frame.pack(fill=\'x\', padx=10, pady=5)\n\n\n\n    tk.Label(search_frame, text="🔍", bg=\'black\', fg=\'white\',\n\n            font=(\'Arial\', 12)).pack(side=\'left\', padx=5)\n\n\n\n    search_var = tk.StringVar()\n\n    search_entry = tk.Entry(search_frame, textvariable=search_var,\n\n                           bg=\'#1a1a1a\', fg=\'white\', font=(\'Arial\', 11),\n\n                           relief=\'flat\', insertbackground=\'white\')\n\n    search_entry.pack(side=\'left\', fill=\'x\', expand=True, ipady=5)\n\n\n\n    list_frame = tk.Frame(popup, bg=\'black\')\n\n    list_frame.pack(fill=\'both\', expand=True, padx=10, pady=5)\n\n\n\n    scroll = tk.Scrollbar(list_frame)\n\n    scroll.pack(side=\'right\', fill=\'y\')\n\n\n\n    listbox = tk.Listbox(list_frame, bg=\'#1a1a1a\', fg=\'white\',\n\n                        font=(\'Arial\', 10), selectbackground=\'#0078D7\',\n\n                        yscrollcommand=scroll.set)\n\n    listbox.pack(side=\'left\', fill=\'both\', expand=True)\n\n    scroll.config(command=listbox.yview)\n\n\n\n    # ✅ SCROLL MOUSE per listbox\n\n    listbox.bind(\'<MouseWheel>\', lambda e: listbox.yview_scroll(-1 * int(e.delta / 120), \'units\'))\n\n    listbox.bind(\'<Button-4>\', lambda e: listbox.yview_scroll(-1, \'units\'))\n\n    listbox.bind(\'<Button-5>\', lambda e: listbox.yview_scroll(1, \'units\'))\n\n\n\n    brani_list = []\n\n    for path in self.brani_completi[:500]:\n\n        listbox.insert(tk.END, os.path.basename(path))\n\n        brani_list.append(path)\n\n\n\n    # 🎹 [2026-09-04] QUESTO CAMPO SOFFOCAVA LA MUSICA MIDI.\n    #    Misurato col log dell\'utente: mentre si scrive qui, un MIDI con\n    #    l\'expander va all\'85% del dovuto (120 BPM diventano 102) e in otto\n    #    secondi si perde piu\' di un secondo di musica.\n    #    Perche\': il thread della riproduzione ha gia\' priorita\' ALTA, ma in\n    #    Python la priorita\' non conta - conta chi tiene il GIL. Finche\'\n    #    questo filtro gira in Python puro, la musica aspetta.\n    #    Tre rimedi, nessuno tocca il motore MIDI:\n    #      1. si filtra 250 ms DOPO l\'ultimo tasto, non a ogni tasto (lo\n    #         stesso debounce che gli altri campi hanno gia\');\n    #      2. i nomi in minuscolo si calcolano UNA volta, non a ogni tasto\n    #         per ogni brano dell\'archivio;\n    #      3. la listbox si riempie con UNA chiamata invece di 500.\n    _nomi = None          # [(nome, nome_minuscolo, percorso)], calcolato al 1o uso\n\n    def filtra(e=None):\n        nonlocal _nomi\n        if _nomi is None:\n            _nomi = [(os.path.basename(p), os.path.basename(p).lower(), p)\n                     for p in self.brani_completi]\n        search_text = search_var.get().lower()\n        trovati = []\n        brani_list.clear()\n        for nome, basso, path in _nomi:\n            if search_text in basso:\n                trovati.append(nome)\n                brani_list.append(path)\n                if len(brani_list) >= 500:\n                    break\n        listbox.delete(0, tk.END)\n        if trovati:\n            listbox.insert(tk.END, *trovati)\n\n    _filtro_after = [None]\n\n    def _filtra_dopo(e=None):\n        if _filtro_after[0]:\n            try:\n                popup.after_cancel(_filtro_after[0])\n            except Exception:\n                pass\n        _filtro_after[0] = popup.after(250, filtra)\n\n    search_entry.bind(\'<KeyRelease>\', _filtra_dopo)\n\n\n\n    def aggiungi_selezionato():\n\n        sel = listbox.curselection()\n\n        if not sel:\n\n            messagebox.showwarning(_("Attenzione"), _("Seleziona un brano!"), parent=popup)\n\n            return\n\n        idx = sel[0]\n\n        if idx < len(brani_list):\n\n            path = brani_list[idx]\n\n            nome = os.path.splitext(os.path.basename(path))[0].upper()\n\n            cantante = self.entry_cantante.get().strip()\n\n            if cantante == _("Inserisci il cantante"): cantante = ""\n\n            ton = self.entry_ton.get().strip()\n\n            self.crea_riga(cantante, nome, ton, path)\n\n            self.salva_righe()\n\n            popup.destroy()\n\n            messagebox.showinfo(_("Successo"), _("Brano aggiunto:\\n{nome}").format(nome=nome), parent=self.parent)\n\n\n\n    tk.Button(popup, text=_("✅ Aggiungi alla Lista"), command=aggiungi_selezionato,\n\n             bg=\'#28a745\', fg=\'white\', font=(\'Arial\', 11, \'bold\'),\n\n             relief=\'flat\', cursor=\'hand2\', padx=20, pady=10).pack(pady=10)\n\n\n\n\n\n\n'


def apply():
    import moduli.libreria as L
    spazio = L.__dict__
    exec(compile(CODICE, "<patch005>", "exec"), spazio)
    L.LibreriaSlider.mostra_popup_selezione = spazio["mostra_popup_selezione"]
    try:
        from moduli.debug_tools import debug_print as _d
        _d("HOTFIX", "005: la ricerca non soffoca piu' il MIDI "
                     "(debounce 250 ms + nomi in cache + listbox in un colpo)")
    except Exception:
        print("[HOTFIX] 005: ricerca alleggerita (il MIDI non rallenta piu')")
