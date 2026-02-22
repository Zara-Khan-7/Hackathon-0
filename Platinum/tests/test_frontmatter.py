"""Tests for YAML frontmatter parsing and writing."""

import tempfile
from pathlib import Path

import pytest

from src.utils.frontmatter import parse, dump, read_file, write_file


class TestParse:
    def test_basic_frontmatter(self):
        text = "---\ntitle: Test\npriority: high\n---\n\n# Body here"
        meta, body = parse(text)
        assert meta["title"] == "Test"
        assert meta["priority"] == "high"
        assert body == "# Body here"

    def test_no_frontmatter(self):
        text = "# Just a heading\n\nSome content."
        meta, body = parse(text)
        assert meta == {}
        assert body == text

    def test_empty_string(self):
        meta, body = parse("")
        assert meta == {}
        assert body == ""

    def test_frontmatter_with_list(self):
        text = "---\ntags:\n  - email\n  - urgent\nstatus: pending\n---\n\nContent"
        meta, body = parse(text)
        assert meta["tags"] == ["email", "urgent"]
        assert meta["status"] == "pending"
        assert body == "Content"

    def test_invalid_yaml(self):
        text = "---\n: invalid: yaml: [broken\n---\n\nBody"
        meta, body = parse(text)
        assert meta == {}

    def test_no_closing_delimiter(self):
        text = "---\ntitle: Test\nNo closing delimiter"
        meta, body = parse(text)
        assert meta == {}


class TestDump:
    def test_basic_dump(self):
        meta = {"title": "Test", "priority": "high"}
        body = "# Content"
        result = dump(meta, body)
        assert result.startswith("---\n")
        assert "title: Test" in result
        assert result.endswith("# Content")

    def test_empty_metadata(self):
        result = dump({}, "# Body only")
        assert result == "# Body only"
        assert "---" not in result


class TestRoundTrip:
    def test_parse_dump_roundtrip(self):
        meta = {"title": "Round Trip", "type": "email", "priority": 1}
        body = "# Task\n\nDo the thing."
        text = dump(meta, body)
        parsed_meta, parsed_body = parse(text)
        assert parsed_meta == meta
        assert parsed_body == body

    def test_file_roundtrip(self, tmp_path):
        filepath = tmp_path / "test.md"
        meta = {"title": "File Test", "tags": ["a", "b"]}
        body = "# Hello\n\nWorld."
        write_file(filepath, meta, body)

        read_meta, read_body = read_file(filepath)
        assert read_meta == meta
        assert read_body == body

    def test_read_nonexistent(self, tmp_path):
        meta, body = read_file(tmp_path / "nope.md")
        assert meta == {}
        assert body == ""
