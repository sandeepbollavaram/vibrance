# Vibrance

> **Photo editor. Batch processor. Compressor.**
> A production-grade desktop image editor built with **PySide6** and **OpenCV**.

[![CI](https://github.com/sandeepbollavaram/image_editor_python/actions/workflows/ci.yml/badge.svg)](https://github.com/sandeepbollavaram/image_editor_python/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/sandeepbollavaram/image_editor_python?label=download)](https://github.com/sandeepbollavaram/image_editor_python/releases/latest)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**One-click download:** **<https://sandeepbollavaram.github.io/image_editor_python/>**
**All releases:** <https://github.com/sandeepbollavaram/image_editor_python/releases>

---

## Features

**Tone & color**
- Exposure, brightness, contrast
- Highlights / shadows (luminance-masked)
- Saturation, vibrance
- Temperature & tint white balance
- 3D LUT (`.cube`) import

**Smart compression** *(new)*
- Target a file-size ceiling in KB — Vibrance binary-searches encoder quality to land at or just under it
- JPEG / WebP / PNG, with progressive JPEG + optimization on by default
- Optional: cap long edge for web use, strip EXIF / metadata
- Built into `Ctrl+E` **Export / Compress…**

**Detail & geometry**
- Gaussian blur, unsharp-mask sharpen
- Rotate 90 / 180 / 270, flip H / V
- Drag-to-select crop dialog (in-window — no OpenCV popup)

**Workflow**
- Batch edit any number of files in a background thread (UI stays responsive)
- Live preview with 80 ms debounce
- Undo / redo (`Ctrl+Z` / `Ctrl+Y`) up to 100 steps
- Save & load presets as JSON
- Draggable before/after split view (`Ctrl+B`)
- Live RGB + luminance histogram
- Output goes to `<source>/edited/` — original files are never touched
- Drag-and-drop a folder or image onto the window
- Rotating log file in your per-user app-data directory

**Engineering**
- `src/` layout, proper package, PEP 621 `pyproject.toml`
- Type hints, dataclasses, pure-function core (no Qt in `core/`)
- Unit tests with pytest, GitHub Actions CI (Linux + Windows, Python 3.10/3.11/3.12)
- Ruff + Black configured
- Inno Setup installer template
- MIT licensed

---

## Get Vibrance

### Easiest — Windows installer

1. Go to the [download center](https://sandeepbollavaram.github.io/image_editor_python/) or the [latest release](https://github.com/sandeepbollavaram/image_editor_python/releases/latest).
2. Download `Vibrance_Setup_<version>.exe`.
3. Run it. The installer:
   - Installs to `Program Files\Vibrance`
   - Creates a **Desktop shortcut** ✓
   - Creates a **Start Menu** entry ✓
   - Registers Vibrance as an **"Open with…"** option for `.jpg / .png / .webp / .tif`
   - Adds an **Uninstaller**

### Portable

Grab `Vibrance.exe` from the release assets — single file, no install, no admin.

### From source (macOS / Linux / development)

```powershell
git clone https://github.com/sandeepbollavaram/image_editor_python.git
cd image_editor_python
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m image_editor
```

After `pip install -e .` you can also launch it as `vibrance` or `vibrance-gui`.

### Linux dependencies

PySide6 needs a few system libs on bare Ubuntu/Debian:

```bash
sudo apt install -y libegl1 libxkbcommon0 libxcb-cursor0 libgl1
```

---

## Project layout

```
image_editor_python/
├── src/image_editor/
│   ├── app.py                # QApplication bootstrap + theme
│   ├── config.py             # EditParams, ExportOptions, paths
│   ├── core/                 # Pure NumPy/OpenCV — no Qt
│   │   ├── image_io.py       # unicode-safe load/save
│   │   ├── filters.py        # every adjustment + histogram + LUT
│   │   ├── pipeline.py       # ordered apply_all
│   │   ├── history.py        # undo/redo stack
│   │   └── presets.py        # JSON preset I/O
│   ├── ui/
│   │   ├── main_window.py    # composes panels
│   │   ├── theme.py          # Fusion + dark QSS
│   │   └── widgets/          # zoomable_view, split_compare, file_panel,
│   │                          edit_panel, output_panel, slider_row,
│   │                          histogram, crop_dialog
│   ├── workers/batch_worker.py  # QThread for batch edits
│   ├── utils/logger.py       # rotating logger
│   └── resources/styles.qss  # design tokens & component styles
├── tests/                    # pytest, runs headless in CI
├── .github/workflows/ci.yml  # lint + test on Linux & Windows
├── installer.iss             # Inno Setup template
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── LICENSE                   # MIT
└── README.md
```

---

## Keyboard shortcuts

| Action                | Shortcut       |
|-----------------------|----------------|
| Apply edits to batch  | `Ctrl+Enter`   |
| Undo                  | `Ctrl+Z`       |
| Redo                  | `Ctrl+Y`       |
| Reset all sliders     | `Ctrl+R`       |
| Fit preview to window | `Ctrl+0`       |
| Compare before/after  | `Ctrl+B`       |
| Double-click preview  | Fit            |
| Mouse wheel on preview| Zoom in/out    |

---

## Build the Windows installer locally

One-shot build:

```powershell
.\build.ps1                 # builds dist\Vibrance.exe and dist\Vibrance_Setup_1.0.0.exe
.\build.ps1 -Version 1.2.0  # bump the installer version
.\build.ps1 -SkipInstaller  # EXE only, no Inno Setup needed
```

Requires Inno Setup 6 on PATH (`iscc`) — install from <https://jrsoftware.org/isinfo.php>.

## Cut a public release (automated)

```powershell
git tag v1.0.0
git push origin v1.0.0
```

`.github/workflows/release.yml` runs on the tag: a Windows runner builds the EXE
with PyInstaller, compiles the Inno Setup installer, computes a SHA-256, creates
a GitHub Release, and uploads:

- `Vibrance_Setup_1.0.0.exe` (installer)
- `Vibrance.exe` (portable)
- `SHA256SUMS.txt`

The download center at <https://sandeepbollavaram.github.io/image_editor_python/>
auto-detects the new release and rewrites its download buttons to point at the
exact installer asset — no edits needed.

## Replace the placeholder app icon

A scripted placeholder lives at `src/image_editor/resources/app.ico`. To use
your own artwork:

1. Drop a 1024×1024 PNG at the repo root as `vibrance.png` (or any path you like).
2. Run:
   ```powershell
   .\.venv\Scripts\python.exe scripts\make_icon.py
   ```
3. Commit the regenerated `.ico`.

Or just replace `src/image_editor/resources/app.ico` directly with your own
multi-resolution `.ico` file (sizes 16, 24, 32, 48, 64, 128, 256).

---

## Development

```powershell
pip install -r requirements-dev.txt

# Tests (headless)
$env:QT_QPA_PLATFORM = "offscreen"
pytest -q

# Lint & format
ruff check src tests
black src tests
```

---

## Kairo MCP — used during development of this project

This repo is also a **live test bed for [Kairo](https://github.com/sandeepbollavaram/Kairo)**,
an MCP server that gives Claude Code (and any other MCP-capable agent) persistent
session memory, repo intelligence, and checkpointing — so a coding agent can
resume work after a context reset without rescanning the tree.

### Why Kairo here

The 1.0 refactor of this app (splitting the 386-line `main.py` into a real
`src/` package with `core/`, `ui/`, `workers/`, tests, and CI) was driven inside
Claude Code with Kairo MCP attached. Every decision, file change, and checkpoint
was logged to Kairo so a follow-up session could pick up where the previous one
left off. If you want to dogfood Kairo on a non-trivial refactor, this repo is a
good reference.

### Connect Kairo to Claude Code

1. Clone and install Kairo (see Kairo README for current install command).
2. Add it to Claude Code's MCP config (`.mcp.json` at the repo root, or your
   global Claude config). Minimal example:

   ```json
   {
     "mcpServers": {
       "kairo": {
         "command": "node",
         "args": ["path/to/kairo/dist/server.js"],
         "env": {
           "KAIRO_PROJECT_ROOT": "${workspaceFolder}"
         }
       }
     }
   }
   ```

3. Restart Claude Code. Kairo tools will appear under `mcp__kairo__*`.

### Tools to call (and when)

| Kairo tool                  | When to call                                                    |
|-----------------------------|------------------------------------------------------------------|
| `kairo_session_start`       | First call of every session. Returns the continuation brief.    |
| `kairo_repo_scan`           | Once per repo. Cached after — don't force a rescan.             |
| `kairo_record`              | After each decision, file change, or recoverable error.         |
| `kairo_assess`              | Before risky/destructive changes (returns ALLOW/CAUTION/HOLD).  |
| `kairo_checkpoint`          | At logical breakpoints, or on a `CHECKPOINT_NOW` directive.     |
| `kairo_brief`               | Begin of a *resumed* session — get the tiny/normal/deep brief.  |
| `kairo_session_status`      | Sanity check: am I still in the session I think I'm in?         |
| `kairo_session_end`         | End of a wrap-up session.                                       |

### Smoke test

Inside Claude Code, in this repo:

```
Use the Kairo MCP. Call kairo_session_start with agent="claude-code" and
task="smoke test". Then call kairo_repo_intel. Then call kairo_record with
kind="note" and item="kairo connected from image_editor_python".
```

You should see a session ID, a cached repo-intel summary, and a recorded note.
If any of those fail, check Claude Code's MCP logs.

---

## Roadmap

- [x] Smart compression with target-size mode
- [x] One-click download center (GitHub Pages)
- [x] Automated release builds (GitHub Actions)
- [ ] Curves / Levels tool
- [ ] Watch-folder mode (auto-process newly added files)
- [ ] Side-by-side multi-image compare grid
- [ ] EXIF read + preserve on save (currently strip-only)
- [ ] Per-image sidecar `.json` edit history
- [ ] Plugin hook so new filters drop into `core/filters.py` and auto-appear
- [ ] AVIF export (smaller files than WebP at equal quality)
- [ ] macOS `.app` bundle and Linux `.AppImage`
- [ ] Code-signed installer (no SmartScreen warning)

---

## License

MIT © Sandeep Bollavaram. See [LICENSE](LICENSE).

---

<sub>Vibrance is a hobby project. If you ship a derivative, a link back to the
GitHub repo is appreciated but not required.</sub>
