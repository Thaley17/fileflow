#!/usr/bin/env python3
"""FileFlow - Tinder-style file sorter following Tiago Forte's CODE method.

Three-folder model:
  Source  — the folder you're evaluating (read from here)
  Inbox   — where "Keep" files move to (for later organizing)
  Archive — where rejected files move to
"""

import json
import mimetypes
import os
import shutil
import sys
import time
from pathlib import Path

from flask import Flask, jsonify, request, send_file, send_from_directory
from markupsafe import escape

try:
    import markdown
    HAS_MARKDOWN = True
except ImportError:
    HAS_MARKDOWN = False

try:
    from PIL import Image
    import pillow_heif
    pillow_heif.register_heif_opener()
    HAS_HEIF = True
except ImportError:
    HAS_HEIF = False

# --- Configuration ---
DEFAULT_SOURCE = os.path.expanduser("~/FileFlow/Inbox")
DEFAULT_INBOX = os.path.expanduser("~/FileFlow/Inbox")
DEFAULT_ARCHIVE = os.path.expanduser("~/FileFlow/Archive")
CONFIG_FILE = os.path.expanduser("~/.fileflow.json")
HOME_DIR = os.path.expanduser("~")

app = Flask(__name__, static_folder=None)

# Undo stack: list of (action_type, filename, dest_path, source_dir) tuples
undo_stack = []

# Mutable config — three distinct folders
config = {
    "source_dir": DEFAULT_SOURCE,
    "inbox_dir": DEFAULT_INBOX,
    "archive_dir": DEFAULT_ARCHIVE,
}


def load_config():
    """Load config from ~/.fileflow.json, falling back to env vars then defaults."""
    global config
    if os.path.isfile(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                saved = json.load(f)
            config["source_dir"] = saved.get("source_dir", saved.get("inbox_dir", DEFAULT_SOURCE))
            config["inbox_dir"] = saved.get("inbox_dir", DEFAULT_INBOX)
            config["archive_dir"] = saved.get("archive_dir", DEFAULT_ARCHIVE)
            return
        except (json.JSONDecodeError, IOError):
            pass
    # Fall back to env vars
    config["source_dir"] = os.environ.get("FILEFLOW_SOURCE", os.environ.get("FILEFLOW_INBOX", DEFAULT_SOURCE))
    config["inbox_dir"] = os.environ.get("FILEFLOW_INBOX", DEFAULT_INBOX)
    config["archive_dir"] = os.environ.get("FILEFLOW_ARCHIVE", DEFAULT_ARCHIVE)


def save_config():
    """Persist config to ~/.fileflow.json."""
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
    except IOError:
        pass


def ensure_dirs():
    os.makedirs(config["source_dir"], exist_ok=True)
    os.makedirs(config["inbox_dir"], exist_ok=True)
    os.makedirs(config["archive_dir"], exist_ok=True)


def get_files():
    """Return sorted list of files in the SOURCE folder (not directories)."""
    ensure_dirs()
    files = []
    try:
        for f in sorted(os.listdir(config["source_dir"])):
            full = os.path.join(config["source_dir"], f)
            if os.path.isfile(full):
                files.append(f)
    except PermissionError:
        pass
    return files


def file_info(filename):
    """Get metadata about a file in the source folder."""
    full = os.path.join(config["source_dir"], filename)
    if not os.path.isfile(full):
        return None
    stat = os.stat(full)
    mime, _ = mimetypes.guess_type(filename)
    ext = Path(filename).suffix.lower()

    if mime and mime.startswith("image/"):
        preview_type = "image"
    elif ext in (".heic", ".heif") and HAS_HEIF:
        preview_type = "image"
    elif ext == ".pdf":
        preview_type = "pdf"
    elif ext in (".md", ".markdown"):
        preview_type = "markdown"
    elif mime and mime.startswith("text/") or ext in (
        ".txt", ".py", ".js", ".ts", ".jsx", ".tsx", ".json", ".yaml", ".yml",
        ".toml", ".cfg", ".ini", ".sh", ".bash", ".zsh", ".css", ".html",
        ".xml", ".csv", ".log", ".env", ".gitignore", ".rs", ".go", ".rb",
        ".java", ".c", ".cpp", ".h", ".hpp", ".swift", ".kt", ".sql",
    ):
        preview_type = "text"
    else:
        preview_type = "binary"

    return {
        "name": filename,
        "size": stat.st_size,
        "size_human": human_size(stat.st_size),
        "modified": stat.st_mtime,
        "modified_human": time.strftime("%b %d, %Y %I:%M %p", time.localtime(stat.st_mtime)),
        "mime": mime or "application/octet-stream",
        "extension": ext,
        "preview_type": preview_type,
    }


def human_size(nbytes):
    for unit in ("B", "KB", "MB", "GB"):
        if abs(nbytes) < 1024:
            return f"{nbytes:.1f} {unit}"
        nbytes /= 1024
    return f"{nbytes:.1f} TB"


def is_safe_path(path):
    """Check that the path is under the user's home directory."""
    try:
        real = os.path.realpath(os.path.expanduser(path))
        return real.startswith(HOME_DIR)
    except (ValueError, OSError):
        return False


def move_file_safe(src, dest_dir, filename):
    """Move a file to dest_dir, handling name collisions. Returns final dest path."""
    dest = os.path.join(dest_dir, filename)
    if os.path.exists(dest):
        base, ext = os.path.splitext(filename)
        dest = os.path.join(dest_dir, f"{base}_{int(time.time())}{ext}")
    shutil.move(src, dest)
    return dest


# --- API Routes ---

@app.route("/")
def index():
    return send_from_directory(os.path.dirname(__file__), "index.html")


@app.route("/api/files")
def api_files():
    files = get_files()
    return jsonify({"files": files, "total": len(files)})


@app.route("/api/file/<path:filename>")
def api_file_info(filename):
    info = file_info(filename)
    if not info:
        return jsonify({"error": "File not found"}), 404
    return jsonify(info)


@app.route("/api/preview/<path:filename>")
def api_preview(filename):
    """Serve file content for preview from the source folder."""
    full = os.path.join(config["source_dir"], filename)
    if not os.path.isfile(full):
        return "Not found", 404

    real_source = os.path.realpath(config["source_dir"])
    real_file = os.path.realpath(full)
    if not real_file.startswith(real_source + os.sep) and real_file != real_source:
        return "Forbidden", 403

    mime, _ = mimetypes.guess_type(filename)
    ext = Path(filename).suffix.lower()

    if ext in (".md", ".markdown") and HAS_MARKDOWN:
        with open(full, "r", errors="replace") as f:
            content = f.read()
        html = markdown.markdown(content, extensions=["fenced_code", "tables", "codehilite"])
        return jsonify({"html": html, "raw": content})

    if mime and mime.startswith("text/") or ext in (
        ".txt", ".py", ".js", ".ts", ".jsx", ".tsx", ".json", ".yaml", ".yml",
        ".toml", ".cfg", ".ini", ".sh", ".bash", ".zsh", ".css", ".html",
        ".xml", ".csv", ".log", ".env", ".gitignore", ".rs", ".go", ".rb",
        ".java", ".c", ".cpp", ".h", ".hpp", ".swift", ".kt", ".sql", ".md",
    ):
        with open(full, "r", errors="replace") as f:
            content = f.read(500_000)
        return jsonify({"text": content})

    # HEIC/HEIF → JPEG conversion for browser preview
    if ext in (".heic", ".heif") and HAS_HEIF:
        try:
            import io
            img = Image.open(full)
            img = img.convert("RGB")
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=85)
            buf.seek(0)
            return send_file(buf, mimetype="image/jpeg")
        except Exception:
            pass  # Fall through to raw send

    return send_file(full, mimetype=mime or "application/octet-stream")


@app.route("/api/action", methods=["POST"])
def api_action():
    """Sort a file from source: 'keep' moves to inbox, 'archive' moves to archive."""
    data = request.json
    filename = data.get("filename")
    action = data.get("action")

    if not filename or action not in ("keep", "archive"):
        return jsonify({"error": "Invalid request"}), 400

    src = os.path.join(config["source_dir"], filename)
    if not os.path.isfile(src):
        return jsonify({"error": "File not found"}), 404

    real_source = os.path.realpath(config["source_dir"])
    real_file = os.path.realpath(src)
    if not real_file.startswith(real_source + os.sep):
        return jsonify({"error": "Forbidden"}), 403

    ensure_dirs()

    if action == "archive":
        dest = move_file_safe(src, config["archive_dir"], filename)
        undo_stack.append(("archive", filename, dest, config["source_dir"]))
        return jsonify({"status": "archived", "file": filename})
    else:
        # "keep" = move to inbox
        # If source IS the inbox, just skip (no-op)
        if os.path.realpath(config["source_dir"]) == os.path.realpath(config["inbox_dir"]):
            undo_stack.append(("keep_skip", filename, None, None))
            return jsonify({"status": "kept_in_place", "file": filename})
        else:
            dest = move_file_safe(src, config["inbox_dir"], filename)
            undo_stack.append(("keep_move", filename, dest, config["source_dir"]))
            return jsonify({"status": "kept", "file": filename})


@app.route("/api/undo", methods=["POST"])
def api_undo():
    """Undo the last action."""
    if not undo_stack:
        return jsonify({"error": "Nothing to undo"}), 400

    action_type, filename, dest_path, orig_dir = undo_stack.pop()

    if action_type in ("archive", "keep_move") and dest_path and os.path.isfile(dest_path):
        restore_path = os.path.join(orig_dir, filename)
        shutil.move(dest_path, restore_path)
        label = "unarchived" if action_type == "archive" else "unkept"
        return jsonify({"status": "undone", "action": label, "file": filename})
    elif action_type == "keep_skip":
        return jsonify({"status": "undone", "action": "unkept", "file": filename})

    return jsonify({"error": "Cannot undo"}), 400


@app.route("/api/stats")
def api_stats():
    """Get source/inbox/archive counts."""
    ensure_dirs()

    def count_files(d):
        try:
            return len([f for f in os.listdir(d) if os.path.isfile(os.path.join(d, f))])
        except PermissionError:
            return -1

    source_count = count_files(config["source_dir"])
    inbox_count = count_files(config["inbox_dir"])
    archive_count = count_files(config["archive_dir"])

    return jsonify({
        "source": source_count,
        "inbox": inbox_count,
        "archive": archive_count,
        "source_dir": config["source_dir"],
        "inbox_dir": config["inbox_dir"],
        "archive_dir": config["archive_dir"],
    })


# --- Config & Browse API ---

@app.route("/api/config")
def api_get_config():
    """Return current configuration."""
    return jsonify({
        "source_dir": config["source_dir"],
        "inbox_dir": config["inbox_dir"],
        "archive_dir": config["archive_dir"],
    })


@app.route("/api/config", methods=["POST"])
def api_set_config():
    """Update source/inbox/archive directories."""
    data = request.json
    changed = False

    for key in ("source_dir", "inbox_dir", "archive_dir"):
        if key in data and data[key]:
            path = os.path.expanduser(data[key])
            if not is_safe_path(path):
                return jsonify({"error": f"Path must be under your home directory: {path}"}), 400
            try:
                os.makedirs(path, exist_ok=True)
                os.listdir(path)
            except PermissionError:
                return jsonify({"error": f"Permission denied: {path}. macOS may block access to this folder."}), 400
            except OSError as e:
                return jsonify({"error": f"Cannot access {path}: {e}"}), 400
            config[key] = path
            changed = True

    if changed:
        ensure_dirs()
        save_config()
        undo_stack.clear()

    return jsonify({
        "status": "updated",
        "source_dir": config["source_dir"],
        "inbox_dir": config["inbox_dir"],
        "archive_dir": config["archive_dir"],
    })


@app.route("/api/browse")
def api_browse():
    """List directories under a given path for the folder picker."""
    path = request.args.get("path", HOME_DIR)
    path = os.path.expanduser(path)

    if not is_safe_path(path):
        path = HOME_DIR

    if not os.path.isdir(path):
        path = HOME_DIR

    real_path = os.path.realpath(path)
    parent = os.path.dirname(real_path)
    if not is_safe_path(parent):
        parent = HOME_DIR

    dirs = []
    try:
        for entry in sorted(os.listdir(real_path)):
            if entry.startswith("."):
                continue
            full = os.path.join(real_path, entry)
            if os.path.isdir(full):
                try:
                    file_count = len([f for f in os.listdir(full) if os.path.isfile(os.path.join(full, f))])
                except PermissionError:
                    file_count = -1
                dirs.append({"name": entry, "path": full, "file_count": file_count})
    except PermissionError:
        pass

    return jsonify({
        "current": real_path,
        "parent": parent,
        "directories": dirs,
        "home": HOME_DIR,
    })


if __name__ == "__main__":
    load_config()
    ensure_dirs()
    port = int(os.environ.get("PORT", sys.argv[1] if len(sys.argv) > 1 else 5050))
    print(f"\n  FileFlow - Tinder-style File Sorter")
    print(f"  ────────────────────────────────────")
    print(f"  Source:  {config['source_dir']}")
    print(f"  Inbox:   {config['inbox_dir']}")
    print(f"  Archive: {config['archive_dir']}")
    print(f"  Config:  {CONFIG_FILE}")
    print(f"  UI:      http://localhost:{port}")
    print(f"\n  Controls: → or L = Keep (→ Inbox)  |  ← or H = Archive  |  Z = Undo  |  S = Settings\n")
    app.run(host="127.0.0.1", port=port, debug=False)
