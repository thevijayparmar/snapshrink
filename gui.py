"""
Snapshrink - Phase 4: the silent background helper.

What it does:
  1. Sits in the system tray using almost no CPU (pynput installs a low-level
     Windows keyboard hook - the OS wakes us only on a keypress, we never poll).
  2. When you press Ctrl+Alt+J, it asks Windows Explorer which files you have
     selected, and converts them using your saved hotkey preset.
  3. Tells you what happened with a toast notification and/or a beep.
     No window ever opens.

Windows-only (it talks to Explorer through COM). On other systems it exits
with a clear message.

Debug output goes to the console, e.g.
    [HOOK]   Ctrl+Alt+J pressed
    [HOOK]   Explorer selection: 3 file(s)
    [ENGINE] photo.png -> photo_1920-248KB.jpg  (246 KB, q72)
"""

from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

from . import config as cfgmod
from .engine import SUPPORTED_INPUT_EXT, process_batch

IS_WINDOWS = sys.platform == "win32"


# --------------------------------------------------------------------------
# Ask Explorer what the user has selected
# --------------------------------------------------------------------------

def get_explorer_selection() -> list[str]:
    """Return the image files currently selected in the FOREGROUND Explorer
    window (or on the Desktop). Empty list if the front window isn't Explorer.

    This is the fragile part of the whole app - Explorer is not built to be
    queried like this. Every call is wrapped defensively: any failure just
    returns [] and the hotkey quietly does nothing rather than crashing."""
    if not IS_WINDOWS:
        return []
    try:
        import pythoncom
        import win32gui
        import win32com.client
    except ImportError:
        print("[HOOK] pywin32 not installed - cannot read Explorer selection")
        return []

    pythoncom.CoInitialize()          # COM must be initialised per thread
    try:
        fg = win32gui.GetForegroundWindow()
        cls = win32gui.GetClassName(fg)

        shell = win32com.client.Dispatch("Shell.Application")
        paths: list[str] = []

        # Normal Explorer window (CabinetWClass) or a folder tree (ExploreWClass)
        for win in shell.Windows():
            try:
                if int(win.HWND) == int(fg):
                    for item in win.Document.SelectedItems():
                        paths.append(str(item.Path))
                    break
            except Exception:
                continue

        # Desktop icons are a different beast (Progman / WorkerW)
        if not paths and cls in ("Progman", "WorkerW"):
            try:
                for win in shell.Windows():
                    if win.Name in ("Desktop", "Windows Explorer"):
                        for item in win.Document.SelectedItems():
                            paths.append(str(item.Path))
                        break
            except Exception:
                pass

        # Keep only real image files (OneDrive placeholders that aren't
        # downloaded yet will fail later in the engine with a clean error)
        return [p for p in paths
                if Path(p).suffix.lower() in SUPPORTED_INPUT_EXT and Path(p).is_file()]
    except Exception as e:
        print(f"[HOOK] could not read Explorer selection: {e}")
        return []
    finally:
        try:
            pythoncom.CoUninitialize()
        except Exception:
            pass


# --------------------------------------------------------------------------
# User feedback (no window!)
# --------------------------------------------------------------------------

def notify(title: str, message: str, cfg: dict, error: bool = False) -> None:
    if cfg.get("sound_feedback", True):
        try:
            import winsound
            if error:
                winsound.MessageBeep(0x00000010)      # error sound
            else:
                winsound.MessageBeep(0x00000000)      # soft "ok" sound
        except Exception:
            pass
    if cfg.get("toast_feedback", True):
        try:
            from winotify import Notification
            Notification(app_id="Snapshrink", title=title, msg=message).show()
        except Exception as e:
            print(f"[TOAST] unavailable ({e}) - message was: {title} | {message}")


# --------------------------------------------------------------------------
# The actual hotkey job
# --------------------------------------------------------------------------

_busy = threading.Lock()


def run_quick_convert(paths: list[str] | None = None,
                      ctx_resize_px: int | None = None,
                      ctx_compress_kb: int | None = None) -> None:
    """Convert using a preset. Safe to call from any thread.
    
    Args:
        paths: explicit files to convert (if None, read from Explorer)
        ctx_resize_px: right-click "Resize to JPG -> 1920px" preset
        ctx_compress_kb: right-click "Compress to JPG -> 250KB" preset
    """
    if not _busy.acquire(blocking=False):
        print("[HOOK] already busy - ignoring")
        return
    try:
        cfg = cfgmod.load()
        files = paths if paths is not None else get_explorer_selection()
        if not files:
            print("[HOOK] no image files selected")
            notify("Snapshrink", "No image files selected in Explorer.", cfg, error=True)
            return

        print(f"[HOOK] {len(files)} file(s) to convert")
        
        # Build options based on which context menu preset was used
        if ctx_resize_px is not None:
            # "Resize to JPG → 1920px": use hotkey quality + this pixel limit
            opts = cfgmod.to_options(cfg, hotkey_preset=True)
            opts.target_px = ctx_resize_px
            opts.target_kb = None  # no KB limit on resize
            opts.out_format = "jpg"
            print(f"[CTX] Resize: max {ctx_resize_px}px, q{opts.quality}")
        elif ctx_compress_kb is not None:
            # "Compress to JPG → 250KB": KB limit only, no PX, let quality float
            opts = cfgmod.to_options(cfg, hotkey_preset=False)  # use master settings
            opts.target_kb = ctx_compress_kb
            opts.target_px = None  # no PX limit on compress
            opts.out_format = "jpg"
            # For compress, we don't force quality - let the KB loop pick it
            print(f"[CTX] Compress: max {ctx_compress_kb}KB")
        else:
            # Regular hotkey: use the hotkey preset as usual
            opts = cfgmod.to_options(cfg, hotkey_preset=True)
            print(f"[HOOK] Hotkey preset: {opts.out_format.upper()} q{opts.quality}"
                  + (f", max {opts.target_kb}KB" if opts.target_kb else "")
                  + (f", max {opts.target_px}px" if opts.target_px else ""))
        
        t0 = time.perf_counter()

        def progress(done, total, r):
            print(f"[ENGINE] {r.summary()}")

        results = process_batch(files, opts, progress=progress)
        ok = [r for r in results if r.ok]
        bad = [r for r in results if not r.ok]
        secs = time.perf_counter() - t0

        if ok and not bad:
            if len(ok) == 1:
                msg = f"{Path(ok[0].output).name}  ({ok[0].out_bytes/1024:.0f} KB)"
            else:
                saved = sum(r.in_bytes for r in ok) - sum(r.out_bytes for r in ok)
                msg = f"{len(ok)} images converted, {saved/1024:.0f} KB saved"
            notify("Snapshrink", msg, cfg)
        elif ok and bad:
            notify("Snapshrink",
                   f"{len(ok)} converted, {len(bad)} failed", cfg, error=True)
        else:
            notify("Snapshrink", bad[0].error or "unknown error", cfg, error=True)
    finally:
        _busy.release()


# --------------------------------------------------------------------------
# Tray icon + hotkey listener
# --------------------------------------------------------------------------

def _tray_image():
    """Draw a simple tray icon in memory (no .ico file needed for testing)."""
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([4, 4, 60, 60], radius=12, fill=(59, 142, 208, 255))
    d.polygon([(34, 12), (20, 36), (30, 36), (26, 52), (44, 28), (33, 28)],
              fill=(255, 255, 255, 255))          # lightning bolt
    return img


def start(open_gui_callback=None) -> int:
    """Run the tray + hotkey daemon. Blocks until the user quits."""
    if not IS_WINDOWS:
        print("The background hotkey daemon is Windows-only.")
        print("The window (python -m sspack) works everywhere.")
        return 1

    try:
        import pystray
        from pynput import keyboard
    except ImportError:
        print("Missing packages. Run:  pip install pystray pynput winotify pywin32")
        return 1

    cfg = cfgmod.load()
    hotkey = cfg.get("hotkey", "<ctrl>+<alt>+j")

    print("=" * 58)
    print(" Snapshrink daemon running.  Tray icon is in the taskbar corner.")
    print(f" Hotkey: {hotkey}  ->  converts files selected in Explorer")
    print(f" Preset: {cfg['hk_out_format'].upper()} q{cfg['hk_quality']}"
          + (f", max {cfg['hk_target_kb']}KB" if cfg['hk_target_kb'] else "")
          + (f", max {cfg['hk_target_px']}px" if cfg['hk_target_px'] else "")
          + (", EXIF stripped" if cfg['hk_strip_exif'] else ""))
    print(f" Config: {cfgmod.config_path()}")
    print(" Ctrl+C here (or tray > Quit) to stop.")
    print("=" * 58)

    def on_hotkey():
        print(f"\n[HOOK] {hotkey} pressed")
        # Do the work on a worker thread: never block the keyboard hook,
        # or Windows will drop the hook for being unresponsive.
        threading.Thread(target=run_quick_convert, daemon=True).start()

    listener = keyboard.GlobalHotKeys({hotkey: on_hotkey})
    listener.start()

    def do_open_gui(icon=None, item=None):
        # Launch the window as its own process so the tray stays responsive
        # and so customtkinter is never imported into the daemon process.
        import subprocess
        if getattr(sys, "frozen", False):
            subprocess.Popen([sys.executable])
        else:
            subprocess.Popen([sys.executable, "-m", "sspack"])

    def do_quit(icon, item):
        print("[TRAY] quitting")
        listener.stop()
        icon.stop()

    icon = pystray.Icon(
        "snapshrink", _tray_image(), "Snapshrink",
        menu=pystray.Menu(
            pystray.MenuItem("Open Snapshrink", do_open_gui, default=True),
            pystray.MenuItem(f"Hotkey: {hotkey}", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", do_quit),
        ),
    )
    try:
        icon.run()
    except KeyboardInterrupt:
        listener.stop()
    return 0
