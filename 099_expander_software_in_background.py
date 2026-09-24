# 099 - Expander software: all'avvio parte la porta MIDI (loopMIDI) e l'expander software, senza aprirli a mano
def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_099', '1')) == '0'
    except Exception:
        return False


def _socket_on():
    # col socket (patch 104) loopMIDI NON serve: niente avvio loopMIDI ne' porta.
    try:
        from moduli.database import Database
        return str(Database.get_config('expander_socket', '0')) == '1'
    except Exception:
        return False


def _percorso_exe():
    import os
    base = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'KaraDom', 'dipendenze', 'Expander')
    return os.path.join(base, 'KaraDom Expander.exe')


def _percorso_loopmidi():
    import os
    exp = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'KaraDom', 'dipendenze', 'Expander', 'loopMIDI.exe')
    pf = os.environ.get('PROGRAMFILES', r'C:\Program Files')
    for p in (exp,   # loopMIDI portatile dentro la cartella Expander (niente admin)
              r'C:\Program Files\KaraDom\soundfonts\loopMIDI.exe',
              os.path.join(pf, 'KaraDom', 'soundfonts', 'loopMIDI.exe'),
              os.path.join(pf, 'Tobias Erichsen', 'loopMIDI', 'loopMIDI.exe')):
        if os.path.exists(p):
            return p
    return ''


def _in_esecuzione(nome_exe):
    import subprocess
    try:
        out = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq %s' % nome_exe],
                             capture_output=True, text=True, timeout=4, creationflags=0x08000000)
        return nome_exe.lower() in (out.stdout or '').lower()
    except Exception:
        return False


def _assicura_porta_registro():
    if _socket_on():
        return
    # loopMIDI crea le porte dall'elenco nel registro. Se non c'e' "loopMIDI Port"
    # la aggiungo: cosi' all'avvio loopMIDI crea la porta da sola (verificato).
    try:
        import winreg
        k = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER,
                               r'Software\Tobias Erichsen\loopMIDI\Ports', 0, winreg.KEY_ALL_ACCESS)
        try:
            winreg.QueryValueEx(k, 'loopMIDI Port')
        except FileNotFoundError:
            winreg.SetValueEx(k, 'loopMIDI Port', 0, winreg.REG_SZ, '')
            print('[EXP] porta "loopMIDI Port" registrata in loopMIDI')
        winreg.CloseKey(k)
        # loopMIDI deve partire MINIMIZZATO nel tray, non con la finestra aperta
        k2 = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER,
                                r'Software\Tobias Erichsen\loopMIDI', 0, winreg.KEY_ALL_ACCESS)
        winreg.SetValueEx(k2, 'StartMinimized', 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(k2)
    except Exception as e:
        print('[EXP] registro loopMIDI:', e)


def _avvia_loopmidi():
    import os, subprocess
    if _socket_on():
        return True   # col socket loopMIDI non serve: non lo avvio
    exe = _percorso_loopmidi()
    if not exe:
        print('[EXP] loopMIDI.exe non trovato')
        return False
    _assicura_porta_registro()
    if _in_esecuzione('loopMIDI.exe'):
        return True
    try:
        subprocess.Popen([exe], creationflags=0x08000000 | 0x00000008, close_fds=True)
        print('[EXP] loopMIDI avviato (porta MIDI virtuale pronta)')
        return True
    except Exception as e:
        print('[EXP] avvio loopMIDI fallito:', e)
        return False


import threading as _threading
_LANCIA_LOCK = _threading.Lock()


def _avvia_expander(port_name):
    import os, subprocess
    if _socket_on():
        return True   # in-process (patch 104): l'exe NON serve, non lo avvio -> niente finestre
    exe = _percorso_exe()
    if not os.path.exists(exe):
        print('[EXP] expander software non installato:', exe)
        return False
    # ⛔ MAI due volte: la 099 chiama _avvia_expander sia all'avvio sia alla prima
    #    riproduzione; con tasklist lento c'era una corsa -> due istanze. Lucchetto
    #    + flag di sessione chiudono la finestra di corsa.
    with _LANCIA_LOCK:
        if globals().get('_exp_lanciato_099'):
            return True
        if _in_esecuzione('KaraDom Expander.exe'):
            globals()['_exp_lanciato_099'] = True
            return True
        try:
            subprocess.Popen([exe, '--hidden', '--port', port_name or 'loopMIDI'],
                             creationflags=0x08000000 | 0x00000008, close_fds=True)
            globals()['_exp_lanciato_099'] = True
            print('[EXP] expander software avviato in background su', port_name or 'loopMIDI')
            return True
        except Exception as e:
            print('[EXP] avvio expander software fallito:', e)
            return False


def _assicura_banco():
    # l'exe expander carica il banco da expander.cfg (ultimo scelto). Se il cfg e'
    # vuoto/assente, punta a un file che non c'e', o punta al "KaraDom HD" (che e'
    # solo un RIPIEGO), lo porto sul banco DEDICATO (banco_toh.sf3 / primo *.sf3):
    # cosi' l'expander suona col ToH senza dover ricompilare. NON tocca una scelta
    # deliberata di un altro banco (resta com'e').
    import os, glob
    base = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'KaraDom', 'dipendenze', 'Expander')
    ded = ''
    for c in (os.path.join(base, 'banco_toh.sf3'),
              os.path.join(base, 'banco.sf3'),
              os.path.join(base, 'banco.sf2')):
        if os.path.exists(c):
            ded = c
            break
    if not ded:
        s = sorted(glob.glob(os.path.join(base, '*.sf3')))
        if s:
            ded = s[0]
    if not ded:
        return
    cfg = os.path.join(base, 'expander.cfg')
    attuale = ''
    try:
        if os.path.exists(cfg):
            attuale = open(cfg, encoding='utf-8').read().strip()
    except Exception:
        attuale = ''
    if (not attuale) or (not os.path.exists(attuale)) or ('karadom hd' in attuale.lower()):
        try:
            with open(cfg, 'w', encoding='utf-8') as f:
                f.write(ded)
            print('[EXP] banco expander impostato su', os.path.basename(ded))
        except Exception as e:
            print('[EXP] cfg banco:', e)


def _e_software(nome):
    n = (nome or '').lower()
    return ('loopmidi' in n) or ('loop midi' in n)


def _software_predefinito(mod):
    # Deve essere disponibile l'expander software (loopMIDI) ogni volta che
    # l'expander non e' spento: in 'auto' fa da default se non c'e' l'HW, e non
    # da' fastidio se l'HW c'e' (l'auto sceglie l'HW). In 'off' niente.
    try:
        return mod.get_mode() != 'off'
    except Exception:
        return True


def _imposta_default_software(mod):
    # Default = 'auto'. Con loopMIDI a punteggio da expander (40) e l'HW a 100/50,
    # in 'auto': se c'e' un expander FISICO vince lui; se non c'e', usa il software
    # (loopMIDI); 'off' = SoundFont interno. NON si forza 'on' (bloccherebbe la
    # porta software ignorando un HW collegato).
    try:
        m = mod.get_mode()
        port = str(mod._cfg(mod.CFG_PORT, '')).strip().lower()
        # correggo il vecchio forzamento 'on'+loopMIDI -> torno ad 'auto'
        if m == 'on' and ('loop' in port):
            mod.set_mode('auto')
            print('[EXP] default riportato ad AUTO (l\'HW vince se collegato)')
    except Exception as e:
        print('[EXP] default auto non impostato:', e)


def apply():
    if _spenta():
        return False
    import os, sys
    # ⛔ SICUREZZA: questa patch e' per chi ha l'EXPANDER SOFTWARE installato.
    #    Se l'exe non c'e' (client normali), NON si fa nulla: niente riscansioni,
    #    niente registro, niente avvii. Cosi' e' innocua ovunque.
    if not os.path.exists(_percorso_exe()):
        return False
    mod = sys.modules.get('moduli.expander_midi')
    if mod is None:
        try:
            import moduli.expander_midi as mod  # noqa
        except Exception:
            print('patch 099: expander_midi non presente (ok)')
            return False

    # ⭐ loopMIDI = il NOSTRO expander software. Di default ('auto') KaraDom lo
    #    scartava (loopback, punteggio 0). Qui gli do' un punteggio da expander,
    #    piu' basso di un HW vero (100/50): cosi' in 'auto' se c'e' loopMIDI usa
    #    il software, e un expander hardware collegato vince comunque.
    if not getattr(mod, '_punt_loop_099', False):
        _op = mod._punteggio
        def _punteggio(nome):
            n = (nome or '').lower()
            if 'loopmidi' in n or 'loop midi' in n:
                return 40
            return _op(nome)
        _punteggio._orig = _op
        mod._punteggio = _punteggio
        mod._punt_loop_099 = True
        print('[EXP] loopMIDI ora conta come expander in Automatico')

    _imposta_default_software(mod)
    _assicura_banco()  # l'expander deve caricare il banco dedicato (ToH), non il KaraDom HD

    # ⭐ AL PRIMISSIMO CARICAMENTO: se l'expander software e' il predefinito,
    #    accendi SUBITO la porta virtuale (loopMIDI) e l'expander in background.
    def _commuta_a_caldo():
        # se un brano MIDI sta gia' suonando, lo ricarica SUBITO sull'expander
        # (non al brano dopo). Gira sul thread UI.
        try:
            main = sys.modules.get('__main__')
            sysobj = getattr(main, '_app_system', None)
            root = getattr(main, '_app_root', None)
            if not (sysobj and root):
                return
            if not (getattr(sysobj, 'is_midi', False) and getattr(sysobj, 'is_playing', False)):
                return
            cf = getattr(sysobj, 'current_file', None)
            if not cf:
                return

            def _hot():
                try:
                    ton = getattr(sysobj, 'current_pitch', 0) or 0
                    try:
                        pos = int(sysobj.get_current_position_ms() or 0)
                    except Exception:
                        pos = 0
                    sysobj.stop()
                    try:
                        ok = sysobj.load_file(cf, ton)
                    except TypeError:
                        ok = sysobj.load_file(cf)
                    if ok:
                        sysobj.play()
                        if pos > 500:
                            sysobj.seek_to(pos)
                    print('[EXP] brano commutato a caldo sull\'expander')
                except Exception as e:
                    print('[EXP] commuta a caldo:', e)
            root.after(0, _hot)
        except Exception:
            pass

    if _software_predefinito(mod):
        _avvia_loopmidi()

        def _aggancia():
            # aspetta che loopMIDI crei la porta, poi avvia l'expander, riscandisce
            # (la 062 cachea le porte all'avvio) e — se serve — commuta a caldo SUBITO.
            import time
            _avvia_expander('loopMIDI')
            for _ in range(20):   # ~10s max
                try:
                    if hasattr(mod, 'rileva_porte_forza'):
                        mod.rileva_porte_forza()
                    p = mod.detect_expander()
                    nome = (p.get('nome') if isinstance(p, dict) else None) or ''
                    if 'loop' in nome.lower():
                        break
                except Exception:
                    pass
                time.sleep(0.5)
            try:
                mod.reset_player()
            except Exception:
                pass
            # PRE-WARM: creo subito il player (se non c'e' HW/off) cosi' l'expander
            # e' ATTIVO gia' all'avvio e il mixer mostra EXPANDER (non "SF:").
            try:
                pl = mod.get_expander_player()
                print('[EXP] pre-warm player:', type(pl).__name__ if pl else None,
                      '| active=', mod.is_active())
            except Exception as e:
                print('[EXP] pre-warm err:', e)
            # aggiorna l'etichetta del mixer (SF -> EXPANDER): e' un singleton
            try:
                import moduli.mixer as _mx
                inst = _mx.MIDIMixerPanel.get_instance() if hasattr(_mx.MIDIMixerPanel, 'get_instance') else None
                root = getattr(sys.modules.get('__main__'), '_app_root', None)
                if inst is not None and root is not None and hasattr(inst, '_update_soundfont_display'):
                    root.after(0, inst._update_soundfont_display)
            except Exception:
                pass
            _commuta_a_caldo()
            print('[EXP] expander software agganciato (immediato)')
        try:
            import threading
            threading.Thread(target=_aggancia, daemon=True, name='exp_aggancia_099').start()
        except Exception:
            _aggancia()

    if getattr(mod, '_bg_099', False):
        return True
    _orig = getattr(mod, 'get_expander_player', None)
    if _orig is None:
        return True

    def get_expander_player():
        # rete di sicurezza AL PLAY: assicura loopMIDI e FORZA la riscansione
        # porte finche' non trova quella software (la 062 le cachea all'avvio,
        # quando loopMIDI non c'era ancora). Trovata una volta, smette di forzare.
        try:
            if mod.get_mode() != 'off':
                if _software_predefinito(mod):
                    _avvia_loopmidi()
                if not getattr(mod, '_soft_trovata_099', False):
                    try:
                        if hasattr(mod, 'rileva_porte_forza'):
                            mod.rileva_porte_forza()
                    except Exception:
                        pass
                porta = mod.detect_expander()
                nome = porta.get('nome') if isinstance(porta, dict) else None
                if nome and _e_software(nome):
                    mod._soft_trovata_099 = True
                    _avvia_loopmidi()
                    _avvia_expander(nome)
        except Exception as e:
            print('[EXP] check software expander:', e)
        return _orig()

    get_expander_player._orig_099 = _orig
    mod.get_expander_player = get_expander_player
    mod._bg_099 = True

    # spia su file: dopo ~5s scrive cosa vede (per diagnosi senza indovinare)
    def _spia():
        import time, os, datetime
        time.sleep(5)
        try:
            d = mod.detect_expander()
            base = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'KaraDom', 'dipendenze', 'Expander')
            os.makedirs(base, exist_ok=True)
            # PROVA VERA: crea il player come al play
            ptxt = 'n/d'
            try:
                p = mod.get_expander_player()
                ptxt = '%s init=%s porta=%s err=%s' % (
                    type(p).__name__ if p else None,
                    getattr(p, 'initialized', None) if p else None,
                    getattr(p, 'nome_porta', None) if p else None,
                    getattr(p, '_ultimo_errore', '') if p else '')
            except Exception as ge:
                ptxt = 'get_expander_player EXCEPTION: %s' % ge
            with open(os.path.join(base, '099_spia.txt'), 'w', encoding='utf-8') as f:
                f.write('%s\nmode=%s\ncfg_port=%r\ndetect=%r\nis_active=%s\nget_player=%s\nports=%r\n' % (
                    datetime.datetime.now().isoformat(), mod.get_mode(),
                    mod._cfg(mod.CFG_PORT, ''), d, mod.is_active(), ptxt,
                    [(p2['nome'], p2['punteggio']) for p2 in mod.list_ports()]))
        except Exception as e:
            try:
                with open(os.path.join(base, '099_spia.txt'), 'w', encoding='utf-8') as f:
                    f.write('spia err: %s' % e)
            except Exception:
                pass
    try:
        import threading
        threading.Thread(target=_spia, daemon=True, name='exp_spia_099').start()
    except Exception:
        pass

    print('[EXP] patch 099: loopMIDI + expander software all\'avvio quando l\'interno e\' predefinito')
    return True


def revert():
    try:
        import sys
        mod = sys.modules.get('moduli.expander_midi')
        if mod is not None:
            o = getattr(getattr(mod, 'get_expander_player', None), '_orig_099', None)
            if o is not None:
                mod.get_expander_player = o
            if hasattr(mod, '_bg_099'):
                del mod._bg_099
    except Exception:
        pass


try:
    apply()
except Exception as _e:
    print('patch 099: %s' % _e)
