# 024 - anche la ricerca nelle righe della scaletta passa dalla tabella.
#
# La 016 ha fatto questo al campo filtro IN ALTO. Nelle righe della scaletta
# c'era una COPIA A MANO dello stesso ciclo, con altri nomi di variabili
# (pb invece di parole_brano, _ac_gen invece di gen): la 016 non poteva
# toccarla, ed e' rimasta a scorrere tutti i brani a ogni tasto.
#
# ⚠️ La funzione e' COPIATA DAL SORGENTE e si cambia solo il blocco della
#    scansione: si porta dietro tutti i nomi che nel compilato potrebbero
#    mancare (la lezione della 015) e non dipende da come e' compilato il
#    programma.
#
# ⚠️ SOLO SOPRA I 100.000 BRANI: senza la tabella della 016 non cambia niente.
#
# SE NON VA BENE: `patch_024 = 0` la spegne su una macchina sola.

CODICE = 'def _setup_brano_autocomplete(self, riga_index):\n\n    """Configura autocompletamento per campo brano - USA INDICE"""\n\n    riga = self.righe[riga_index]\n\n    entry_brano = riga[\'brano\']\n\n    \n\n    # ✅ Assicurati che il cursore sia visibile\n\n    entry_brano.config(insertbackground=\'white\')\n\n    \n\n    entry_brano.unbind(\'<KeyRelease>\')\n\n    entry_brano.unbind(\'<FocusIn>\')\n\n    entry_brano.unbind(\'<FocusOut>\')\n\n    entry_brano.unbind(\'<Return>\')\n\n    entry_brano.unbind(\'<Down>\')\n\n    entry_brano.unbind(\'<Up>\')\n\n    entry_brano.unbind(\'<Escape>\')\n\n    entry_brano.unbind(\'<Button-1>\')\n\n    \n\n    riga[\'_suggestions_frame\'] = None\n\n    riga[\'_suggestions_listbox\'] = None\n\n    riga[\'_current_suggestions\'] = []\n\n    \n\n    def on_click(e):\n\n        # ✅ Al click, rendi il campo editabile e dai focus\n\n        if entry_brano.cget(\'state\') == \'readonly\' or entry_brano.cget(\'fg\') == \'gray\':\n\n            entry_brano.config(state=\'normal\', fg=\'white\')\n\n            if entry_brano.get() == _("Digita per cercare..."):\n\n                entry_brano.delete(0, tk.END)\n\n            entry_brano.icursor(tk.END)  # Posiziona cursore alla fine\n\n    \n\n    def on_focus_in(e):\n\n        if entry_brano.cget(\'fg\') == \'gray\':\n\n            entry_brano.config(state=\'normal\', fg=\'white\')\n\n            entry_brano.delete(0, tk.END)\n\n    \n\n    def on_focus_out(e):\n\n        entry_brano.after(200, lambda: _check_focus_out())\n\n    \n\n    def _check_focus_out():\n\n        testo = entry_brano.get().strip()\n\n        if not testo or testo.lower() == _("Digita per cercare...").lower():\n\n            entry_brano.config(state=\'normal\', fg=\'gray\')\n\n            entry_brano.delete(0, tk.END)\n\n            entry_brano.insert(0, _("Digita per cercare..."))\n\n        _hide_suggestions()\n\n    \n\n    def on_key_release(e):\n\n        if e.keysym in (\'Up\', \'Down\', \'Return\', \'Escape\'):\n\n            return\n\n        \n\n        # ✅ AZZERA PATH quando inizi a digitare (per evitare path vecchio)\n\n        if riga[\'path\']:\n\n            riga[\'path\'] = \'\'\n\n        \n\n        testo = entry_brano.get().lower().strip()\n\n        \n\n        if not testo or testo == _("Digita per cercare...").lower() or len(testo) < 2:\n\n            _hide_suggestions()\n\n            return\n\n        \n\n        if \'*\' in testo:\n\n            raw_parts = [p.strip() for p in testo.split(\'*\') if p.strip()]\n\n            parti_wildcard = []\n\n            parti_is_ext = []\n\n            for p in raw_parts:\n\n                if p.startswith(\'.\'):\n\n                    parti_wildcard.append(p[1:])\n\n                    parti_is_ext.append(True)\n\n                else:\n\n                    parti_wildcard.append(p)\n\n                    parti_is_ext.append(False)\n\n        else:\n\n            raw_parts = [p for p in re.split(r\'\\s+\', testo) if p]\n\n            parti_wildcard = []\n\n            parti_is_ext = []\n\n            for p in raw_parts:\n\n                if p.startswith(\'.\'):\n\n                    parti_wildcard.append(p[1:])\n\n                    parti_is_ext.append(True)\n\n                else:\n\n                    parti_wildcard.append(p)\n\n                    parti_is_ext.append(False)\n\n        \n\n        if not parti_wildcard:\n\n            _hide_suggestions()\n\n            return\n\n        \n\n        risultati_mp3 = []\n        risultati_altri = []\n        # ✅ Ricerca in THREAD per non bloccare UI con 263k+ brani\n        _ac_gen = getattr(self, \'_ac_search_gen\', 0) + 1\n        self._ac_search_gen = _ac_gen\n        brani_ref = self.brani_pc\n\n        def _ac_search():\n            # ✅ Stesso indice di ricerca del filtro in alto\n            self._ensure_search_index()\n            r_mp3 = []\n            r_altri = []\n            # ⭐ [patch 024] LA RICERCA LA FA IL DATABASE.\n            #    Stesso identico blocco della 016, che ha sistemato il campo\n            #    filtro in alto: qui era rimasta una COPIA a mano dello stesso\n            #    ciclo, con altri nomi di variabili, e nessuno l\'aveva toccata.\n            #\n            # ⛔ Quando risponde la tabella NON si ricontrolla niente: i\n            #    brani si smistano e basta, il filtro l\'ha gia\' fatto lei in SQL.\n            #    Ricontrollarli uno per uno sarebbe rifare il lavoro due volte.\n            #    Il ciclo sui file resta solo come ripiego per quando la tabella\n            #    non c\'e\' - archivio sotto i 100.000 brani, o non ancora pronta.\n            _righe024 = None\n            try:\n                _righe024 = self._cerca_in_tabella_016(\n                    parti_wildcard, parti_is_ext, brani_ref, 100)\n            except Exception:\n                _righe024 = None\n            \n            if _righe024 is not None:\n                for _i024 in _righe024:\n                    if getattr(self, \'_ac_search_gen\', 0) != _ac_gen:\n                        return\n                    brano = brani_ref[_i024]\n                    if brano.get(\'ext\', \'\') == \'mp3\':\n                        r_mp3.append(brano)\n                    else:\n                        r_altri.append(brano)\n            else:\n                try:\n                    self._prepara_tabella_016()\n                except Exception:\n                    pass\n                for brano in brani_ref:\n                    if getattr(self, \'_ac_search_gen\', 0) != _ac_gen:\n                        return  # Cancellata\n                    pb = brano.get(\'parole\')\n                    ex = brano.get(\'ext\', \'\')\n                    if pb is None:\n                        nl = brano[\'nome\'].lower()\n                        ns, ep = os.path.splitext(nl)\n                        ex = ep[1:] if ep else ""\n                        if \' - \' in ns:\n                            pp = ns.split(\' - \', 1)\n                            pb = pp[0].strip().split() + pp[1].strip().split()\n                        else:\n                            pb = ns.split()\n                        if ex:\n                            pb.append(ex)\n                    ok = True\n                    for i, pc in enumerate(parti_wildcard):\n                        if parti_is_ext[i]:\n                            if ex != pc:\n                                ok = False\n                                break\n                        else:\n                            # ✅ Stessa regola del filtro in alto (aggiorna_suggerimenti_live):\n                            #    prefisso di parola OPPURE sottostringa nel nome completo\n                            nome_full = brano.get(\'nome_lower\', brano[\'nome\'].lower())\n                            if not any(w.startswith(pc) for w in pb) and pc not in nome_full:\n                                ok = False\n                                break\n                    if ok:\n                        if ex == \'mp3\':\n                            r_mp3.append(brano)\n                        else:\n                            r_altri.append(brano)\n                        if len(r_mp3) + len(r_altri) >= 100:\n                            break\n            if getattr(self, \'_ac_search_gen\', 0) == _ac_gen:\n                # ✅ Dedup per path\n                visti = set()\n                dedup = []\n                for b in (r_mp3 + r_altri):\n                    p = b.get(\'path\', \'\')\n                    if p not in visti:\n                        visti.add(p)\n                        dedup.append(b)\n                finali = dedup[:50]\n                try:\n                    self.parent.after(0, lambda f=finali: _show_suggestions(f) if f else _hide_suggestions())\n                except:\n                    pass\n\n        threading.Thread(target=_ac_search, daemon=True).start()\n\n    \n\n    def _show_suggestions(risultati):\n\n        _hide_suggestions()\n\n        \n\n        x = entry_brano.winfo_rootx() - self.parent.winfo_rootx()\n\n        y = entry_brano.winfo_rooty() - self.parent.winfo_rooty()\n\n        h = entry_brano.winfo_height()\n\n        \n\n        sugg_container = tk.Frame(self.parent, bg=\'black\', bd=2, relief=\'solid\')\n\n        riga[\'_suggestions_frame\'] = sugg_container\n\n        \n\n        sugg_container.place(x=x - 200, y=y + h, width=700, height=250)\n\n        sugg_container.lift()\n\n        \n\n        listbox = tk.Listbox(\n\n            sugg_container,\n\n            bg=\'#1a1a1a\', fg=\'yellow\',\n\n            font=(\'Arial\', 14),\n\n            relief=\'flat\', bd=0,\n\n            highlightthickness=1,\n\n            highlightbackground=\'#333333\',\n\n            selectmode=\'single\',\n\n            selectbackground=\'#0078D7\',\n\n            activestyle=\'none\'\n\n        )\n\n        listbox.pack(fill=\'both\', expand=True)\n\n        \n\n        for r in risultati:\n\n            listbox.insert(tk.END, f" 🎵 {r[\'nome\']}")\n\n        \n\n        riga[\'_suggestions_listbox\'] = listbox\n\n        riga[\'_current_suggestions\'] = risultati\n\n        \n\n        def on_scroll(event):\n\n            listbox.yview_scroll(-1 * int(event.delta / 120), \'units\')\n\n        \n\n        listbox.bind(\'<MouseWheel>\', on_scroll)\n\n        listbox.bind(\'<Button-4>\', lambda e: listbox.yview_scroll(-1, \'units\'))\n\n        listbox.bind(\'<Button-5>\', lambda e: listbox.yview_scroll(1, \'units\'))\n\n        listbox.bind(\'<<ListboxSelect>>\', lambda e: _select_suggestion())\n\n    \n\n    def _hide_suggestions():\n\n        if riga.get(\'_suggestions_frame\'):\n\n            try:\n\n                riga[\'_suggestions_frame\'].destroy()\n\n            except:\n\n                pass\n\n            riga[\'_suggestions_frame\'] = None\n\n            riga[\'_suggestions_listbox\'] = None\n\n    \n\n    def _navigate_suggestions(e):\n\n        listbox = riga.get(\'_suggestions_listbox\')\n\n        if not listbox:\n\n            return\n\n        \n\n        current = listbox.curselection()\n\n        size = listbox.size()\n\n        \n\n        if e.keysym == \'Down\':\n\n            next_idx = (current[0] + 1) if current else 0\n\n            next_idx = min(next_idx, size - 1)\n\n        elif e.keysym == \'Up\':\n\n            next_idx = (current[0] - 1) if current else size - 1\n\n            next_idx = max(next_idx, 0)\n\n        else:\n\n            return\n\n        \n\n        listbox.selection_clear(0, tk.END)\n\n        listbox.selection_set(next_idx)\n\n        listbox.see(next_idx)\n\n        return "break"\n\n    \n\n    def _select_suggestion(e=None):\n\n        listbox = riga.get(\'_suggestions_listbox\')\n\n        suggestions = riga.get(\'_current_suggestions\', [])\n\n        \n\n        if not listbox:\n\n            return\n\n        \n\n        selection = listbox.curselection()\n\n        if selection and selection[0] < len(suggestions):\n\n            brano_info = suggestions[selection[0]]\n\n            from pathlib import Path\n\n            \n\n            entry_brano.config(state=\'normal\', fg=\'white\')\n\n            entry_brano.delete(0, tk.END)\n\n            entry_brano.insert(0, Path(brano_info[\'path\']).stem.upper())\n\n            entry_brano.config(state=\'readonly\')\n\n            \n\n            riga[\'path\'] = brano_info[\'path\']\n\n            \n\n            durata_str = self._calcola_durata(brano_info[\'path\'])\n\n            if riga.get(\'durata_label\'):\n\n                riga[\'durata_label\'].config(text=durata_str)\n\n            \n\n            _hide_suggestions()\n\n            self.salva_righe()\n\n            \n\n            entry_brano.unbind(\'<KeyRelease>\')\n\n            entry_brano.unbind(\'<FocusIn>\')\n\n            entry_brano.unbind(\'<FocusOut>\')\n\n    \n\n    def on_enter(e):\n\n        listbox = riga.get(\'_suggestions_listbox\')\n\n        if listbox and listbox.curselection():\n\n            _select_suggestion()\n\n        elif riga.get(\'_current_suggestions\'):\n\n            listbox = riga.get(\'_suggestions_listbox\')\n\n            if listbox and listbox.size() > 0:\n\n                listbox.selection_set(0)\n\n                _select_suggestion()\n\n    \n\n    def on_escape(e):\n\n        _hide_suggestions()\n\n    \n\n    entry_brano.bind(\'<Button-1>\', on_click)\n\n    entry_brano.bind(\'<FocusIn>\', on_focus_in)\n\n    entry_brano.bind(\'<FocusOut>\', on_focus_out)\n\n    # ✅ Debounce autocomplete (200ms) per evitare lag con 263k+ brani\n    _brano_debounce_id = [None]\n    def _debounce_key_release(e):\n        if _brano_debounce_id[0]:\n            self.parent.after_cancel(_brano_debounce_id[0])\n        _brano_debounce_id[0] = self.parent.after(200, lambda: on_key_release(e))\n    entry_brano.bind(\'<KeyRelease>\', _debounce_key_release)\n\n    entry_brano.bind(\'<Return>\', on_enter)\n\n    entry_brano.bind(\'<Down>\', _navigate_suggestions)\n\n    entry_brano.bind(\'<Up>\', _navigate_suggestions)\n\n    entry_brano.bind(\'<Escape>\', on_escape)\n\n\n'


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_024', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def traccia(testo):
    """Una riga su file. Nell'eseguibile compilato i messaggi a schermo si
    perdono: senza questo, quando il cliente dice "non va" non c'e' modo di
    sapere se la patch si e' agganciata o e' morta per strada."""
    try:
        import datetime, os
        d = os.path.join(os.environ.get('LOCALAPPDATA') or
                         os.path.expanduser('~'), 'KaraDom')
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, 'patch024.log'), 'a', encoding='utf-8') as f:
            f.write('%s  %s' % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                  testo) + chr(10))
    except Exception:
        pass


def apply():
    if _spenta():
        traccia('spenta da patch_024 = 0')
        return False
    try:
        # Come la 016: si importa il modulo e si sostituisce il metodo, subito.
        import moduli.libreria as m
        C = m.LibreriaSlider
        if hasattr(C, '_orig_024'):
            traccia('gia' + chr(39) + ' agganciata')
            return True
        if not hasattr(C, '_cerca_in_tabella_016'):
            traccia('la 016 non e' + chr(39) + ' attiva: senza tabella non si aggancia')
            return False
        C._orig_024 = C._setup_brano_autocomplete
        spazio = m.__dict__
        exec(compile(CODICE, "<patch024>", "exec"), spazio)
        setattr(C, '_setup_brano_autocomplete', spazio['_setup_brano_autocomplete'])
        traccia('AGGANCIATA: la ricerca nelle righe della scaletta passa dalla tabella')
        print("patch 024: la ricerca nelle righe della scaletta passa dalla tabella")
        return True
    except Exception as e:
        traccia('NON agganciata: %s: %s' % (type(e).__name__, e))
        print("patch 024: %s" % e)
        return False


def revert():
    try:
        import sys
        m = sys.modules.get('moduli.libreria')
        C = getattr(m, 'LibreriaSlider', None) if m else None
        if C is not None and hasattr(C, '_orig_024'):
            setattr(C, '_setup_brano_autocomplete', C._orig_024)
            del C._orig_024
            print("patch 024: rimesso l'originale")
            return True
    except Exception as e:
        print("revert 024: %s" % e)
    return False


try:
    apply()
except Exception as _e:
    print("patch 024: %s" % _e)
