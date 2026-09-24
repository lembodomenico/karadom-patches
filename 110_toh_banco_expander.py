import os


def _dest_dir():
    d = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'KaraDom', 'dipendenze', 'Expander')
    os.makedirs(d, exist_ok=True)
    return d


# file locale gia' scaricato (PC di Domenico); se manca, si scarica da Archive
_SRC_LOCALE = r"C:\Users\lembo\Desktop\Banchi\Timbres of Heaven (XGM) 4.00(G).sf2"
_URL = ("https://github.com/lembodomenico/karadom-patches/releases/download/"
        "banchi-v1/Timbres_of_Heaven.sf2")
_MIN_OK = 180 * 1024 * 1024   # un banco ToH valido e' > 180 MB


def _scarica(url, dest):
    import urllib.request
    tmp = dest + '.parte'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=60) as r, open(tmp, 'wb') as f:
        while True:
            blocco = r.read(1024 * 512)
            if not blocco:
                break
            f.write(blocco)
    os.replace(tmp, dest)


def _aggancia(dest):
    try:
        from moduli.database import Database
        Database.set_config('exp_banco_path', dest)
        print('[TOH110] ToH agganciata all Expander Software:', dest)
    except Exception as e:
        print('[TOH110] set_config:', e)


def _scarica_e_aggancia(dest):
    # gira in un THREAD a parte: NON deve bloccare l'avvio di KaraDom
    try:
        print('[TOH110] scarico la ToH in background da GitHub...')
        _scarica(_URL, dest)
        if os.path.isfile(dest) and os.path.getsize(dest) >= _MIN_OK:
            print('[TOH110] ToH scaricata (%d MB)' % (os.path.getsize(dest) // (1024 * 1024)))
            _aggancia(dest)
    except Exception as e:
        print('[TOH110] download in background:', e)


def apply():
    dest = os.path.join(_dest_dir(), 'Timbres_of_Heaven.sf2')
    try:
        # 1) gia' presente (copiata o scaricata prima): aggancio SUBITO
        if os.path.isfile(dest) and os.path.getsize(dest) >= _MIN_OK:
            _aggancia(dest)
            return True
        # 2) copia locale (PC di Domenico): veloce, sincrona
        if os.path.isfile(_SRC_LOCALE) and os.path.getsize(_SRC_LOCALE) >= _MIN_OK:
            import shutil
            shutil.copy2(_SRC_LOCALE, dest)
            print('[TOH110] ToH copiata nella cartella Expander')
            _aggancia(dest)
            return True
        # 3) client: download in BACKGROUND (l'avvio NON si blocca; il banco si
        #    aggancia appena finito, pronto dal brano/avvio successivo)
        import threading
        threading.Thread(target=_scarica_e_aggancia, args=(dest,), daemon=True).start()
        print('[TOH110] banco assente: scarico in background, avvio non bloccato')
        return True
    except Exception as e:
        print('[TOH110] errore:', e)
        return False


try:
    apply()
except Exception as _e:
    print('patch 110: %s' % _e)
