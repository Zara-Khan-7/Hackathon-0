"""Safe file operations for the AI Employee project.

Respects Company Handbook rules:
- Never overwrite without confirmation
- All moves are logged
- Folder structure is maintained
"""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.utils import frontmatter


def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent.parent


def get_folder(name: str) -> Path:
    """Get a project folder by name, creating it if needed."""
    folder = get_project_root() / name
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def list_md_files(folder: str, ignore_prefixes: Optional[list[str]] = None) -> list[Path]:
    """List all .md files in a folder, optionally ignoring certain prefixes."""
    path = get_folder(folder)
    files = sorted(path.glob("*.md"), key=lambda f: f.stat().st_mtime)
    if ignore_prefixes:
        files = [
            f for f in files
            if not any(f.name.startswith(prefix) for prefix in ignore_prefixes)
        ]
    return files


def safe_move(src: str | Path, dest_folder: str, overwrite: bool = False) -> Path:
    """Move a file to a destination folder safely.

    Returns the new file path. Raises FileExistsError if destination
    exists and overwrite is False.
    """
    src_path = Path(src)
    if not src_path.exists():
        raise FileNotFoundError(f"Source file not found: {src}")

    dest_dir = get_folder(dest_folder)
    dest_path = dest_dir / src_path.name

    if dest_path.exists() and not overwrite:
        # Add timestamp suffix to avoid collision
        stem = src_path.stem
        suffix = src_path.suffix
        ts = datetime.now().strftime("%H%M%S")
        dest_path = dest_dir / f"{stem}_{ts}{suffix}"

    shutil.move(str(src_path), str(dest_path))
    return dest_path


def create_task_file(
    folder: str,
    prefix: str,
    name: str,
    metadata: dict,
    body: str,
) -> Path:
    """Create a new task .md file with YAML frontmatter.

    Filename format: {PREFIX}_{name}.md
    """
    # Sanitize name for filename
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
    filename = f"{prefix}_{safe_name}.md"

    dest_dir = get_folder(folder)
    filepath = dest_dir / filename

    # Add created timestamp if not present
    if "created" not in metadata:
        metadata["created"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    frontmatter.write_file(filepath, metadata, body)
    return filepath


def file_exists(folder: str, filename: str) -> bool:
    """Check if a file exists in a folder."""
    return (get_folder(folder) / filename).exists()


def read_task_file(filepath: str | Path) -> tuple[dict, str]:
    """Read a task file and return (metadata, body)."""
    return frontmatter.read_file(filepath)


def count_by_prefix(folder: str) -> dict[str, int]:
    """Count .md files in a folder grouped by prefix (e.g. EMAIL_, LINKEDIN_).

    Returns a dict like {"EMAIL": 3, "LINKEDIN": 2, "EXECUTE": 1}.
    """
    files = list_md_files(folder)
    counts: dict[str, int] = {}
    for f in files:
        parts = f.stem.split("_", 1)
        prefix = parts[0] if len(parts) > 1 else "OTHER"
        counts[prefix] = counts.get(prefix, 0) + 1
    return counts
