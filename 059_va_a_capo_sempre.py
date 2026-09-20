# 059 - Il testo va SEMPRE a capo (anche all'avvio): niente piu' righe uniche col font rimpicciolito
def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_059', '1')) == '0'
    except Exception:
        return False


def apply():
    if _spenta():
        return False
    try:
        from moduli.monitor import KaraokeMonitor as C
    except Exception as _e:
        print('patch 059: no monitor %s' % _e)
        return False
    if hasattr(C, '_rewrap_syllables') and not hasattr(C, '_orig_059_rewrap'):
        C._orig_059_rewrap = C._rewrap_syllables

        def _rewrap_syllables(self, syllables, _orig=C._orig_059_rewrap):
            res = _orig(self, syllables)
            try:
                import tkinter.font as tkFont
                f = tkFont.Font(family=self.font_family, size=self.font_size, weight='bold')
                cw = 0
                try:
                    cw = self.center_container.winfo_width()
                except Exception:
                    cw = 0
                if cw <= 200:
                    # contenitore non ancora dimensionato: ripiego sullo SCHERMO,
                    # cosi' l'a-capo avviene comunque (era il caso all'avvio)
                    try:
                        cw = self.text_widget.winfo_screenwidth()
                    except Exception:
                        cw = 0
                maxw = cw - (getattr(self, 'text_padx', 0) * 2) - 20
                if maxw < 200:
                    return res
                result = [list(s) for s in res]

                def build_lines():
                    lines = []
                    cur = ""
                    sp = []
                    for i, (syl, _) in enumerate(result):
                        if '\n' in syl:
                            parts = syl.split('\n')
                            cur += parts[0]
                            lines.append((cur, sp))
                            cur = parts[-1]
                            sp = []
                            if parts[-1].endswith(' '):
                                sp.append(i)
                        else:
                            cur += syl
                            if syl.endswith(' '):
                                sp.append(i)
                    lines.append((cur, sp))
                    return lines

                for _ in range(40):
                    done = False
                    for text, idxs in build_lines():
                        if f.measure(text.rstrip()) <= maxw:
                            continue
                        if not idxs:
                            continue
                        at = idxs[len(idxs) // 2]
                        old = result[at][0]
                        s2 = old.rstrip(' ')
                        if len(s2) < len(old):
                            result[at][0] = s2 + '\n' + old[len(s2) + 1:]
                            done = True
                            break
                    if not done:
                        break
                return [(r[0], r[1]) for r in result]
            except Exception:
                return res

        C._rewrap_syllables = _rewrap_syllables
    return True


def revert():
    try:
        from moduli.monitor import KaraokeMonitor as C
        if hasattr(C, '_orig_059_rewrap'):
            C._rewrap_syllables = C._orig_059_rewrap
            del C._orig_059_rewrap
    except Exception:
        pass


try:
    apply()
except Exception as _e:
    print('patch 059: %s' % _e)
