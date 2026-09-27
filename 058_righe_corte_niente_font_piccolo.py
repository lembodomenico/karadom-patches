# 058 - Righe lunghe (MIDI e non) spezzate in PIU' righe corte: il testo non si rimpicciolisce piu'
def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_058', '1')) == '0'
    except Exception:
        return False


def _wrap(full_text, maxch=34):
    out = []
    for line in (full_text or '').split('\n'):
        words = line.split()
        if not words:
            out.append(line)
            continue
        # riga gia' corta: lasciala com'e'
        if len(line) <= maxch and len(words) < 8:
            out.append(line)
            continue
        cur = ""
        for w in words:
            if cur and (len(cur) + 1 + len(w)) > maxch:
                out.append(cur)
                cur = w
            else:
                cur = (cur + " " + w) if cur else w
        if cur:
            out.append(cur)
    return '\n'.join(out)


def apply():
    if _spenta():
        return False
    try:
        from moduli.engine import KaraokeTextEngine as C
    except Exception as _e:
        print('patch 058: no engine %s' % _e)
        return False
    if hasattr(C, '_split_long_lines') and not hasattr(C, '_orig_058_split'):
        C._orig_058_split = C._split_long_lines

        def _split_long_lines(self, maxch=34):
            try:
                self.full_text = _wrap(getattr(self, 'full_text', '') or '', maxch)
            except Exception:
                try:
                    return C._orig_058_split(self)
                except Exception:
                    pass

        C._split_long_lines = _split_long_lines
    return True


def revert():
    try:
        from moduli.engine import KaraokeTextEngine as C
        if hasattr(C, '_orig_058_split'):
            C._split_long_lines = C._orig_058_split
            del C._orig_058_split
    except Exception:
        pass


try:
    apply()
except Exception as _e:
    print('patch 058: %s' % _e)
