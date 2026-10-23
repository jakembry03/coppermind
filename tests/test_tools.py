import pytest
from coppermind.tools import ToolError, list_files, read_file

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