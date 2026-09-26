import tkinter as tk


def _spenta():
    try:
        from moduli.database import Database
        return str(Database.get_config('patch_132', '1')) == '0'
    except Exception:
        return False


def apply():
    if _spenta():
        return False
    try:
        import moduli.libreria as lib
        C = getattr(lib, 'LibreriaSlider', None)
        if C is None or getattr(C, '_scroll132', False):
            return True
        _orig = C._sc_edit_brano

        def _wrap(self, iid, text_item_id):
            r = _orig(self, iid, text_item_id)
            try:
                fr = getattr(self, '_sc_brano_sugg', None)
                lb = getattr(self, '_sc_brano_sugg_lb', None)
                if fr is not None and lb is not None and not getattr(fr, '_sb132', None):
                    lb.pack_forget()
                    sb = tk.Scrollbar(fr, bg='#1a1a1a', bd=0,
                                      troughcolor='#1a1a1a', command=lb.yview)
                    lb.config(yscrollcommand=sb.set)
                    sb.pack(side='right', fill='y')
                    lb.pack(side='left', fill='both', expand=True)
                    fr._sb132 = sb
                    # rotella: scorre i suggerimenti e NON la scaletta dietro
                    lb.bind('<MouseWheel>', lambda e: (lb.yview_scroll(-1 * int(e.delta / 120), 'units'), 'break')[1])
                    lb.bind('<Button-4>', lambda e: (lb.yview_scroll(-1, 'units'), 'break')[1])
                    lb.bind('<Button-5>', lambda e: (lb.yview_scroll(1, 'units'), 'break')[1])
            except Exception as e:
                print('[SCROLL132] popup:', e)
            return r

        C._sc_edit_brano = _wrap
        C._scroll132 = True
        print('[SCROLL132] scrollbar nei suggerimenti delle righe')
    except Exception as e:
        print('[SCROLL132] hook:', e)
    return True


def revert():
    pass


try:
    apply()
except Exception as _e:
    print('patch 132: %s' % _e)
