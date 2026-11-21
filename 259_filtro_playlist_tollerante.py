# 259 - filtro playlist tollerante

import re
import unicodedata

_VER = 3


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_259', '1')).strip() in ('0', 'no', 'off')
    except Exception:
        return False


def _parole(s):
    s = unicodedata.normalize('NFD', str(s or '').lower())
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.findall(r'[a-z0-9]+', s)


def _pezzi(filtro):
    if '*' in filtro:
        grezzi = [p for p in filtro.split('*') if p.strip()]
    else:
        grezzi = [p for p in re.split(r'\s+', filtro) if p]
    fuori = []
    for g in grezzi:
        w = _parole(g)
        if w:
            fuori.append(w)
    return fuori


def _combacia(pezzi, testo):
    w = _parole(testo)
    norm = ' ' + ' '.join(w) + ' '
    unito = ''.join(w)
    for p in pezzi:
        frase = ' '.join(p)
        if len(frase) == 1:
            if (' %s' % frase) not in norm:
                return False
        elif frase not in norm and not (len(frase) >= 4 and ''.join(p) in unito):
            return False
    return True


def filtra_playlist_lista(self, event=None):
    filtro = self.entry_filtro_playlist.get().strip().lower()
    pezzi = [] if filtro in ("filtra playlist...", "") else _pezzi(filtro)
    if not pezzi:
        self.playlist_data_filtered = self.playlist_data.copy()
    else:
        self.playlist_data_filtered = [p for p in self.playlist_data if _combacia(pezzi, p['nome'])]
    self._aggiorna_listbox_playlist()


def _richiesta_in_corso():
    import sys
    try:
        fr = sys._getframe(2)
    except Exception:
        return None
    visto = False
    for _ in range(6):
        if fr is None:
            return None
        nome = fr.f_code.co_name
        if nome == '_prova_playlist':
            visto = True
        elif nome == '_on_sel' and visto:
            loc = fr.f_locals
            if 'brano' in loc and 'artista' in loc:
                return loc.get('brano'), loc.get('artista')
            return None
        fr = fr.f_back
    return None


def _applica(self, pezzi):
    visibili = 0
    for row in self._pl_rows:
        ok = (not pezzi) or _combacia(pezzi, row['search_key'])
        if ok:
            visibili += 1
        if ok and not row['visible']:
            self._pl_tree.reattach(row['iid'], '', 'end')
            row['visible'] = True
        elif not ok and row['visible']:
            self._pl_tree.detach(row['iid'])
            row['visible'] = False
    return visibili


def _scrivi(entry, testo):
    try:
        entry.delete(0, 'end')
        entry.insert(0, testo)
        entry.config(fg='white')
    except Exception:
        pass


def _ridisegna_dopo(self):
    def fai():
        try:
            self._pl_redraw_buttons()
        except Exception:
            pass
    for ms in (60, 250, 700):
        try:
            self.parent.after(ms, fai)
        except Exception:
            pass


def filtra_brani_playlist(self, event=None):
    if not hasattr(self, '_pl_rows') or not self._pl_rows:
        return
    if not hasattr(self, '_pl_tree'):
        return
    dati = _richiesta_in_corso()
    if dati:
        brano, artista = (str(x or '').strip() for x in dati)
        con_artista = ('%s %s' % (brano, artista)).strip()
        _scrivi(self.entry_filtro_brani_pl, con_artista)
        if _applica(self, _pezzi(con_artista.lower())) == 0 and artista:
            _scrivi(self.entry_filtro_brani_pl, brano)
            _applica(self, _pezzi(brano.lower()))
        self._pl_redraw_buttons()
        _ridisegna_dopo(self)
        return
    filtro = self.entry_filtro_brani_pl.get().strip().lower()
    pezzi = [] if filtro in ("filtra brani...", "") else _pezzi(filtro)
    _applica(self, pezzi)
    self._pl_redraw_buttons()


def apply():
    if _spenta():
        return False
    try:
        import moduli.libreria_playlist_mixin as PL
    except Exception:
        return False
    C = getattr(PL, 'LibreriaPlaylistMixin', None)
    if C is None or not hasattr(C, 'filtra_brani_playlist'):
        return False
    classi = [C]
    try:
        import moduli.libreria as lib
        S = getattr(lib, 'LibreriaSlider', None)
        if S is not None and ('filtra_brani_playlist' in S.__dict__ or 'filtra_playlist_lista' in S.__dict__):
            classi.append(S)
    except Exception:
        pass
    for K in classi:
        if getattr(K, '_ver259', None) == _VER:
            continue
        K.filtra_playlist_lista = filtra_playlist_lista
        K.filtra_brani_playlist = filtra_brani_playlist
        K._ver259 = _VER
    print('[259] filtro playlist: accenti, apostrofi e ordine delle parole ignorati')
    return True


def revert():
    return False


try:
    apply()
except Exception as _e:
    print('[259] %s' % _e)
