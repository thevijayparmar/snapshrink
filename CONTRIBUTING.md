# Contributing to Snapshrink

Thanks for considering it — here's everything you need, whether you're
fixing a typo or adding a feature.

## Before you write code

For anything beyond a small fix, **open an Issue first** describing what
you'd like to change. This avoids someone spending time on a Pull Request
for something that doesn't fit the project's direction.

## Reporting a bug

Open an [Issue](../../issues/new) with:
- What you did
- What you expected to happen
- What actually happened
- Your Windows version, and the Snapshrink version (Help → About)

## Suggesting a feature

Open an Issue describing the problem you're facing, not just the solution
you have in mind — it's easier to find the best fix when the underlying
need is clear.

## Making a code change (Pull Request)

1. Fork the repository (button top-right of the GitHub page)
2. Clone your fork to your computer
3. Create a branch for your change: `git checkout -b fix-thing`
4. Make your change
5. Test it: run `python -m sspack.engine --selftest` — all tests must pass
6. Commit and push to your fork
7. Open a Pull Request against `main` — describe what you changed and why

## Project structure, for orientation

```
sspack/
  engine.py        - the actual conversion logic (no GUI, no Windows-specific code)
  gui.py           - the window (CustomTkinter)
  daemon.py        - background tray icon + Ctrl+Alt+J hotkey
  contextmenu.py   - right-click menu registration
  config.py        - settings storage
  __main__.py      - routes command-line arguments to the right mode
installer/
  build_app.py     - packages everything into Snapshrink.exe (PyInstaller)
  Snapshrink.iss   - builds the installer (Inno Setup)
```

## Code style

Keep it simple and readable over clever. `engine.py` in particular has a
built-in self-test suite (`--selftest`) — if you touch conversion logic,
make sure it still passes, and add a new test case for whatever you fixed
or added.

## Questions

Open an Issue and tag it `question` — no need to email, GitHub is the whole
workflow for this project.
