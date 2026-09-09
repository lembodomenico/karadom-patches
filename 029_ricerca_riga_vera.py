# 029 - la ricerca nelle righe della scaletta passa dalla tabella (quella VERA).
#
# ⛔ LA 024 PATCHAVA UNA FUNZIONE MORTA. `_setup_brano_autocomplete` non la
#    chiama nessuno: verificato, zero riferimenti in tutto il programma. La
#    024 la sostituiva, scriveva "AGGANCIATA" e non cambiava niente, perche'
#    quel codice non gira mai. Il campo che si apre col doppio clic su una
#    riga della scaletta e' `_sc_edit_brano`, ed era rimasto con il ciclo su
#    tutti i brani e i 200 ms fissi.
#
# ⚠️ La funzione e' COPIATA DAL SORGENTE (la lezione della 015: si porta
#    dietro tutti i nomi, cosi' funziona anche nel compilato) e si cambiano
#    due soli punti: la lista su cui gira il ciclo e l'attesa.
#
# SE NON VA BENE: `patch_029 = 0` la spegne su una macchina sola.

CODICE = 'def _sc_edit_brano(self, iid, text_item_id):\n    """Entry sovrapposta con suggerimenti per cercare/selezionare brano"""\n    # Chiudi edit precedente\n    if hasattr(self, \'_sc_edit_entry\') and self._sc_edit_entry:\n        try: self._sc_edit_entry.destroy()\n        except: pass\n    if hasattr(self, \'_sc_brano_sugg\') and self._sc_brano_sugg:\n        try: self._sc_brano_sugg.destroy()\n        except: pass\n\n    bb = self._sc_cv.bbox(text_item_id)\n    if not bb: return\n    x1 = bb[0] - int(self._sc_cv.canvasx(0))\n    y1 = bb[1] - int(self._sc_cv.canvasy(0))\n    # Allarga il campo editabile a tutta la colonna "Brano" (fino a "Ton"),\n    # con minimo di sicurezza, invece di adattarlo al solo testo presente.\n    try:\n        _xc, _xb, _xt = self._sc_get_col_x()\n        _col_w = max(_xt - _xb - self._S(20), self._S(420))\n    except Exception:\n        _col_w = self._S(420)\n    w = max(bb[2] - bb[0], _col_w)\n    h = max(bb[3] - bb[1], self._S(30))\n\n    d = self._sc_row_data.get(iid, {})\n    current = d.get(\'brano\', \'\')\n    is_placeholder = current == \'\' or current.upper().startswith(_(\'Digita per cercare...\').rstrip(\'.\').upper())\n\n    # Entry sovrapposta\n    entry = tk.Entry(self._sc_cv, bg=\'#1a1a1a\', fg=\'white\',\n        font=self._F(\'Arial\', 16, \'bold\'), relief=\'flat\', insertbackground=\'white\')\n    if not is_placeholder:\n        entry.insert(0, current)\n        entry.select_range(0, tk.END)\n    entry.place(x=x1-3, y=y1-2, width=w+10, height=h+4)\n    entry.focus_set()\n    self._sc_edit_entry = entry\n\n    # Listbox suggerimenti sotto l\'entry\n    sugg_frame = tk.Frame(self.parent, bg=\'black\', bd=2, relief=\'solid\')\n    sugg_lb = tk.Listbox(sugg_frame, bg=\'#1a1a1a\', fg=\'yellow\',\n        font=self._F(\'Arial\', 14), relief=\'flat\', bd=0,\n        highlightthickness=1, highlightbackground=\'#333333\',\n        selectbackground=\'#0078D7\', activestyle=\'none\')\n    sugg_lb.pack(fill=\'both\', expand=True)\n    self._sc_brano_sugg = sugg_frame\n    self._sc_brano_sugg_lb = sugg_lb\n    self._sc_brano_sugg_results = []\n    self._sc_brano_iid = iid\n    self._sc_brano_text_id = text_item_id\n\n    # Posiziona suggerimenti sotto l\'entry\n    ex = self._sc_cv.winfo_rootx() + x1 - 3\n    ey = self._sc_cv.winfo_rooty() + y1 + h + 4\n    px = ex - self.parent.winfo_rootx()\n    py = ey - self.parent.winfo_rooty()\n    sugg_frame.place(x=px, y=py, width=w+10, height=250)\n    sugg_frame.lift()\n    sugg_frame.place_forget()  # Nascondi inizialmente\n\n    # Scroll suggerimenti\n    sugg_lb.bind(\'<MouseWheel>\', lambda e: sugg_lb.yview_scroll(-1*int(e.delta/120), \'units\'))\n    sugg_lb.bind(\'<Button-4>\', lambda e: sugg_lb.yview_scroll(-1, \'units\'))\n    sugg_lb.bind(\'<Button-5>\', lambda e: sugg_lb.yview_scroll(1, \'units\'))\n\n    _debounce = [None]\n\n    def _on_key(e):\n        if e.keysym in (\'Down\', \'Up\', \'Return\', \'Escape\'):\n            return\n        if _debounce[0]:\n            self.parent.after_cancel(_debounce[0])\n        # ⭐ [patch 029] la stessa attesa del campo IN ALTO: sopra i\n        #    100.000 brani si aspetta che l\'utente finisca di scrivere\n        #    (900 ms), sotto si resta reattivi (150 ms). Prima erano\n        #    200 ms fissi: una ricerca ogni due tasti.\n        _att029 = 200\n        try:\n            _v029 = getattr(self, \'_attese_ricerca\', None)\n            if _v029 is None:\n                from .database import Database as _Db029\n                _lunga029 = int(str(_Db029.get_config(\n                    \'ricerca_attesa_ms\', \'900\')).strip())\n                _soglia029 = int(str(_Db029.get_config(\n                    \'ricerca_soglia_brani\', \'100000\')).strip())\n                _v029 = (max(100, min(2000, _lunga029)), 150,\n                         max(0, _soglia029))\n                self._attese_ricerca = _v029\n            _att029 = (_v029[0] if len(self.brani_pc or ()) >= _v029[2]\n                       else _v029[1])\n        except Exception:\n            pass\n        _debounce[0] = self.parent.after(_att029, _do_search)\n\n    def _do_search():\n        testo = entry.get().strip().lower()\n        if not testo or len(testo) < 2:\n            sugg_frame.place_forget()\n            return\n        # Stessa logica di aggiorna_suggerimenti_live\n        if \'*\' in testo:\n            parti = [p.strip() for p in testo.split(\'*\') if p.strip()]\n        else:\n            parti = [p for p in re.split(r\'\\s+\', testo) if p]\n        parti_ext = []\n        parti_is_ext = []\n        for p in parti:\n            if p.startswith(\'.\'):\n                parti_ext.append(p[1:]); parti_is_ext.append(True)\n            else:\n                parti_ext.append(p); parti_is_ext.append(False)\n        if not parti_ext:\n            sugg_frame.place_forget()\n            return\n        risultati = []\n        # ⭐ [patch 029] LA RICERCA LA FA IL DATABASE.\n        #    Stessa tabella della 016, quella che ha sistemato il campo in\n        #    alto. Non si riscrive il ciclo: gli si mette davanti la lista\n        #    GIA\' filtrata, cosi\' scorre 50 nomi invece di 400.000 e il\n        #    criterio resta identico, riga per riga.\n        #\n        # ⛔ Il ciclo qui sotto gira nel thread della GRAFICA, non in uno\n        #    a parte: a ogni tasto il programma si fermava per tutto il\n        #    tempo della scansione, ed e\' da li\' che il MIDI perdeva i\n        #    colpi. Con la tabella l\'attesa non esiste piu\'.\n        _lista029 = self.brani_pc\n        _dove029 = \'CICLO sui file\'\n        try:\n            _idx029 = self._cerca_in_tabella_016(parti_ext, parti_is_ext,\n                                                 _lista029, 50)\n            if _idx029 is not None:\n                _lista029 = [_lista029[_i029] for _i029 in _idx029]\n                _dove029 = \'tabella\'\n            else:\n                try:\n                    self._prepara_tabella_016()\n                except Exception:\n                    pass\n        except Exception:\n            pass\n        import time as _t029\n        _inizio029 = _t029.perf_counter()\n        for brano in _lista029:\n            parole = brano.get(\'parole\')\n            ext = brano.get(\'ext\', \'\')\n            if parole is None:\n                nl = brano[\'nome\'].lower()\n                ns, ep = os.path.splitext(nl)\n                ext = ep[1:] if ep else \'\'\n                parole = ns.split()\n                if ext: parole.append(ext)\n            ok = True\n            for i, pc in enumerate(parti_ext):\n                if parti_is_ext[i]:\n                    if ext != pc: ok = False; break\n                else:\n                    nome_full = brano.get(\'nome_lower\', brano[\'nome\'].lower())\n                    if not any(w.startswith(pc) for w in parole) and pc not in nome_full:\n                        ok = False; break\n            if ok:\n                risultati.append(brano)\n                if len(risultati) >= 50: break\n        try:\n            print(\'[ricerca riga] %s | %d brani | %d risultati | %.0f ms\'\n                  % (_dove029, len(self.brani_pc or ()), len(risultati),\n                     (_t029.perf_counter() - _inizio029) * 1000))\n        except Exception:\n            pass\n        self._sc_brano_sugg_results = risultati\n        sugg_lb.delete(0, tk.END)\n        if risultati:\n            for r in risultati:\n                sugg_lb.insert(tk.END, f" 🎵 {r[\'nome\']}")\n            sugg_frame.place(x=px, y=py, width=w+10, height=250)\n            sugg_frame.lift()\n            entry.focus_force()\n        else:\n            sugg_frame.place_forget()\n\n    def _select_sugg(e=None):\n        sel = sugg_lb.curselection()\n        if sel and sel[0] < len(self._sc_brano_sugg_results):\n            brano_info = self._sc_brano_sugg_results[sel[0]]\n            nome = os.path.splitext(brano_info[\'nome\'])[0].upper()\n            path = brano_info[\'path\']\n            ext = os.path.splitext(path)[1][1:].upper()\n            # Aggiorna dati Canvas\n            d[\'brano\'] = nome\n            d[\'path\'] = path\n            d[\'ext\'] = ext\n            # Aggiorna path nel dizionario riga\n            for riga in self.righe:\n                if riga.get(\'iid\') == iid:\n                    riga[\'path\'] = path\n                    break\n            self.salva_righe()\n            _close()\n            # Ridisegna per troncamento corretto\n            self.parent.after(10, self._sc_redraw_all)\n\n    def _close():\n        try: entry.destroy()\n        except: pass\n        try: sugg_frame.destroy()\n        except: pass\n        self._sc_edit_entry = None\n        self._sc_brano_sugg = None\n\n    def _on_down(e):\n        if sugg_lb.size() > 0:\n            cur = sugg_lb.curselection()\n            nxt = (cur[0] + 1) if cur else 0\n            nxt = min(nxt, sugg_lb.size() - 1)\n            sugg_lb.selection_clear(0, tk.END)\n            sugg_lb.selection_set(nxt)\n            sugg_lb.see(nxt)\n        return \'break\'\n\n    def _on_up(e):\n        if sugg_lb.size() > 0:\n            cur = sugg_lb.curselection()\n            nxt = (cur[0] - 1) if cur else sugg_lb.size() - 1\n            nxt = max(nxt, 0)\n            sugg_lb.selection_clear(0, tk.END)\n            sugg_lb.selection_set(nxt)\n            sugg_lb.see(nxt)\n        return \'break\'\n\n    def _on_enter(e):\n        if sugg_lb.curselection():\n            _select_sugg()\n        elif sugg_lb.size() > 0:\n            sugg_lb.selection_set(0)\n            _select_sugg()\n        return \'break\'\n\n    entry.bind(\'<KeyRelease>\', _on_key)\n    entry.bind(\'<Down>\', _on_down)\n    entry.bind(\'<Up>\', _on_up)\n    entry.bind(\'<Return>\', _on_enter)\n    entry.bind(\'<Escape>\', lambda e: _close())\n    entry.bind(\'<FocusOut>\', lambda e: self.parent.after(200, _close))\n    sugg_lb.bind(\'<<ListboxSelect>>\', _select_sugg)'


def _spenta():
    """⚠️ AL CONTRARIO DELLE ALTRE: questa nasce SPENTA.

    Sta nel manifest solo per non farsi cancellare dal ritiro, ma non deve
    entrare in funzione da nessuna parte finche' non e' collaudata: si
    accende su una macchina alla volta scrivendo `patch_029 = 1` nella
    configurazione. Quando sara' provata, questa riga tornera' come le altre.
    """
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_029', '0')).strip() not in ('1', 'si', 'on')
    except Exception:
        return True


def traccia(testo):
    try:
        import datetime
        import os
        d = os.path.join(os.environ.get('LOCALAPPDATA') or
                         os.path.expanduser('~'), 'KaraDom')
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, 'patch029.log'), 'a', encoding='utf-8') as f:
            f.write('%s  %s' % (
                datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                testo) + chr(10))
    except Exception:
        pass


def apply():
    if _spenta():
        traccia('spenta da patch_029 = 0')
        return False
    try:
        import moduli.libreria as m
        C = m.LibreriaSlider
        if hasattr(C, '_orig_029'):
            traccia('gia' + chr(39) + ' agganciata')
            return True
        if not hasattr(C, '_cerca_in_tabella_016'):
            traccia('la 016 non e' + chr(39) + ' attiva: senza tabella non si aggancia')
            return False
        C._orig_029 = C._sc_edit_brano
        spazio = m.__dict__
        exec(compile(CODICE, "<patch029>", "exec"), spazio)
        setattr(C, '_sc_edit_brano', spazio['_sc_edit_brano'])
        traccia('AGGANCIATA: _sc_edit_brano (il campo VERO delle righe)')
        print("patch 029: la ricerca nelle righe della scaletta passa dalla tabella")
        return True
    except Exception as e:
        traccia('NON agganciata: %s: %s' % (type(e).__name__, e))
        print("patch 029: %s" % e)
        return False


def revert():
    try:
        import sys
        m = sys.modules.get('moduli.libreria')
        C = getattr(m, 'LibreriaSlider', None) if m else None
        if C is not None and hasattr(C, '_orig_029'):
            setattr(C, '_sc_edit_brano', C._orig_029)
            del C._orig_029
            print("patch 029: rimesso l'originale")
            return True
    except Exception as e:
        print("patch 029: %s" % e)
    return False


try:
    apply()
except Exception:
    pass
