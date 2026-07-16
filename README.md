# ⚡ Snapshrink

**Right-click. One click. Done.**

The fastest way to convert, resize and compress images on Windows — without ever opening an app.

![Snapshrink demo](demo-placeholder.gif)
*(replace this with your recorded demo GIF/video once ready)*

---

## Why Snapshrink exists

Screenshots save as PNG. Photos from your phone arrive as HEIC. Downloads show up as WebP, BMP, AVIF — anything except the one format every website upload form actually wants: **JPG**.

The usual fixes are all broken in their own way:
- Photo editors overwrite your original file
- Online converters ask "where do you want to save this?" for every single image
- None of them let you say *"just keep it under 250 KB"* and have it actually happen

Snapshrink solves all three, right from the Windows right-click menu.

## What it does

- **Convert** any supported image to JPG, PNG, or WebP — one click
- **Resize to JPG** by exact pixel limit (250px → 2500px presets)
- **Compress to JPG** by exact file size limit (10 KB → 1 MB presets) — the engine finds the right quality automatically, no trial and error
- **Instant hotkey**: select images in Explorer, press `Ctrl+Alt+J`, done — no window ever opens
- **Batch mode**: drop a whole folder into the app for parallel processing
- **Privacy**: optional one-toggle EXIF/GPS metadata stripping
- **Originals are never touched** — every run creates a new file alongside the source

## Supported formats

| Input | Output |
|---|---|
| JPEG, PNG, WebP, GIF, TIFF, BMP, ICO, HEIC/HEIF | JPG, PNG, WebP |

## Install

1. Download the latest `SnapshrinkSetup.exe` from [Releases](../../releases)
2. Run it — no admin rights needed, installs to your user folder
3. Right-click any image → **Snapshrink** → pick an option

> First run may show a Windows SmartScreen warning ("Windows protected your PC") since this is an independently-published tool. Click **More info → Run anyway**. This is expected for any app outside the Microsoft Store and is not a sign of a problem — see [SECURITY.md](SECURITY.md) for detail on why, and what's actually running.

## Building it yourself

See [`installer/`](installer) for the full build pipeline (PyInstaller + Inno Setup). Requires Python 3.10+ and the packages in `requirements.txt`.

```bash
pip install -r requirements.txt
python installer/build_app.py      # builds the app
# then open installer/Snapshrink.iss in Inno Setup and compile
```

## Contributing

Contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) for how to get set up, and [Issues](../../issues) for open ideas and bugs.

## License

MIT — see [LICENSE](LICENSE). Free for personal and commercial use.

---

**Open Source · Free Forever**
Developed by [Vijay Parmar](https://www.linkedin.com/in/thevijayparmar/)
