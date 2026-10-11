# 211 - patch all'avvio: si scaricano solo quelle cambiate (impronta nel manifest)

_VER = 1


# [11-10-2026] estesa a TUTTI i PC (prima solo quelli del gestore)
SOLO_SERIALI = ('1A55-2CD1-3303-20EB', '64D4-81C3-65D3-C024', '0182-5846-232C-930E', '4D8E-F63F-45E1-8F06')


def _pc_del_gestore():
    import sys
    gia = getattr(sys, '_kd_pc_del_gestore', None)
    if gia is None:
        try:
            from moduli.licensing import get_hardware_id, generate_serial
            c, m = get_hardware_id()
            gia = generate_serial(c, m) in SOLO_SERIALI
        except Exception:
            gia = False
        sys._kd_pc_del_gestore = gia
    return gia


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_211', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def apply():
    """Prima: a ogni avvio si scaricavano TUTTE le patch con la loro firma (~270 richieste, ~2 MB)
    e solo dopo si confrontavano con quelle sul disco; 8 secondi dopo la 002 rifaceva tutto.
    Ora il manifest porta l'impronta (sha256) di ogni patch: si scaricano solo quelle diverse
    o nuove, e il secondo giro, se GitHub e' allo stesso commit gia' controllato, si ferma
    subito. Manifest vecchio senza impronte = si fa come prima."""
    if _spenta():
        return False
    import hashlib
    import json
    import os
    import threading
    import urllib.request
    try:
        import moduli.updater as up
    except Exception:
        return False
    if getattr(up, '_ver211', None) == _VER:
        return True

    stato = {'base_fatta': None}
    blocco = threading.Lock()
    INTESTAZIONI = {'User-Agent': 'KaraDom Pro Updater', 'Cache-Control': 'no-cache', 'Pragma': 'no-cache'}

    def _impronta_locale(percorso):
        try:
            return hashlib.sha256(open(percorso, 'rb').read()).hexdigest()[:16]
        except Exception:
            return None

    def aggiorna_set():
        """Scarica le patch cambiate. Ritorna l'elenco dei file NUOVI (sul disco non c'erano)."""
        nuove = []
        with blocco:                      # avvio e controllo dopo 8 s non lavorano insieme
            try:
                if not up._is_online():
                    return nuove
                try:
                    from moduli.hotfix import patches_dir, _verify
                except Exception:
                    from hotfix import patches_dir, _verify
                d = patches_dir()
                base = up._base_patches()
                if base == stato['base_fatta'] and not base.endswith('/main'):
                    return nuove          # stesso commit gia' controllato in questa sessione
                try:
                    req = urllib.request.Request(base + '/manifest.json', headers=INTESTAZIONI)
                    with urllib.request.urlopen(req, timeout=15) as resp:
                        manifest = json.loads(resp.read().decode('utf-8'))
                except Exception as e:
                    print('⚠️ patch: manifest non raggiungibile (%s)' % e)
                    return nuove
                impronte = manifest.get('hash') or {}
                elenco = [str(n) for n in (manifest.get('patches') or []) if str(n).endswith('.py')]
                attesi = set()
                scaricate = 0
                for nome in elenco:
                    attesi.add(nome)
                    attesi.add(nome + '.sig')
                    try:
                        dest = os.path.join(d, nome)
                        c_era = os.path.exists(dest)
                        if c_era and os.path.exists(dest + '.sig') and nome in impronte \
                                and _impronta_locale(dest) == str(impronte[nome])[:16]:
                            continue      # uguale a quella pubblicata: niente rete
                        scaricate += 1
                        py = up._scarica(base + '/' + nome)
                        sig = up._scarica(base + '/' + nome + '.sig')
                        if py is None or sig is None:
                            continue
                        if not _verify(py, sig):
                            print('⚠️ patch %s: firma NON valida -> non salvata' % nome)
                            continue
                        if c_era and open(dest, 'rb').read() == py:
                            continue
                        open(dest, 'wb').write(py)
                        open(dest + '.sig', 'wb').write(sig)
                        print('🩹 patch aggiornata: %s' % nome)
                        if not c_era:
                            nuove.append(dest)
                    except Exception as e:
                        print('⚠️ patch %s: errore (%s)' % (nome, e))
                if impronte:
                    print('[211] patch: %d da scaricare su %d (le altre gia\' uguali)' % (scaricate, len(elenco)))
                # ritiro: via i file locali non piu' nel manifest (le prove locali .prova restano)
                try:
                    for f in os.listdir(d):
                        if not (f.endswith('.py') or f.endswith('.py.sig')) or f in attesi:
                            continue
                        b = f[:-4] if f.endswith('.py.sig') else f
                        if os.path.exists(os.path.join(d, b + '.prova')):
                            continue
                        try:
                            os.remove(os.path.join(d, f))
                            print('🧹 patch rimossa (ritirata): %s' % f)
                        except Exception as e:
                            print('⚠️ non rimossa: %s (%s)' % (f, e))
                except Exception:
                    pass
                if not base.endswith('/main'):
                    stato['base_fatta'] = base
            except Exception as e:
                print('⚠️ Controllo patch errore: %s' % e)
        return nuove

    def _applica(percorso):
        f = getattr(up, 'apply_one_hot', None)          # quella della 002 (non riapplica le attive)
        if f is None:
            try:
                from moduli.hotfix import apply_one as f
            except Exception:
                return
        try:
            f(percorso)
        except Exception as e:
            print('⚠️ patch %s: non applicata a caldo (%s)' % (os.path.basename(percorso), e))

    def check_and_update_patches(parent_window=None):
        def _lavoro():
            for p in aggiorna_set():
                _applica(p)
        threading.Thread(target=_lavoro, daemon=True, name='PatchUpdater').start()

    up.scarica_patch_adesso = aggiorna_set
    up.check_and_update_patches = check_and_update_patches
    up._ver211 = _VER
    print('[211] patch: si scaricano solo quelle cambiate')
    return True


def revert():
    return False


try:
    apply()
except Exception:
    pass
