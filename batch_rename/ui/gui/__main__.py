# batch_rename/ui/gui/__main__.py

# import the real runner in ui/gui/gui.py
from . import gui as _gui  # relative import; _gui refers to batch_rename.ui.gui.gui

def main():
    # call whatever entrypoint your gui module exposes. adjust if named differently.
    try:
        _gui.main()
    except AttributeError:
        # if your module exposes a different entry name, call it explicitly
        if hasattr(_gui, "run"):
            _gui.run()
        else:
            raise RuntimeError("ui.gui.gui has no main() or run() function")

if __name__ == "__main__":
    main()
