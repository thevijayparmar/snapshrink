"""
Snapshrink Context Menu Extension - Phase 4B

This module builds a standalone .exe shim that Explorer calls directly.
No registry hassle, no quoting issues, no "Show more options" burial.

When you right-click an image:
  Snapshrink → Convert to JPG               (hotkey preset)
  Snapshrink → Resize to JPG → [pixels]     (q95 + pixel limit)
  Snapshrink → Compress to JPG → [KB]       (KB limit, no PX)
  Snapshrink → Open Tool                    (window)

The Explorer handler passes the clicked file(s) as argv to the shim.
The shim then calls back into sspack with the right --cwd and conversion options.

Building the shim:
    python -m sspack --build-contextmenu-shim

Installing (adds registry entries):
    python -m sspack --install-contextmenu

Uninstalling:
    python -m sspack --uninstall-contextmenu
"""

from __future__ import annotations

import sys
from pathlib import Path

IS_WINDOWS = sys.platform == "win32"

# Presets for the right-click submenus
PIXEL_SIZES = [250, 500, 800, 1200, 1600, 1980, 2500]
KB_SIZES = [10, 50, 150, 250, 500, 1024]  # 1024 = 1 MB


def _shim_code(sspack_folder: Path) -> str:
    """Generate Python source for the .exe shim.
    
    This tiny script is what gets embedded in the .exe. When Explorer calls it,
    it receives the clicked file as argv[1], plus query params from the registry
    telling it which conversion to perform."""
    sspack_folder_str = str(sspack_folder).replace("\\", "\\\\")
    return f'''#!/usr/bin/env python3
"""Snapshrink context menu shim - embedded in the .exe."""
import sys, os
sys.path.insert(0, r"{sspack_folder_str}")
os.chdir(r"{sspack_folder_str}")

from sspack.__main__ import main
sys.exit(main())
'''


def build_shim(output_exe: str | Path) -> bool:
    """Build the .exe shim using PyInstaller (called during installer prep).
    This is done ONCE during packaging, not at runtime."""
    import subprocess
    import tempfile
    from pathlib import Path
    
    output_exe = Path(output_exe)
    pkg_parent = Path(__file__).resolve().parent.parent
    
    with tempfile.TemporaryDirectory() as tmp:
        shim_py = Path(tmp) / "shim.py"
        shim_py.write_text(_shim_code(pkg_parent))
        
        cmd = [
            sys.executable, "-m", "pyinstaller",
            "--onefile", "--windowed", "--noconsole",
            "--name", "snapshrink-ctx",
            "--distpath", str(output_exe.parent),
            "--specpath", str(Path(tmp) / "build"),
            "--buildpath", str(Path(tmp) / "build"),
            str(shim_py),
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"[SHIM] built -> {output_exe}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[SHIM] build failed: {e.stderr}")
            return False


def install(shim_exe: str | Path | None = None) -> int:
    """Register the context menu entries in the registry.
    
    If shim_exe is None, auto-detect: when running as a frozen PyInstaller
    build, Snapshrink.exe registers ITSELF as the handler (no separate shim
    needed - the installed app already understands --quick/--ctx-resize/etc).
    Only when running from raw source (development/testing) do we need the
    separately-built snapshrink-ctx.exe from build_shim.py."""
    if not IS_WINDOWS:
        print("Windows only.")
        return 1
    
    import winreg
    
    if shim_exe is None:
        if getattr(sys, "frozen", False):
            shim_exe = Path(sys.executable)   # the installed Snapshrink.exe itself
        else:
            shim_exe = Path(__file__).resolve().parent.parent / "snapshrink-ctx.exe"
    shim_exe = Path(shim_exe)
    
    if not shim_exe.exists():
        print(f"Shim exe not found: {shim_exe}")
        print("Run: python -m sspack --build-contextmenu-shim")
        return 1
    
    shim_str = str(shim_exe)
    base = r"Software\Classes\SystemFileAssociations\image\shell"
    
    def setval(path, name, value):
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, path) as k:
            winreg.SetValueEx(k, name, 0, winreg.REG_SZ, value)
    
    try:
        # --- top-level Snapshrink entry (no command, just a label) ---
        setval(f"{base}\\Snapshrink", "MUIVerb", "Snapshrink")
        setval(f"{base}\\Snapshrink", "Icon", shim_str)
        setval(f"{base}\\Snapshrink", "subcommands", "")
        setval(f"{base}\\Snapshrink", "MultiSelectModel", "Player")
        
        # --- 1. Convert to JPG (instant, hotkey preset) ---
        setval(f"{base}\\Snapshrink\\shell\\01convert", "MUIVerb", "Convert to JPG")
        setval(f"{base}\\Snapshrink\\shell\\01convert", "Icon", shim_str)
        setval(f"{base}\\Snapshrink\\shell\\01convert\\command", "",
               f'"{shim_str}" --quick "%1"')
        
        # --- 2. Resize to JPG (submenu) ---
        setval(f"{base}\\Snapshrink\\shell\\02resize", "MUIVerb", "Resize to JPG")
        setval(f"{base}\\Snapshrink\\shell\\02resize", "Icon", shim_str)
        setval(f"{base}\\Snapshrink\\shell\\02resize", "subcommands", "")
        
        for i, px in enumerate(PIXEL_SIZES):
            key = f"{base}\\Snapshrink\\shell\\02resize\\shell\\r{i:02d}_{px}"
            setval(key, "MUIVerb", f"{px}px")
            setval(f"{key}\\command", "",
                   f'"{shim_str}" --ctx-resize {px} "%1"')
        
        # --- 3. Compress to JPG (submenu) ---
        setval(f"{base}\\Snapshrink\\shell\\03compress", "MUIVerb", "Compress to JPG")
        setval(f"{base}\\Snapshrink\\shell\\03compress", "Icon", shim_str)
        setval(f"{base}\\Snapshrink\\shell\\03compress", "subcommands", "")
        
        for i, kb in enumerate(KB_SIZES):
            kb_label = f"{kb//1024}MB" if kb >= 1024 else f"{kb}KB"
            key = f"{base}\\Snapshrink\\shell\\03compress\\shell\\c{i:02d}_{kb}"
            setval(key, "MUIVerb", kb_label)
            setval(f"{key}\\command", "",
                   f'"{shim_str}" --ctx-compress {kb} "%1"')
        
        # --- 4. Open Tool ---
        setval(f"{base}\\Snapshrink\\shell\\04open", "MUIVerb", "Open Tool")
        setval(f"{base}\\Snapshrink\\shell\\04open", "Icon", shim_str)
        setval(f"{base}\\Snapshrink\\shell\\04open\\command", "",
               f'"{shim_str}" "%1"')
        
        print("Context menu installed (current user only).")
        print(f"  Shim: {shim_exe}")
        print(f"  Registry: HKEY_CURRENT_USER\\{base}\\Snapshrink")
        return 0
    except Exception as e:
        print(f"Install failed: {e}")
        return 1


def uninstall() -> int:
    """Remove all Snapshrink context menu entries."""
    if not IS_WINDOWS:
        print("Windows only.")
        return 1
    
    import winreg
    base = r"Software\Classes\SystemFileAssociations\image\shell"
    
    def nuke(path: str):
        """Delete a key and everything under it."""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path, 0,
                                winreg.KEY_ALL_ACCESS) as k:
                while True:
                    try:
                        child = winreg.EnumKey(k, 0)
                    except OSError:
                        break
                    nuke(f"{path}\\{child}")
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, path)
        except FileNotFoundError:
            pass
        except OSError as e:
            print(f"  Could not remove {path}: {e}")
    
    nuke(f"{base}\\Snapshrink")
    print("Context menu removed.")
    return 0
