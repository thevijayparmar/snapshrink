#!/usr/bin/env python3
"""
Phase 5, step 1: build Snapshrink.exe itself (the whole app, one file that
handles every mode: window, daemon, hotkey, right-click).

Run from the snapshrink folder (the one with 'sspack' inside it):

    python installer\\build_app.py

This produces:  installer\\dist\\Snapshrink\\Snapshrink.exe   (plus support files)

We use --onedir (a folder), NOT --onefile. A single .exe sounds simpler, but
it silently unpacks itself to a temp folder on every single launch, which
adds a very noticeable delay - exactly what we don't want for a hotkey tool
that's supposed to feel instant. Inno Setup will hide the folder from the
user anyway; they'll only ever see one Start Menu shortcut.
"""

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent          # .../snapshrink/installer
ROOT = HERE.parent                                # .../snapshrink


def fail(msg: str, fix: str = "") -> int:
    print("\n" + "!" * 60)
    print("BUILD FAILED: " + msg)
    if fix:
        print("\nHOW TO FIX:\n" + fix)
    print("!" * 60)
    return 1


def main() -> int:
    print("=" * 60)
    print(" Building Snapshrink.exe (the full app)")
    print("=" * 60)
    print(f"Python being used : {sys.executable}")
    print(f"Snapshrink folder : {ROOT}")

    if not (ROOT / "sspack" / "__main__.py").exists():
        return fail(
            "Can't find the 'sspack' folder next to 'installer'.",
            f"Make sure this script stays inside the snapshrink\\installer\n"
            f"folder, and run it from there. Current location:\n  {HERE}",
        )

    probe = subprocess.run([sys.executable, "-m", "PyInstaller", "--version"],
                           capture_output=True, text=True)
    if probe.returncode != 0:
        return fail(
            "PyInstaller is not installed for this Python.",
            f'  "{sys.executable}" -m pip install pyinstaller\n'
            f"Then run this script again.",
        )
    print(f"PyInstaller       : {probe.stdout.strip()} OK")

    entry = ROOT / "installer" / "_entry.py"
    entry.write_text(
        # No sys.path hacking here: PyInstaller statically finds and bundles
        # the sspack package because we import it directly below. Inserting
        # a raw filesystem path (which we used to do) fights with PyInstaller's
        # own frozen import machinery and breaks stdlib resolution - do not
        # add that back even though it looks harmless.
        "from sspack.__main__ import main\n"
        "import sys\n"
        "sys.exit(main())\n",
        encoding="utf-8",
    )

    dist = HERE / "dist"
    work = HERE / "build"
    icon = ROOT / "snapshrink.ico"   # optional - falls back to default if missing

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onedir",                 # a folder, not one slow-starting file
        "--noconsole",
        "--noconfirm",
        "--clean",
        "--name", "Snapshrink",
        "--distpath", str(dist),
        "--workpath", str(work),
        "--specpath", str(work),
        "--paths", str(ROOT),        # so PyInstaller's ANALYSIS finds sspack
                                     # (this does not affect the frozen app's
                                     # runtime sys.path - only build-time search)
        # these packages don't declare their data files well enough for
        # PyInstaller to find automatically - spell them out:
        "--collect-all", "customtkinter",
        "--collect-all", "tkinterdnd2",
        "--collect-all", "winotify",
        "--hidden-import", "win32timezone",  # pywin32 quirk, harmless if unused
    ]
    if icon.exists():
        cmd += ["--icon", str(icon)]
    cmd.append(str(entry))

    print("\nRunning PyInstaller (1-3 minutes)...\n")
    result = subprocess.run(cmd)
    entry.unlink(missing_ok=True)

    if result.returncode != 0:
        return fail("PyInstaller reported an error (scroll up).",
                    "Copy the error lines above and send them over.")

    exe = dist / "Snapshrink" / "Snapshrink.exe"
    if not exe.exists():
        return fail(f"Build finished but no exe at:\n  {exe}")

    print("\n" + "=" * 60)
    print(f" DONE - built: {exe}")
    print("=" * 60)
    print("\nNEXT STEP: open installer\\Snapshrink.iss in Inno Setup and")
    print("click Compile (or press F9). See PHASE5-INSTALLER.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
