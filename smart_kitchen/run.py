"""
Smart Kitchen — universal launcher.

Run this from any Python environment:

    python run.py

• On a desktop with a screen  → opens the full Tkinter GUI (main.py).
• In a headless / online IDE   → automatically opens the console UI (cli.py).

Both share the same logic in core.py, so the behaviour is identical
everywhere. The web/React version (in the project root) is for publishing
online; this Python version is the standalone IDE-friendly app.
"""

import importlib


def _gui_available():
    try:
        import tkinter  # noqa: F401
    except Exception:
        return False
    try:
        root = tkinter.Tk()
        root.destroy()
        return True
    except Exception:
        return False


def main():
    if _gui_available():
        gui = importlib.import_module("main")
        gui.main()
    else:
        print("No graphical display detected — starting the console version.")
        print("(Run on a desktop with a screen to get the full GUI.)\n")
        cli = importlib.import_module("cli")
        cli.main()


if __name__ == "__main__":
    main()
