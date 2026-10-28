import sys

import pytest

from coppermind.tools import ToolError, build_registry, list_files, read_file, get_current_datetime, write_to_file, append_to_file, create_file

import re

from pathlib import Path

@pytest.fixture
def notes_root(tmp_path):
    """A fake notes folder with a nested file, a hidden file, and a file outside it."""
    root = tmp_path / "notes"
    (root / "ideas").mkdir(parents=True)
    (root / "groceries.md").write_text("eggs\nmilk\n", encoding="utf-8")
    (root / "ideas" / "movie.md").write_text("scratch notes", encoding="utf-8")
    (root / ".hidden.md").write_text("should not be listed.", encoding="utf-8")
    (tmp_path / "secret.txt").write_text("outside teh root", encoding="utf-8")
    return root


def test_list_files_returns_sorted_relative_paths(notes_root):
    assert list_files(notes_root) == "groceries.md\nideas/movie.md"


def test_list_files_refuses_a_missing_folder(tmp_path):
    with pytest.raises(ToolError, match="not found"):
        list_files(tmp_path / "does-not-exist")


def test_read_file_returns_contents(notes_root):
    assert read_file(notes_root, "groceries.md") == "eggs\nmilk\n"


def test_read_file_allows_paths_that_resolve_inside(notes_root):
    assert read_file(notes_root, "ideas/../groceries.md") == "eggs\nmilk\n"


@pytest.mark.parametrize("bad_path", ["../secret.txt", "../notes_private/file.md"])
def test_read_file_refuses_paths_outside_root(notes_root, bad_path):
    with pytest.raises(ToolError, match="outside"):
        read_file(notes_root, bad_path)


def test_read_file_refuses_absolute_paths_outside_root(notes_root, tmp_path):
    secret = tmp_path / "secret.txt"
    with pytest.raises(ToolError, match="outside"):
        read_file(notes_root, str(secret))


def test_read_file_refuses_symlink_escape(notes_root, tmp_path):
    link = notes_root / "sneaky.md"
    try:
        link.symlink_to(tmp_path / "secret.txt")
    except OSError:
        pytest.skip("creating symlinks needs Developer Mode or admin on Windows")

    with pytest.raises(ToolError, match="outside"):
        read_file(notes_root, "sneaky.md")


def test_read_file_refuses_folders_and_missing_files(notes_root):
    with pytest.raises(ToolError, match="Not a file"):
        read_file(notes_root, "ideas")
    with pytest.raises(ToolError, match="not found"):
        read_file(notes_root, "missing.md")


def test_read_file_refuses_binary_files(notes_root):
    (notes_root / "image.bin").write_bytes(b"\xff\xfe\x00\x81")
    with pytest.raises(ToolError, match="Not a text file"):
        read_file(notes_root, "image.bin")


def test_read_file_truncates_long_files(notes_root):
    result = read_file(notes_root, "groceries.md", max_chars=4)
    assert result.startswith("eggs\n[Truncated")


def test_registry_keys_match_tool_names(notes_root):
    registry = build_registry(notes_root)
    assert set(registry) == {"list_files", "read_file", "get_current_datetime", "write_to_file", "append_to_file", "create_file"}
    for name, tool in registry.items():
        assert tool.schema()["function"]["name"] == name


def test_registry_schemas_have_openai_shape(notes_root):
    for tool in build_registry(notes_root).values():
        schema = tool.schema()
        assert schema["type"] == "function"
        assert schema["function"]["description"]
        assert schema["function"]["parameters"]["type"] == "object"


def test_file_tools_are_read_only(notes_root):
    for tool in build_registry(notes_root).values():
        assert tool.writes is False


def test_registry_tools_run_against_the_bound_root(notes_root):
    registry = build_registry(notes_root)
    assert registry["list_files"].function() == "groceries.md\nideas/movie.md"
    assert registry["read_file"].function(path="groceries.md") == "eggs\nmilk\n"


def test_model_cannot_pass_its_own_root(notes_root, tmp_path):
    read = build_registry(notes_root)["read_file"].function
    with pytest.raises(TypeError):
        read(path="secret.txt", root=tmp_path)


@pytest.mark.skipif(sys.platform != "win32", reason="backslash is only a separator on Windows")
def test_read_file_refuses_windows_style_traversal(notes_root):
    with pytest.raises(ToolError, match="outside"):
        read_file(notes_root, r"..\secret.txt")


@pytest.mark.parametrize("hidden_path", [".hidden.md", ".git/config", "ideas/.env"])
def test_read_file_refuses_hidden_files(notes_root, hidden_path):
    target = notes_root / hidden_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("TOKEN=secret", encoding="utf-8")
    with pytest.raises(ToolError, match="Hidden files"):
        read_file(notes_root, hidden_path)


def test_list_files_skips_symlinks_that_escape(notes_root, tmp_path):
    try:
        (notes_root / "sneaky.md").symlink_to(tmp_path / "secret.txt")
    except OSError:
        pytest.skip("creating symlinks needs Developer Mode or admin on Windows")

    assert "sneaky.md" not in list_files(notes_root)

def test_get_current_datetime_format():
    result = get_current_datetime()
    assert re.fullmatch(r"\w+, \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \(UTC[+-]\d{4}\)", result)

def test_write_file(notes_root, tmp_path):
    file_to_write = "test_write.md"
    content = "Hello World!"
    expected_path = tmp_path / "notes" / "test_write.md"
    file = write_to_file(notes_root, file_to_write, content)

    assert expected_path.is_file()
    assert expected_path.read_text(encoding="utf-8") == content

def test_append_to_file(notes_root, tmp_path):
    file_to_write = "test_write.md"
    path = tmp_path / "notes" / file_to_write
    write_content = "Hello World!"
    _ = write_to_file(notes_root, file_to_write, write_content)
    append_content = "My name is Copper."
    _ = append_to_file(notes_root, file_to_write, append_content)

    assert path.is_file()
    assert path.read_text() == write_content + append_content

def test_create_file(notes_root, tmp_path):
    file_to_create = "test_create.md"
    expected_path = tmp_path / "notes" / file_to_create
    _ = create_file(notes_root, file_to_create)

    assert expected_path.is_file()
    


    

