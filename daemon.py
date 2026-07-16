"""
Snapshrink - settings storage.

Settings live in config.json in the APPLICATION FOLDER (next to snapshrink.exe),
not in the user's AppData - as requested.

IMPORTANT for the installer: because of this, Snapshrink must be installed to a
user-writable location (e.g. C:\\Users\\<you>\\AppData\\Local\\Programs\\Snapshrink),
NOT to C:\\Program Files. Program Files is read-only for normal users, and the app
would not be able to save your settings there. Inno Setup does this with
PrivilegesRequired=lowest - it also means the installer needs no admin rights.

If the app folder somehow isn't writable (e.g. someone force-installs to
Program Files), we fall back to a LocalAppData folder rather than crash.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------- defaults

DEFAULTS: dict = {
    # --- master settings: used by the GUI window ---
    "out_format": "jpg",        # jpg | png | webp
    "quality": 95,              # 60..95
    "target_kb": None,          # None or int
    "target_px": None,          # None or int
    "strip_exif": False,
    "output_dir": None,         # None = same folder as source

    # --- hotkey preset: used by Ctrl+Alt+J (Phase 4), independent of above ---
    "hotkey_enabled": True,
    "hotkey": "<ctrl>+<alt>+j",
    "hk_out_format": "jpg",
    "hk_quality": 95,
    "hk_target_kb": None,
    "hk_target_px": None,
    "hk_strip_exif": False,

    # --- feedback ---
    "toast_feedback": True,     # Windows notification after hotkey convert
    "sound_feedback": True,     # short beep on success / error
}


def app_dir() -> Path:
    """Folder the app lives in (works both as .py script and frozen .exe)."""
    if getattr(sys, "frozen", False):          # PyInstaller build
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


def _fallback_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    d = Path(base) / "Snapshrink"
    d.mkdir(parents=True, exist_ok=True)
    return d


def config_path() -> Path:
    """Prefer app folder; fall back only if it isn't writable."""
    primary = app_dir() / "config.json"
    try:
        probe = app_dir() / ".write_test"
        probe.write_text("x")
        probe.unlink()
        return primary
    except Exception:
        return _fallback_dir() / "config.json"


def load() -> dict:
    """Always returns a complete settings dict (defaults + saved values)."""
    cfg = dict(DEFAULTS)
    p = config_path()
    try:
        if p.exists():
            saved = json.loads(p.read_text(encoding="utf-8"))
            # only accept keys we know about - ignores junk / old versions
            for k in DEFAULTS:
                if k in saved:
                    cfg[k] = saved[k]
    except Exception as e:
        print(f"[CONFIG] could not read {p}: {e} - using defaults")
    return cfg


def save(cfg: dict) -> bool:
    p = config_path()
    try:
        clean = {k: cfg.get(k, DEFAULTS[k]) for k in DEFAULTS}
        p.write_text(json.dumps(clean, indent=2), encoding="utf-8")
        print(f"[CONFIG] saved -> {p}")
        return True
    except Exception as e:
        print(f"[CONFIG] SAVE FAILED {p}: {e}")
        return False


def to_options(cfg: dict, hotkey_preset: bool = False):
    """Turn a settings dict into an engine Options object.
    hotkey_preset=True reads the hk_* keys instead of the master keys."""
    from .engine import Options
    p = "hk_" if hotkey_preset else ""
    if hotkey_preset:
        return Options(
            out_format=cfg["hk_out_format"], quality=cfg["hk_quality"],
            target_kb=cfg["hk_target_kb"], target_px=cfg["hk_target_px"],
            strip_exif=cfg["hk_strip_exif"], output_dir=None,
        )
    return Options(
        out_format=cfg["out_format"], quality=cfg["quality"],
        target_kb=cfg["target_kb"], target_px=cfg["target_px"],
        strip_exif=cfg["strip_exif"], output_dir=cfg["output_dir"],
    )
