# Security & SmartScreen

## "Windows protected your PC" warning

When you first run `SnapshrinkSetup.exe`, Windows may show a blue screen
saying **"Windows protected your PC"** with a "Don't run" button front and
center. This is **expected**, not a sign that something is wrong.

### Why this happens

Windows SmartScreen shows this warning for any application that isn't
**code-signed** with a certificate from a recognized certificate authority,
or hasn't yet built up enough download reputation with Microsoft. Signing
certificates cost money annually and are a separate step from writing the
software itself — many free, independent, open-source tools (including
well-known ones) show this same warning for exactly this reason.

### How to proceed if you trust the source

1. Click **"More info"**
2. Click **"Run anyway"**

### How to verify it yourself instead of trusting this README

Since Snapshrink is fully open source, you don't have to take anyone's word
for it:
- Read the source code yourself — every line is in this repository
- Build it yourself from source using `installer/build_app.py`, so the
  `.exe` you run is one you compiled, not one you downloaded
- Check the [Releases](../../releases) page — each release is built from a
  tagged commit, so you can compare the exact source that produced it

### What Snapshrink actually does on your machine

For full transparency:
- Reads image files you select, converts them, writes a new file next to
  the original (never overwrites or deletes anything)
- Registers a right-click menu entry (removable via **Uninstall**)
- Runs a small background process for the `Ctrl+Alt+J` hotkey and tray icon
- **Does not** access the network, does not send any data anywhere, does
  not collect telemetry
