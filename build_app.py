; ============================================================================
; Snapshrink installer  -  Inno Setup script
;
; Build order:
;   1. python installer\build_app.py     <- makes dist\Snapshrink\Snapshrink.exe
;   2. Open THIS file in Inno Setup, click Compile (or press F9)
;   3. The finished installer appears in installer\output\SnapshrinkSetup.exe
;
; What this installer does:
;   - Installs to a per-user folder (no admin rights needed)
;   - Adds a Start Menu shortcut called "Snapshrink"
;   - Registers the right-click context menu automatically
;   - Sets Snapshrink's background helper to start with Windows
;   - Uninstall reverses all of the above, and nothing else
; ============================================================================

#define MyAppName "Snapshrink"
#define MyAppVersion "1.26.00"
#define MyAppExeName "Snapshrink.exe"
#define MyAppSourceDir "dist\Snapshrink"

[Setup]
AppId={{8F2C1A4E-5B3D-4E6A-9C7F-1D2E3F4A5B6C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppName}
DefaultDirName={localappdata}\Programs\{#MyAppName}
; No admin prompt at all - installs to the user's own folder:
PrivilegesRequired=lowest
DisableProgramGroupPage=yes
OutputDir=output
OutputBaseFilename=SnapshrinkSetup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
; Uninstall entry that appears in "Add or remove programs":
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; Everything PyInstaller produced, copied as-is:
Source: "{#MyAppSourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Start Menu shortcut - opens the window
Name: "{userprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
; Desktop shortcut (optional tick-box during setup, see [Tasks] below)
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
; Auto-start entry: launches the background helper (tray + Ctrl+Alt+J) each
; time you log in to Windows. This is a normal Startup-folder shortcut, so
; it's easy for you to find, disable, or remove by hand later if you ever
; want to (right-click it in shell:startup -> Delete), independent of us.
Name: "{userstartup}\{#MyAppName} (background helper)"; \
    Filename: "{app}\{#MyAppExeName}"; Parameters: "--daemon"; \
    WorkingDir: "{app}"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Run]
; After copying files, before finishing: register the right-click menu.
; This calls Snapshrink.exe itself (no separate build step needed).
Filename: "{app}\{#MyAppExeName}"; Parameters: "--install-contextmenu"; \
    Flags: runhidden waituntilterminated

; Start the background helper immediately (so it's running right after
; install, without waiting for the next login):
Filename: "{app}\{#MyAppExeName}"; Parameters: "--daemon"; \
    Flags: nowait postinstall skipifsilent runasoriginaluser; \
    Description: "Start the background helper now (Ctrl+Alt+J)"

[UninstallRun]
; Order matters here:
;   1. Remove the right-click registry entries WHILE the exe still exists
;      (the uninstall command needs to run before its own files vanish).
;   2. Stop any running copy of Snapshrink so Windows can delete the files
;      (a running .exe can't be deleted - this releases the lock).
Filename: "{app}\{#MyAppExeName}"; Parameters: "--uninstall-contextmenu"; \
    Flags: runhidden waituntilterminated; RunOnceId: "UninstallCtxMenu"
Filename: "{cmd}"; Parameters: "/c taskkill /f /im {#MyAppExeName}"; \
    Flags: runhidden waituntilterminated; RunOnceId: "KillSnapshrink"

[Code]
// Nothing custom needed yet - Inno Setup's defaults handle everything above.
// (Kept as a placeholder section in case Phase 5 testing turns up an edge
// case that needs a bit of Pascal-script glue - e.g. detecting a previous
// install, or migrating settings - so we don't have to restructure the file.)
