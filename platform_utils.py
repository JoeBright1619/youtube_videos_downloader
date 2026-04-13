def enable_high_dpi():
    """
    Prevent Windows from bitmap-scaling the UI (blurry).
    Call before creating the Tk root window.
    """
    try:
        import ctypes

        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
            return
        except Exception:
            pass

        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass
    except Exception:
        pass


def apply_tk_scaling(root):
    """Match Tk scaling to monitor DPI for crisper text/layout."""
    try:
        import ctypes

        dpi = ctypes.windll.user32.GetDpiForWindow(root.winfo_id())
        root.tk.call("tk", "scaling", dpi / 96.0)
    except Exception:
        pass
