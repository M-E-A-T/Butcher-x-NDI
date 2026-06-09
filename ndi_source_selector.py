import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time

def choose_source(ndi, finder, poll_interval=2000):
    """Open a modal Tk dialog to choose an NDI source.

    ndi: the NDIlib module
    finder: a finder instance (returned by ndi.find_create_v2())
    Returns the selected source object or None if cancelled.
    """
    selected = {'src': None}

    root = tk.Tk()
    root.title('Select NDI Source')
    root.geometry('600x300')

    frm = ttk.Frame(root, padding=10)
    frm.pack(fill=tk.BOTH, expand=True)

    lst = tk.Listbox(frm, height=10)
    lst.pack(fill=tk.BOTH, expand=True, side=tk.TOP)

    btn_frame = ttk.Frame(frm)
    btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

    def refresh():
        try:
            ndi.find_wait_for_sources(finder, 100)
            sources = ndi.find_get_current_sources(finder)
        except Exception:
            sources = []
        lst.delete(0, tk.END)
        for i, s in enumerate(sources):
            name = getattr(s, 'ndi_name', None) or getattr(s, 'p_ndi_name', None) or str(s)
            lst.insert(tk.END, name)
        # store latest list
        lst._sources = sources

    def on_select():
        sel = lst.curselection()
        if not sel:
            messagebox.showinfo('Select', 'Please select a source first')
            return
        idx = sel[0]
        sources = getattr(lst, '_sources', [])
        if idx < len(sources):
            selected['src'] = sources[idx]
        # ensure mainloop exits cleanly
        try:
            root.quit()
        except Exception:
            pass
        root.destroy()

    def on_cancel():
        root.destroy()

    btn_refresh = ttk.Button(btn_frame, text='Refresh', command=refresh)
    btn_refresh.pack(side=tk.LEFT, padx=4, pady=4)

    btn_select = ttk.Button(btn_frame, text='Select', command=on_select)
    btn_select.pack(side=tk.LEFT, padx=4, pady=4)

    btn_cancel = ttk.Button(btn_frame, text='Cancel', command=on_cancel)
    btn_cancel.pack(side=tk.RIGHT, padx=4, pady=4)

    # Auto-refresh periodically
    def periodic_refresh():
        try:
            refresh()
        except Exception:
            pass
        root.after(poll_interval, periodic_refresh)

    # Initial population
    refresh()
    root.after(poll_interval, periodic_refresh)

    # Bind double-click and Enter key for immediate selection
    lst.bind('<Double-Button-1>', lambda e: on_select())
    root.bind('<Return>', lambda e: on_select())
    lst.focus_set()

    # Run the Tk mainloop (this will block until the window is closed)
    root.mainloop()

    return selected['src']
