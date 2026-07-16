"""
Snapshrink - single entry point. Decides what to do, then imports ONLY what
that job needs. This is what keeps the background daemon light: it never
imports customtkinter, and the quick-convert path never opens a window.

    python -m sspack                      -> window, empty drop zone
    python -m sspack a.png b.jpg          -> window, files already queued
    python -m sspack --quick a.png        -> silent convert, no window
    python -m sspack --daemon             -> tray icon + Ctrl+Alt+J listener
    python -m sspack --install-menu       -> add right-click entry (old, simple)
    python -m sspack --uninstall-menu     -> remove old right-click entry
    
    # NEW: Context Menu Extension (proper Windows integration)
    python -m sspack --build-contextmenu-shim    -> compile the .exe shim
    python -m sspack --install-contextmenu       -> install right-click with submenus
    python -m sspack --uninstall-contextmenu     -> remove right-click submenus
"""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    # --cwd <path> is only used by the registry command line so that Python can
    # find the package when launched from Explorer. Strip it out early.
    if "--cwd" in argv:
        i = argv.index("--cwd")
        try:
            sys.path.insert(0, argv[i + 1])
            del argv[i:i + 2]
        except IndexError:
            del argv[i:]

    if "--help" in argv or "-h" in argv or "/?" in argv:
        print(__doc__)
        return 0

    if "--build-contextmenu-shim" in argv:
        # This is now delegated to build_shim.py for better PyInstaller integration
        print("Context menu shim building moved to standalone script.")
        print("\nRun:")
        print("  python build_shim.py")
        print("\nMake sure pyinstaller is installed:")
        print("  pip install pyinstaller")
        return 1

    if "--install-contextmenu" in argv:
        from .contextmenu import install
        return install(None)  # auto-detects: frozen exe registers itself

    if "--uninstall-contextmenu" in argv:
        from .contextmenu import uninstall
        return uninstall()

    if "--ctx-resize" in argv or "--ctx-compress" in argv:
        # Silent right-click conversions: context menu preset
        from .daemon import run_quick_convert
        from pathlib import Path
        
        # Parse: --ctx-resize 1920 "file.jpg" OR --ctx-compress 250 "file.jpg"
        try:
            if "--ctx-resize" in argv:
                i = argv.index("--ctx-resize")
                px = int(argv[i + 1])
                files = [a for a in argv[i+2:] if not a.startswith("--")]
                run_quick_convert(files, ctx_resize_px=px)
            elif "--ctx-compress" in argv:
                i = argv.index("--ctx-compress")
                kb = int(argv[i + 1])
                files = [a for a in argv[i+2:] if not a.startswith("--")]
                run_quick_convert(files, ctx_compress_kb=kb)
        except (ValueError, IndexError) as e:
            print(f"[CTX] argument parse error: {e}")
            return 1
        return 0

    if "--install-menu" in argv:
        from .shellmenu import install
        return install()

    if "--uninstall-menu" in argv:
        from .shellmenu import uninstall
        return uninstall()

    if "--daemon" in argv:
        from .daemon import start
        return start()

    if "--quick" in argv:
        # Silent path: no GUI import at all.
        from .daemon import run_quick_convert
        files = [a for a in argv if not a.startswith("--")]
        run_quick_convert(files or None)   # None -> ask Explorer
        return 0

    # Default: open the window (with any files passed as arguments)
    files = [a for a in argv if not a.startswith("--")]
    from .gui import launch
    launch(files or None)
    return 0


if __name__ == "__main__":
    sys.exit(main())
