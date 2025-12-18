from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from rmoji.files import _load_gitignore_spec, get_file_list


@pytest.fixture
def gitignore_spec(tmp_path: Path) -> tuple[Path, Path]:
    gitignore_content = """
# Ignore all .log files
*.log
# Ignore temp/ directory
temp/
"""
    gitignore_path = tmp_path / ".gitignore"
    gitignore_path.write_text(gitignore_content, encoding="utf-8")

    return gitignore_path, gitignore_path.parent


@pytest.fixture
def test_dir(tmp_path: Path) -> Path:
    # Create a test directory structure
    (tmp_path / "file1.txt").write_text("This is a text file.", encoding="utf-8")
    (tmp_path / "file2.log").write_text("This is a log file.", encoding="utf-8")
    (tmp_path / "temp").mkdir()
    (tmp_path / "temp" / "file3.txt").write_text("This is a temp file.", encoding="utf-8")
    (tmp_path / "important.txt").write_text("This is important.", encoding="utf-8")
    # .git directory should be ignored
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("git config content", encoding="utf-8")
    return tmp_path


def test_load_gitignore_spec_no_file(gitignore_spec: tuple[Path, Path]) -> None:
    gitignore_path, tmp_path = gitignore_spec
    spec = _load_gitignore_spec(tmp_path)
    # assert that it returns PathSpec object when .gitignore exists

    assert spec is not None
    assert spec.match_file("example.log")
    assert spec.match_file("temp/file.txt")
    assert not spec.match_file("important.txt")

    # unlink the .gitignore file to test absence
    gitignore_path.unlink()
    spec_none = _load_gitignore_spec(tmp_path)
    assert spec_none is None


def test_get_file_list_respects_gitignore(test_dir: Path, gitignore_spec: tuple[Path, Path]) -> None:
    gitignore_path, tmp_path = gitignore_spec
    # Ensure .gitignore is in the test directory
    gitignore_path.rename(tmp_path / ".gitignore")

    file_list = get_file_list(str(test_dir))

    # assert thhat .git is ignored and .log files and temp/ directory are excluded
    assert ".git/config" not in file_list

    expected_files = {"file1.txt", "important.txt", ".gitignore"}

    assert len(file_list) == len(expected_files)
    assert set(file_list) == expected_files
