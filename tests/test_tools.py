import re
import sys

import pytest

from coppermind.tools import ToolError, build_registry
from coppermind.tools import files as files_module
from coppermind.tools.core import get_current_datetime
from coppermind.tools.files import (
    append_to_file,
    copy_file,
    copy_folder,
    create_file,
    delete_file,
    list_files,
    list_folders,
    move_file,
    move_folder,
    read_file,
    write_to_file,
)


@pytest.fixture
def notes_root(tmp_path):
    """A fake notes folder with a nested file, a hidden file, and a file outside it."""
    root = tmp_path / "notes"
    (root / "ideas").mkdir(parents=True)
    (root / "things").mkdir(parents=True)
    (root / "stuff").mkdir(parents=True)
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

def test_list_folders_returns_sorted_relative_paths(notes_root):
    assert list_folders(notes_root) == "ideas\nstuff\nthings"


def test_list_folders_refuses_a_missing_folder(tmp_path):
    with pytest.raises(ToolError, match="not found"):
        list_folders(tmp_path / "does-not-exist")


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
    assert set(registry) == {
        "list_files",
        "list_folders", 
        "read_file",
        "copy_file",
        "move_file", 
        "get_current_datetime", 
        "write_to_file", 
        "append_to_file", 
        "create_file",
        "delete_file",
        "create_folder",
        "copy_folders",
        "move_folder",
        "save_memory",
    }
    for name, tool in registry.items():
        assert tool.schema()["function"]["name"] == name


def test_registry_schemas_have_openai_shape(notes_root):
    for tool in build_registry(notes_root).values():
        schema = tool.schema()
        assert schema["type"] == "function"
        assert schema["function"]["description"]
        assert schema["function"]["parameters"]["type"] == "object"


def test_only_reading_file_tools_are_read_only(notes_root):
    read_only = {"list_files", "list_folders", "read_file"}
    for tool in build_registry(notes_root).values():
        if tool.group == "files":
            assert tool.writes is (tool.name not in read_only)


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
    write_to_file(notes_root, file_to_write, content)

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

def test_delete_file(notes_root, tmp_path):
    file_to_delete = "test_del.md"
    _ = create_file(notes_root, file_to_delete)
    expected_path = tmp_path / "notes" / file_to_delete

    assert expected_path.is_file()
    _ = delete_file(notes_root, file_to_delete)

    assert expected_path.exists() == False

def test_copy_file(notes_root, tmp_path):
    source_file = tmp_path / "notes" / "ideas/movie.md"
    destination_path = tmp_path / "notes" / "things/movie.md"
    assert source_file.is_file()

    _ = copy_file(notes_root, source_file, destination_path)

    assert destination_path.is_file()

def test_move_file(notes_root, tmp_path):
    source_file = tmp_path / "notes" / "ideas/movie.md"
    destination_path = tmp_path / "notes" / "stuff/movie.md"
    assert source_file.is_file()

    _ = move_file(notes_root, source_file, destination_path)

    assert source_file.exists() == False
    assert destination_path.is_file()


# --- No overwriting ---------------------------------------------------------

@pytest.mark.parametrize("tool", [copy_file, move_file])
def test_copy_and_move_file_refuse_to_overwrite(notes_root, tool):
    (notes_root / "things" / "movie.md").write_text("keep me", encoding="utf-8")

    with pytest.raises(ToolError, match="already exists"):
        tool(notes_root, "ideas/movie.md", "things/movie.md")

    assert (notes_root / "things" / "movie.md").read_text(encoding="utf-8") == "keep me"
    assert (notes_root / "ideas" / "movie.md").is_file()


def test_copy_file_into_an_existing_folder_keeps_the_name(notes_root):
    assert copy_file(notes_root, "groceries.md", "things") == "Copied groceries.md to things/groceries.md"
    assert (notes_root / "things" / "groceries.md").is_file()


def test_move_file_creates_missing_parent_folders(notes_root):
    move_file(notes_root, "groceries.md", "archive/2026/groceries.md")
    assert (notes_root / "archive" / "2026" / "groceries.md").is_file()


# --- Folders ----------------------------------------------------------------

def test_move_folder_to_a_new_path_creates_missing_folders(notes_root):
    result = move_folder(notes_root, "ideas", "archive/old-ideas")

    assert result == "Moved ideas to archive/old-ideas"
    assert (notes_root / "archive" / "old-ideas" / "movie.md").is_file()
    assert not (notes_root / "ideas").exists()


def test_move_folder_into_an_existing_folder(notes_root):
    move_folder(notes_root, "ideas", "things")
    assert (notes_root / "things" / "ideas" / "movie.md").is_file()


def test_copy_folder_to_a_new_path(notes_root):
    copy_folder(notes_root, "ideas", "backup/ideas")
    assert (notes_root / "backup" / "ideas" / "movie.md").is_file()
    assert (notes_root / "ideas" / "movie.md").is_file()


@pytest.mark.parametrize("tool", [copy_folder, move_folder])
@pytest.mark.parametrize(
    "source, destination",
    [
        ("ideas", "ideas"),        # would land at ideas/ideas
        ("ideas", "ideas/inner"),  # a new folder inside the source
        (".", "ideas"),            # the whole notes folder into one of its own folders
    ],
)
def test_folders_cannot_go_inside_themselves(notes_root, tool, source, destination):
    with pytest.raises(ToolError, match="into itself"):
        tool(notes_root, source, destination)
    assert not (notes_root / "ideas" / "inner").exists()


@pytest.mark.parametrize("tool", [copy_folder, move_folder])
def test_folder_tools_refuse_to_overwrite(notes_root, tool):
    (notes_root / "things" / "ideas").mkdir()
    with pytest.raises(ToolError, match="already exists"):
        tool(notes_root, "ideas", "things")


def test_tools_answer_with_absolute_paths_when_given_absolute_paths(notes_root):
    destination = notes_root.resolve() / "things" / "copy.md"
    result = copy_file(notes_root, "groceries.md", str(destination))
    assert result == f"Copied groceries.md to {destination}"


# --- Create -----------------------------------------------------------------

def test_create_file_on_an_existing_folder_says_folder(notes_root):
    with pytest.raises(ToolError, match="folder already exists"):
        create_file(notes_root, "ideas")


def test_create_file_on_an_existing_file(notes_root):
    with pytest.raises(ToolError, match="File already exists"):
        create_file(notes_root, "groceries.md")


def test_write_reports_a_summary_not_the_content(notes_root):
    assert write_to_file(notes_root, "new.md", "Hello") == "Wrote 5 characters to new.md"
    assert append_to_file(notes_root, "new.md", "!!") == "Appended 2 characters to new.md"


# --- Listing ----------------------------------------------------------------

def test_list_files_accepts_an_absolute_path_outside_the_notes_folder(notes_root, tmp_path):
    other = tmp_path / "elsewhere"
    other.mkdir()
    (other / "a.txt").write_text("x", encoding="utf-8")

    assert list_files(notes_root, str(other)) == "a.txt"


def test_list_files_refuses_relative_paths(notes_root):
    with pytest.raises(ToolError, match="absolute"):
        list_files(notes_root, "ideas")


def test_list_files_refuses_hidden_folders(notes_root, tmp_path):
    with pytest.raises(ToolError, match="Hidden"):
        list_files(notes_root, str(tmp_path / ".secrets"))


def test_list_files_skips_hidden_folders_while_walking(notes_root):
    (notes_root / ".git").mkdir()
    (notes_root / ".git" / "config").write_text("x", encoding="utf-8")
    assert ".git" not in list_files(notes_root)


def test_list_files_stops_at_the_limit(notes_root, monkeypatch):
    monkeypatch.setattr(files_module, "MAX_LIST_ENTRIES", 1)
    assert list_files(notes_root).endswith("[Truncated: showing the first 1 entries.]")


def test_list_folders_says_folders_when_empty(tmp_path):
    assert list_folders(tmp_path) == "No folders found."


def test_registry_list_tools_take_an_optional_path(notes_root, tmp_path):
    registry = build_registry(notes_root)
    assert registry["list_folders"].function(path=str(notes_root)) == "ideas\nstuff\nthings"
    assert registry["list_folders"].function() == "ideas\nstuff\nthings"





    


    

