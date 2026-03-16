def bring_popup_to_front(
    popup,
    parent=None,
    keep_on_top: bool = True,
    take_focus: bool = True,
) -> None:
    """Raise a CTk/Tk popup above other windows."""
    if parent is not None:
        try:
            popup.transient(parent)
        except Exception:
            pass

    try:
        popup.lift()
    except Exception:
        pass

    try:
        popup.attributes("-topmost", True)
        if not keep_on_top:
            popup.after(150, lambda: popup.attributes("-topmost", False))
    except Exception:
        pass

    if take_focus:
        try:
            popup.focus_force()
        except Exception:
            pass
