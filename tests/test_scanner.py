from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from rmoji.scanner import _display_scan_results, _nuke_file, _scan_for_emojis


@pytest.fixture
def emoji_file(tmp_path: Path) -> Path:
    file_path = tmp_path / "emoji_file.txt"
    file_path.write_text("Hello 😊! This file has some emojis 🍕🎉.", encoding="utf-8")
    return file_path


@pytest.fixture
def emoji_dir() -> Path:
    return Path(__file__).parent / "testdata"


def test_scan_for_emojis(emoji_dir: Path) -> None:
    total_count, results = _scan_for_emojis(str(emoji_dir))

    assert total_count == 4  # file1 (1) + file2 (1) + file4 (2 unique emojis)
    result_dict = {file_display: count for count, file_display, _ in results}
    assert result_dict.get("file1.txt") == 1
    assert result_dict.get("file2.txt") == 1
    assert result_dict.get("file4.txt") == 2


def test_nuke_file(emoji_file: Path) -> None:
    success = _nuke_file(str(emoji_file), exclude=None, exclude_task_lists=False)
    assert success

    content = emoji_file.read_text(encoding="utf-8")
    assert "😊" not in content
    assert "🍕" not in content
    assert "🎉" not in content


def test_display_scan_results_success(capsys: pytest.CaptureFixture[str]) -> None:
    display_tuples = [
        (5, "file1.txt", "/path/to/file1.txt"),
        (3, "file2.txt", "/path/to/file2.txt"),
    ]
    _display_scan_results(display_tuples)
    captured = capsys.readouterr()
    assert "5" in captured.out
    assert "file1.txt" in captured.out
    assert "3" in captured.out
    assert "file2.txt" in captured.out


def test_display_scan_results_error(capsys: pytest.CaptureFixture[str]) -> None:
    display_tuples = [(-1, "error_file.txt", "/path/to/error_file.txt")]
    _display_scan_results(display_tuples)
    captured = capsys.readouterr()
    assert "error_file.txt" in captured.out
    assert "error" in captured.out


def test_nuke_file_empty_content(tmp_path: Path) -> None:
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("", encoding="utf-8")
    success = _nuke_file(str(empty_file), exclude=None, exclude_task_lists=False)
    assert success
    assert empty_file.read_text(encoding="utf-8") == ""


def test_nuke_file_with_exclude_task_lists(tmp_path: Path) -> None:
    task_file = tmp_path / "tasks.md"
    content = "# Tasks\n- [ ] Complete task 😊\n- [x] Done task 🎉\nRegular line with emoji 🍕"
    task_file.write_text(content, encoding="utf-8")
    success = _nuke_file(str(task_file), exclude=None, exclude_task_lists=True)
    assert success

    result = task_file.read_text(encoding="utf-8")
    # Task list emojis should be preserved
    assert "😊" in result
    assert "🎉" in result
    # Regular line emojis should be removed
    assert "🍕" not in result


def test_nuke_file_with_exclude(tmp_path: Path) -> None:
    file_path = tmp_path / "emoji_file.txt"
    file_path.write_text("Hello 😊 and 🍕 pizza!", encoding="utf-8")
    success = _nuke_file(str(file_path), exclude=["🍕"], exclude_task_lists=False)
    assert success

    content = file_path.read_text(encoding="utf-8")
    assert "😊" not in content
    assert "🍕" in content  # Should be preserved due to exclude


def test_scan_for_emojis_no_matches(tmp_path: Path) -> None:
    no_emoji_file = tmp_path / "no_emoji.txt"
    no_emoji_file.write_text("This file has no emojis at all.", encoding="utf-8")

    total_count, results = _scan_for_emojis(str(tmp_path))
    assert total_count == 0
    assert results == []


def test_scan_for_emojis_no_valid_paths(tmp_path: Path) -> None:
    """Test when ripgrep returns results but without valid path data.

    This is a defensive check for malformed ripgrep output - requires mocking.
    """
    mock_rg_instance = MagicMock()
    mock_rg_instance.json.return_value = mock_rg_instance
    mock_rg_instance.run.return_value.as_dict = [
        {"type": "match", "data": {"lines": {"text": "some text"}}},  # No path key
        {"type": "summary"},  # No data key
    ]

    with patch("ripgrepy.Ripgrepy", return_value=mock_rg_instance):
        total_count, results = _scan_for_emojis(str(tmp_path))
        assert total_count == 0
        assert results == []


def test_scan_for_emojis_file_read_error(tmp_path: Path) -> None:
    """Test when a file cannot be read after ripgrep finds it.

    This tests a race condition where ripgrep finds a file but it becomes
    unreadable before we process it. We simulate this by creating a file,
    letting ripgrep cache find it, then replacing it with a broken symlink.
    """
    # Create a real file with emoji that ripgrep will find
    emoji_file = tmp_path / "emoji.txt"
    emoji_file.write_text("Hello 😊", encoding="utf-8")

    # Mock ripgrep to return this file path, then break the file
    mock_rg_instance = MagicMock()
    mock_rg_instance.json.return_value = mock_rg_instance
    mock_rg_instance.run.return_value.as_dict = [
        {"data": {"path": {"text": str(emoji_file)}}},
    ]

    # Delete the file so reading fails
    emoji_file.unlink()

    with patch("ripgrepy.Ripgrepy", return_value=mock_rg_instance):
        total_count, results = _scan_for_emojis(str(tmp_path))
        assert total_count == -1
        assert results == []


def test_scan_for_emojis_relative_path_fallback(tmp_path: Path) -> None:
    """Test fallback when file path can't be made relative to scan root.

    This requires mocking because ripgrep only returns files within the search path.
    """
    emoji_file = tmp_path / "emoji.txt"
    emoji_file.write_text("Hello 😊", encoding="utf-8")

    mock_rg_instance = MagicMock()
    mock_rg_instance.json.return_value = mock_rg_instance
    mock_rg_instance.run.return_value.as_dict = [
        {"data": {"path": {"text": str(emoji_file)}}},
    ]

    other_dir = tmp_path / "other"
    other_dir.mkdir()

    with patch("ripgrepy.Ripgrepy", return_value=mock_rg_instance):
        total_count, results = _scan_for_emojis(str(other_dir))
        assert total_count == 1
        assert len(results) == 1
        assert results[0][1] == str(emoji_file)
