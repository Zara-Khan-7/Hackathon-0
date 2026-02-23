"""Parse and write YAML frontmatter in Markdown files.

Format:
    ---
    key: value
    ---
    # Body content here
"""

import yaml
from pathlib import Path
from typing import Any


def parse(text: str) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter from markdown text.

    Returns (metadata_dict, body_string). If no frontmatter found,
    returns ({}, original_text).
    """
    text = text.strip()
    if not text.startswith("---"):
        return {}, text

    # Find closing ---
    end = text.find("---", 3)
    if end == -1:
        return {}, text

    yaml_block = text[3:end].strip()
    body = text[end + 3:].strip()

    try:
        metadata = yaml.safe_load(yaml_block)
        if not isinstance(metadata, dict):
            return {}, text
    except yaml.YAMLError:
        return {}, text

    return metadata, body


def dump(metadata: dict[str, Any], body: str) -> str:
    """Combine metadata dict and body into frontmatter markdown string."""
    if not metadata:
        return body

    yaml_str = yaml.dump(metadata, default_flow_style=False, sort_keys=False).strip()
    return f"---\n{yaml_str}\n---\n\n{body}"


def read_file(filepath: str | Path) -> tuple[dict[str, Any], str]:
    """Read a markdown file and return (metadata, body)."""
    path = Path(filepath)
    if not path.exists():
        return {}, ""
    text = path.read_text(encoding="utf-8")
    return parse(text)


def write_file(filepath: str | Path, metadata: dict[str, Any], body: str) -> None:
    """Write metadata + body to a markdown file with frontmatter."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    content = dump(metadata, body)
    path.write_text(content, encoding="utf-8")
