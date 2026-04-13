# FileFlow

A local file sorter with a Tinder-style swipe interface. Point it at any folder, preview each file, and sort them into an Inbox or Archive with keyboard shortcuts.

Built around the [PARA method](https://fortelabs.com/blog/para/) — capture everything, then organize.

## How it works

```
Source folder          Inbox folder         Archive folder
(you evaluate)    →    (files you keep)     (files you dismiss)
~/Documents            ~/FileFlow/Inbox     ~/FileFlow/Archive
```

You see each file one at a time with a live preview. Press **right** to keep it or **left** to archive it. Every file leaves the source folder — nothing stays behind.

## Install

**Requirements:** Python 3.7+ (macOS, Linux, WSL)

```bash
git clone https://github.com/YOUR_USERNAME/fileflow.git
cd fileflow
bash install.sh
```

That's it. The installer:
- Installs Python packages (`flask`, `markdown`)
- Adds `fileflow` to your PATH
- Creates `~/FileFlow/Inbox` and `~/FileFlow/Archive`

## Usage

```bash
fileflow            # start server + open browser
fileflow start      # start server in background only
fileflow stop       # stop the server
fileflow status     # show running state + folder stats
fileflow help       # all commands
```

### Keyboard shortcuts

| Key | Action |
|-----|--------|
| `→` or `L` | Keep — move file to Inbox |
| `←` or `H` | Archive — move file to Archive |
| `Z` | Undo last action |
| `S` | Open settings panel |
| `Esc` | Close settings |

### Settings

Click the gear icon (or press `S`) to change folders at any time:

- **Source** — the folder you want to evaluate
- **Inbox** — where "keep" files go
- **Archive** — where dismissed files go

Settings persist to `~/.fileflow.json` and survive restarts.

### File previews

FileFlow previews files inline — no need to open them separately:

- **Markdown** — rendered with headings, lists, code blocks
- **Code** — syntax-highlighted for Python, JavaScript, shell, etc.
- **JSON/YAML/config** — formatted text preview
- **Images** — displayed inline (PNG, JPG, GIF, SVG, WebP)
- **PDFs** — embedded viewer
- **Everything else** — file type badge + metadata

## Project structure

```
fileflow/
├── app.py           # Flask backend — API + file operations
├── index.html       # Frontend — single-file UI
├── fileflow         # CLI launcher script
├── install.sh       # One-command installer
├── start.sh         # Quick foreground start
├── requirements.txt # Python dependencies
└── README.md
```

## Configuration

FileFlow stores its config at `~/.fileflow.json`:

```json
{
  "source_dir": "/Users/you/Documents",
  "inbox_dir": "/Users/you/FileFlow/Inbox",
  "archive_dir": "/Users/you/FileFlow/Archive"
}
```

You can edit this file directly or use the in-app settings panel.

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FILEFLOW_PORT` | `5050` | Server port |
| `FILEFLOW_SOURCE` | `~/FileFlow/Inbox` | Initial source folder |
| `FILEFLOW_INBOX` | `~/FileFlow/Inbox` | Initial inbox folder |
| `FILEFLOW_ARCHIVE` | `~/FileFlow/Archive` | Initial archive folder |

Environment variables are only used if `~/.fileflow.json` doesn't exist.

## For AI agents

If you're an AI agent setting this up for a user, here's what to do:

```bash
# 1. Clone and install
git clone https://github.com/YOUR_USERNAME/fileflow.git
cd fileflow
bash install.sh

# 2. (Optional) Point it at a specific folder
cat > ~/.fileflow.json << 'EOF'
{
  "source_dir": "/Users/USERNAME/Documents",
  "inbox_dir": "/Users/USERNAME/FileFlow/Inbox",
  "archive_dir": "/Users/USERNAME/FileFlow/Archive"
}
EOF

# 3. Launch
fileflow
```

### Troubleshooting

| Problem | Fix |
|---------|-----|
| `command not found: fileflow` | Run `bash install.sh` again, or add `~/.local/bin` to your PATH |
| Port 5050 in use | `FILEFLOW_PORT=5051 fileflow` or kill the existing process |
| `pip3 install` fails | Try `python3 -m pip install flask markdown markupsafe` |
| Permission denied on a folder | macOS restricts `~/Downloads`, `~/Desktop` etc. — grant Terminal full disk access in System Settings > Privacy, or use a different folder |
| Server won't start | Check `/tmp/fileflow.log` for errors |
| Blank screen in browser | Wait 2 seconds for the server to boot, then refresh |

## How it's built

- **Backend:** Python + Flask — serves the UI and handles file move/undo operations
- **Frontend:** Single HTML file — vanilla JS, CSS animations, no build step
- **Storage:** Files are moved with `shutil.move`, config saved as JSON
- **Preview:** Text files read and served as JSON, images/PDFs served directly
- **Zero cloud dependencies** — everything runs locally, nothing leaves your machine

## License

MIT
