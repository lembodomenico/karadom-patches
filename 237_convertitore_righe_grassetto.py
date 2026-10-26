# 237 - convertitore righe grassetto

_VER = 4

# _generate_ass_file com'e' nel sorgente (moduli/convertitore.py): righe piu' vicine,
# grassetto a scelta, preset 'Come il monitor di KaraDom'. Si esegue nel modulo del convertitore cosi' trova gli stessi nomi.
_ASS = 'def _generate_ass_file(self, filepath, lines_data, width, height):\n    """Genera file ASS con sottotitoli karaoke"""\n    font_name = self.font_var.get()\n    # "Auto" = come il monitor di KaraDom: il carattere riempie la riga\n    _dim = str(self.font_size_var.get()).strip()\n    auto = not _dim.isdigit()\n    base_font_size = 0 if auto else int(_dim)\n    num_lines = int(self.lines_var.get())\n    \n    # ✅ Ordina righe per timestamp di inizio: evita tempi ASS decrescenti\n    # con SYLT che contengono righe in ordine non-temporale (es. duetti)\n    lines_data = sorted(\n        [l for l in lines_data if l],\n        key=lambda line: line[0][1] if line else 0\n    )\n    \n    # Scala il font size in base alla risoluzione\n    # Il font size è pensato per 1024x600, scala proporzionalmente\n    base_width = 1024\n    base_height = 600\n    scale_factor = min(width / base_width, height / base_height)\n\n    # Righe COME IL MONITOR di KaraDom: l\'altezza del video divisa in parti uguali, le righe\n    # occupano tutto lo schermo dall\'alto in basso (prima stavano strette al centro).\n    line_height = height // num_lines\n    if auto:\n        font_size = int(line_height * 0.8)          # il carattere riempie la riga\n    else:\n        font_size = min(int(base_font_size * scale_factor), int(line_height * 0.95))\n\n    print(f"📝 Generazione ASS: Font={font_name}, Size={\'Auto\' if auto else base_font_size}→{font_size} (scale={scale_factor:.2f}), Righe={num_lines}, Res={width}x{height}")\n    \n    # Colori in formato ASS (BGR con alpha)\n    text_color_hex = self.text_color.get().lstrip(\'#\')\n    highlight_hex = self.highlight_color.get().lstrip(\'#\')\n    \n    # Converti RGB -> BGR per ASS\n    text_bgr = text_color_hex[4:6] + text_color_hex[2:4] + text_color_hex[0:2]\n    highlight_bgr = highlight_hex[4:6] + highlight_hex[2:4] + highlight_hex[0:2]\n    \n    # Outline scalato\n    outline_size = max(2, int(3 * scale_factor))\n    shadow_size = max(1, int(2 * scale_factor))\n\n    total_text_height = line_height * num_lines\n    start_y = (height - total_text_height) // 2 + line_height // 2\n\n    bold = -1 if getattr(self, \'bold_var\', None) is None or self.bold_var.get() else 0\n\n    # Righe troppo larghe (caratteri grandi): non vanno a capo (si sovrapporrebbero alla riga\n    # sotto) ma si stringono quanto basta per stare nello schermo, come fa il monitor.\n    _file_font = {\'Arial\': (\'arial\', \'arialbd\'), \'Calibri\': (\'calibri\', \'calibrib\'),\n                  \'Verdana\': (\'verdana\', \'verdanab\'), \'Tahoma\': (\'tahoma\', \'tahomabd\'),\n                  \'Impact\': (\'impact\', \'impact\'), \'Georgia\': (\'georgia\', \'georgiab\'),\n                  \'Times New Roman\': (\'times\', \'timesbd\'), \'Comic Sans MS\': (\'comic\', \'comicbd\'),\n                  \'Trebuchet MS\': (\'trebuc\', \'trebucbd\')}\n    # Il Fontsize dell\'ASS e\' l\'altezza ascendente+discendente del carattere (libass), non la\n    # sua misura in pixel: la larghezza si scala di font_size / (ascent + descent), altrimenti\n    # le righe risultano ~20% piu\' larghe del vero e si stringono senza bisogno.\n    _misura, _scala = None, 1.0\n    try:\n        from PIL import ImageFont\n        _ff = _file_font.get(font_name, (\'arial\', \'arialbd\'))[1 if bold else 0]\n        _misura = ImageFont.truetype(_ff + \'.ttf\', font_size)\n        # libass: Fontsize = usWinAscent + usWinDescent (tabella OS/2) -> em = size * upem / (A + D)\n        with open(_misura.path, \'rb\') as _fh:\n            _dati = _fh.read()\n        _n = struct.unpack(\'>H\', _dati[4:6])[0]\n        _tab = {_dati[12 + 16 * i:16 + 16 * i]: struct.unpack(\'>I\', _dati[20 + 16 * i:24 + 16 * i])[0]\n                for i in range(_n)}\n        _upem = struct.unpack(\'>H\', _dati[_tab[b\'head\'] + 18:_tab[b\'head\'] + 20])[0]\n        _wa, _wd = struct.unpack(\'>HH\', _dati[_tab[b\'OS/2\'] + 74:_tab[b\'OS/2\'] + 78])\n        if _wa + _wd > 0:\n            _scala = _upem / float(_wa + _wd)\n    except Exception:\n        _scala = 0.82 if _misura is not None else 1.0\n    _largo = width - 40 - 2 * outline_size\n\n    def _stringi(riga):\n        testo = \'\'.join(x.replace(\'\\n\', \'\').replace(\'\\r\', \'\').upper() for x, _t in riga)\n        try:\n            w = _misura.getlength(testo) * _scala if _misura else len(testo) * font_size * 0.5\n        except Exception:\n            w = len(testo) * font_size * 0.5\n        if w <= _largo or w <= 0:\n            return \'\'\n        q = max(10, int(100 * _largo / w))\n        return f"\\\\fscx{q}\\\\fscy{q}"\n\n    # Header ASS\n    ass_content = f"""[Script Info]\nTitle: Karaoke\nScriptType: v4.00+\nPlayResX: {width}\nPlayResY: {height}\nWrapStyle: 2\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: KaraokeActive,{font_name},{font_size},&H00{highlight_bgr},&H00{text_bgr},&H00000000,&H80000000,{bold},0,0,0,100,100,0,0,1,{outline_size},{shadow_size},5,10,10,10,1\nStyle: TextWhite,{font_name},{font_size},&H00{text_bgr},&H00{text_bgr},&H00000000,&H80000000,{bold},0,0,0,100,100,0,0,1,{outline_size},{shadow_size},5,10,10,10,1\nStyle: TextRed,{font_name},{font_size},&H00{highlight_bgr},&H00{highlight_bgr},&H00000000,&H80000000,{bold},0,0,0,100,100,0,0,1,{outline_size},{shadow_size},5,10,10,10,1\nStyle: YellowBar,Arial,20,&H0000FFFF,&H0000FFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"""\n    \n    total_lines = len(lines_data)\n    center_pos = num_lines // 2\n    transition_ms = 400  # durata scorrimento a nastro\n\n    for current_idx in range(total_lines):\n        if not lines_data[current_idx]:\n            continue\n\n        current_line = lines_data[current_idx]\n        start_ms = current_line[0][1]\n\n        if current_idx + 1 < total_lines and lines_data[current_idx + 1]:\n            end_ms = lines_data[current_idx + 1][0][1]\n        else:\n            end_ms = current_line[-1][1] + 5000\n\n        # ✅ Validazione: se end_ms <= start_ms, usa fallback di 3 secondi\n        if end_ms <= start_ms:\n            end_ms = start_ms + 3000\n\n        block_dur = end_ms - start_ms\n        t_ms = min(transition_ms, block_dur // 3)\n        static_end = end_ms - t_ms\n\n        st_s = self._ms_to_ass_time(start_ms)\n        st_e = self._ms_to_ass_time(static_end)\n        # ✅ tr_s 10ms DOPO static_end per evitare sovrapposizione con la statica\n        tr_s = self._ms_to_ass_time(static_end + 10)\n        # ✅ tr_e 10ms PRIMA di end_ms per evitare sovrapposizione con la statica successiva\n        tr_e = self._ms_to_ass_time(end_ms - 10)\n\n        for display_pos in range(num_lines):\n            line_offset = display_pos - center_pos\n            line_idx = current_idx + line_offset\n\n            if line_idx < 0 or line_idx >= total_lines:\n                continue\n            if not lines_data[line_idx]:\n                continue\n\n            line = lines_data[line_idx]\n            fs = _stringi(line)\n            pos_y = start_y + display_pos * line_height\n            new_y = pos_y - line_height\n\n            if line_offset == 0:\n                # ── Riga attiva: karaoke statico, poi scorre su come rossa ──\n                karaoke_text = ""\n                prev_ts = start_ms\n                for syl, ts in line:\n                    syl_clean = syl.replace(\'\\n\', \'\').replace(\'\\r\', \'\').upper()\n                    if not syl_clean:\n                        continue\n                    duration_cs = max(1, (ts - prev_ts) // 10) if ts > prev_ts else 10\n                    karaoke_text += f"{{\\\\kf{duration_cs}}}{syl_clean}"\n                    prev_ts = ts\n                ass_content += f"Dialogue: 1,{st_s},{st_e},KaraokeActive,,0,0,0,,{{{fs}\\\\pos({width//2},{pos_y})}}{karaoke_text}\\n"\n                # Transizione: diventa rossa e scorre su\n                text = \'\'.join(s.replace(\'\\n\', \'\').replace(\'\\r\', \'\').upper() for s, _ts in line)\n                ass_content += f"Dialogue: 0,{tr_s},{tr_e},TextRed,,0,0,0,,{{{fs}\\\\move({width//2},{pos_y},{width//2},{new_y})}}{text}\\n"\n\n            elif line_offset < 0:\n                # ── Righe già cantate (rosse): statiche poi scorrono su ──\n                text = \'\'.join(s.replace(\'\\n\', \'\').replace(\'\\r\', \'\').upper() for s, _ts in line)\n                ass_content += f"Dialogue: 0,{st_s},{st_e},TextRed,,0,0,0,,{{{fs}\\\\pos({width//2},{pos_y})}}{text}\\n"\n                if display_pos == 0:\n                    ass_content += f"Dialogue: 0,{tr_s},{tr_e},TextRed,,0,0,0,,{{{fs}\\\\move({width//2},{pos_y},{width//2},{new_y})\\\\fad(0,{t_ms})}}{text}\\n"\n                else:\n                    ass_content += f"Dialogue: 0,{tr_s},{tr_e},TextRed,,0,0,0,,{{{fs}\\\\move({width//2},{pos_y},{width//2},{new_y})}}{text}\\n"\n\n            else:\n                # ── Righe future (bianche): statiche poi scorrono su ──\n                text = \'\'.join(s.replace(\'\\n\', \'\').replace(\'\\r\', \'\').upper() for s, _ts in line)\n                ass_content += f"Dialogue: 0,{st_s},{st_e},TextWhite,,0,0,0,,{{{fs}\\\\pos({width//2},{pos_y})}}{text}\\n"\n                ass_content += f"Dialogue: 0,{tr_s},{tr_e},TextWhite,,0,0,0,,{{{fs}\\\\move({width//2},{pos_y},{width//2},{new_y})}}{text}\\n"\n\n        # ── Nuova riga dal basso durante la transizione ──\n        new_line_idx = current_idx + center_pos + 1\n        already_drawn = (new_line_idx - current_idx) <= (num_lines - center_pos - 1)\n        if not already_drawn and 0 <= new_line_idx < total_lines and lines_data[new_line_idx]:\n            new_line = lines_data[new_line_idx]\n            fs = _stringi(new_line)\n            text = \'\'.join(s.replace(\'\\n\', \'\').replace(\'\\r\', \'\').upper() for s, _ts in new_line)\n            bottom_y = start_y + num_lines * line_height\n            target_y = bottom_y - line_height\n            ass_content += f"Dialogue: 0,{tr_s},{tr_e},TextWhite,,0,0,0,,{{{fs}\\\\move({width//2},{bottom_y},{width//2},{target_y})\\\\fad({t_ms},0)}}{text}\\n"\n    \n    # Scrivi file\n    # ── Barra gialla durante i gap (come in KaraDom: 300x35 centrata) ──\n    bar_h = max(20, int(35 * scale_factor))\n    bar_w = max(200, int(300 * scale_factor))\n    bar_x = (width - bar_w) // 2\n    bar_y = max(3, int(5 * scale_factor))\n    container_h = bar_h + bar_y * 2\n    BS = chr(92)\n    for i in range(len(lines_data)):\n        if not lines_data[i]: continue\n        line_end_ms = lines_data[i][-1][1]\n        next_start_ms = None\n        for j in range(i+1, len(lines_data)):\n            if lines_data[j]:\n                next_start_ms = lines_data[j][0][1]\n                break\n        if next_start_ms is None: continue\n        gap = next_start_ms - line_end_ms\n        if gap < 1500: continue\n        gs = self._ms_to_ass_time(line_end_ms)\n        ge = self._ms_to_ass_time(next_start_ms)\n        dur_ms = int(gap)\n        draw_bar = f"m 0 0 l {bar_w} 0 {bar_w} {bar_h} 0 {bar_h}"\n        draw_bg = f"m 0 0 l {width} 0 {width} {container_h} 0 {container_h}"\n        # Contenitore nero pieno\n        ass_content += f"Dialogue: 1,{gs},{ge},YellowBar,,0,0,0,,{{{BS}pos(0,0){BS}p1{BS}bord0{BS}shad0{BS}1c&H000000&{BS}fad(200,200)}}{draw_bg}\\n"\n        # Sfondo grigio centrato\n        ass_content += f"Dialogue: 2,{gs},{ge},YellowBar,,0,0,0,,{{{BS}pos({bar_x},{bar_y}){BS}p1{BS}bord0{BS}shad0{BS}1c&H333333&{BS}fad(200,200)}}{draw_bar}\\n"\n        # Barra gialla che si svuota da dx a sx\n        ass_content += f"Dialogue: 3,{gs},{ge},YellowBar,,0,0,0,,{{{BS}pos({bar_x},{bar_y}){BS}p1{BS}bord0{BS}shad0{BS}1c&H00FFFF&{BS}fad(200,0){BS}clip({bar_x},0,{bar_x+bar_w},{container_h}){BS}t(0,{dur_ms},{BS}clip({bar_x},0,{bar_x},{container_h}))}}{draw_bar}\\n"\n\n    with open(filepath, \'w\', encoding=\'utf-8\') as f:\n        f.write(ass_content)\n'
_MISURA = 'def _misura_monitor(self):\n    """Misure del riquadro video del monitor di KaraDom (pari, come vuole x264) nel preset\n    \'Come il monitor di KaraDom\'. Se non si riesce a misurare restano 1920x1080."""\n    p = PRESETS.get(\'monitor_karadom\')\n    if not p:\n        return\n    try:\n        box = self.system.monitor.center_container\n        box.update_idletasks()\n        w, h = int(box.winfo_width()), int(box.winfo_height())\n        if w >= 320 and h >= 180:\n            if w > 3840:\n                w, h = 3840, int(h * 3840 / w)\n            p[\'width\'], p[\'height\'] = w // 2 * 2, h // 2 * 2\n    except Exception:\n        pass\n    p[\'description\'] = \'Riempie il monitor di KaraDom: %dx%d (per YouTube meglio 1080p)\' % (p[\'width\'], p[\'height\'])\n'
_PRESET = {'name': 'Come il monitor di KaraDom', 'width': 1920, 'height': 1080, 'fps': 30, 'video_bitrate': '8M', 'audio_bitrate': '320k', 'description': 'Riempie il monitor di KaraDom (per YouTube meglio 1080p)'}


def _ui(self):
    """Dopo la finestra: dimensioni fino a 144 e casella Grassetto accanto a Righe."""
    import tkinter as tk
    from tkinter import ttk
    import moduli.convertitore as mc
    try:
        self.saved_bold = mc.Database.get_config('converter_bold', '1')
    except Exception:
        self.saved_bold = '1'
    self.bold_var = tk.BooleanVar(value=str(self.saved_bold) != '0')
    righe = None

    def giro(w):
        nonlocal righe
        for c in w.winfo_children():
            if isinstance(c, ttk.Combobox):
                tv = str(c.cget('textvariable'))
                if tv == str(self.font_size_var):
                    c.configure(values=['Auto'] + [str(n) for n in range(36, 146, 2)])
                elif tv == str(self.lines_var):
                    righe = c
            giro(c)
    giro(self.window)
    if righe is None:
        return
    try:
        _t = mc._
    except Exception:
        _t = lambda s: s
    tk.Checkbutton(righe.master, text=_t("Grassetto"), variable=self.bold_var,
                   bg='#1a1a1a', fg='white', selectcolor='#333333', activebackground='#1a1a1a',
                   activeforeground='white', font=mc.F('Arial', 10, 'bold'),
                   command=lambda: self._save_setting('converter_bold', '1' if self.bold_var.get() else '0')
                   ).pack(side='left', padx=(mc.S(15), mc.S(0)))



def _titolare():
    """[26-10-2026] Solo sui PC del titolare (licenza Domenico Lembo), come 239/242/245-249."""
    try:
        from moduli.licensing import load_license
        d = load_license() or {}
        return (str(d.get('nome', '')).strip().lower(),
                str(d.get('cognome', '')).strip().lower()) == ('domenico', 'lembo')
    except Exception:
        return False


def apply():
    if not _titolare():
        return False
    try:
        import moduli.convertitore as mc
        C = mc.ConvertitoreKaraoke
        if getattr(C, '_ver237', None) == _VER:
            return True
        ui0 = getattr(C, '_o237_ui', None) or C._create_ui
        C._o237_ui = ui0
        sel0 = getattr(C, '_o237_sel', None) or C._on_preset_selected
        C._o237_sel = sel0
        vai0 = getattr(C, '_o237_vai', None) or C._start_conversion
        C._o237_vai = vai0
        ns = dict(vars(mc))
        exec(_ASS, ns)
        exec(_MISURA, ns)
        mc.PRESETS.setdefault('monitor_karadom', dict(_PRESET))

        def _create_ui(self, *a, **k):
            r = ui0(self, *a, **k)
            try:
                _ui(self)
            except Exception as e:
                print('[237] %s' % e)
            return r

        def _on_preset_selected(self, *a, **k):
            try:
                self._misura_monitor()
            except Exception:
                pass
            return sel0(self, *a, **k)

        def _start_conversion(self, *a, **k):
            try:
                self._misura_monitor()
            except Exception:
                pass
            return vai0(self, *a, **k)

        C._create_ui = _create_ui
        C._on_preset_selected = _on_preset_selected
        C._start_conversion = _start_conversion
        C._misura_monitor = ns['_misura_monitor']
        C._generate_ass_file = ns['_generate_ass_file']
        C._ver237 = _VER
        print('[237] convertitore: righe piu vicine, grassetto, carattere fino a 144, come il monitor')
        return True
    except Exception as e:
        print('[237] %s' % e)
        return False
