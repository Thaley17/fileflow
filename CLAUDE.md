# CLAUDE.md — Agent context for FileFlow

## What is this?

FileFlow is a local web app for sorting files. It shows files from a source folder one at a time with a preview, and the user swipes right (keep → inbox) or left (archive). Think Tinder for files.

## Tech stack

- **Backend:** Python 3 + Flask (single file: `app.py`)
- **Frontend:** Single HTML file with inline CSS/JS (`index.html`)
- **CLI:** Bash script (`fileflow`)
- **Config:** `~/.fileflow.json`
- **No build step.** No bundler. No node_modules. Just Python + a browser.

## How to run it

```bash
bash install.sh    # first time only
fileflow           # starts server on :5050 and opens browser
```

Or manually:
```bash
pip3 install flask markdown markupsafe
python3 app.py 5050
# open http://localhost:5050
```

## Architecture

### Three-folder model

- **Source** — folder being evaluated (files are read from here)
- **Inbox** — where "keep" moves files (right swipe / L key)
- **Archive** — where "archive" moves files (left swipe / H key)

If source === inbox (same folder), "keep" skips instead of moving.

### API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Serves `index.html` |
| GET | `/api/files` | List files in source folder |
| GET | `/api/file/<name>` | File metadata (size, type, preview type) |
| GET | `/api/preview/<name>` | File content for preview |
| POST | `/api/action` | `{filename, action: "keep"|"archive"}` |
| POST | `/api/undo` | Undo last action |
| GET | `/api/stats` | Source/inbox/archive counts + paths |
| GET | `/api/config` | Current folder config |
| POST | `/api/config` | Update folder config |
| GET | `/api/browse?path=...` | List subdirectories for folder picker |

### Key design decisions

- All files served from `app.py` — no static file server
- Undo stack is in-memory (resets on server restart)
- Config persists to `~/.fileflow.json`
- Security: all paths must be under `$HOME`, path traversal blocked
- macOS permission errors handled gracefully (e.g. ~/Downloads)
- Frontend polls every 5s for new files when source is empty

## Common tasks

### Change the default port
```bash
FILEFLOW_PORT=8080 fileflow
```

### Add a new file type preview
1. In `app.py`, add the extension to the `file_info()` function's type detection
2. In `app.py`, add handling in `api_preview()` if it needs special serving
3. In `index.html`, add a case in `loadFilePreview()` for the new preview type
4. In `index.html`, add a label in `getTypeLabel()` for the file icon badge

### Add a new keyboard shortcut
In `index.html`, add a case to the `keydown` event listener (~line 830).

### Change the color scheme
All colors are CSS custom properties in `:root` at the top of `index.html`.
