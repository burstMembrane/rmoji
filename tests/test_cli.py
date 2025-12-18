from pathlib import Path

from typer.testing import CliRunner

from rmoji.cli import app

runner = CliRunner()


def test_scan_command() -> None:
    testdata_path = Path(__file__).parent / "testdata"
    result = runner.invoke(app, ["scan", str(testdata_path)])
    assert result.exit_code == 0
    assert "file1.txt" in result.output
    assert "file2.txt" in result.output


def test_scan_nonexistent_path() -> None:
    result = runner.invoke(app, ["scan", "/nonexistent/path"])
    assert result.exit_code == 1


def test_print_emojis_command() -> None:
    result = runner.invoke(app, ["print"])
    assert result.exit_code == 0


def test_nuke_command(tmp_path: Path) -> None:
    emoji_file = tmp_path / "emoji.txt"
    emoji_file.write_text("Hello 😊 world!", encoding="utf-8")

    result = runner.invoke(app, ["nuke", str(emoji_file), "--yes"])
    assert result.exit_code == 0

    content = emoji_file.read_text(encoding="utf-8")
    assert "😊" not in content


def test_nuke_command_with_exclude(tmp_path: Path) -> None:
    emoji_file = tmp_path / "emoji.txt"
    emoji_file.write_text("Hello 😊 and 🍕!", encoding="utf-8")

    result = runner.invoke(app, ["nuke", str(emoji_file), "--yes", "--exclude", "🍕"])
    assert result.exit_code == 0

    content = emoji_file.read_text(encoding="utf-8")
    assert "😊" not in content
    assert "🍕" in content


def test_remove_emojis_from_file_command(tmp_path: Path) -> None:
    emoji_file = tmp_path / "emoji.txt"
    emoji_file.write_text("Test 🎉 file", encoding="utf-8")

    result = runner.invoke(app, ["remove", str(emoji_file), "--yes"])
    assert result.exit_code == 0

    content = emoji_file.read_text(encoding="utf-8")
    assert "🎉" not in content


def test_remove_command_with_exclude_task_lists() -> None:
    testdata = Path(__file__).parent / "testdata"
    task_file = testdata / "file4.txt"
    original = task_file.read_text(encoding="utf-8")
    try:
        result = runner.invoke(app, ["remove", str(task_file), "--yes", "--exclude-task-lists"])
        assert result.exit_code == 0
        content = task_file.read_text(encoding="utf-8")
        # All emojis preserved because all lines are task lists
        assert "🔼" in content
        assert "📅" in content
    finally:
        task_file.write_text(original, encoding="utf-8")


def test_remove_command_no_emojis(tmp_path: Path) -> None:
    plain_file = tmp_path / "plain.txt"
    plain_file.write_text("No emojis here", encoding="utf-8")
    result = runner.invoke(app, ["remove", str(plain_file), "--yes"])
    assert result.exit_code == 0
    assert "No emojis found" in result.output


def test_remove_command_file_error() -> None:
    result = runner.invoke(app, ["remove", "/nonexistent/file.txt", "--yes"])
    assert "Error reading file" in result.output


def test_scan_no_emoji_files(tmp_path: Path) -> None:
    plain_file = tmp_path / "plain.txt"
    plain_file.write_text("No emojis", encoding="utf-8")
    result = runner.invoke(app, ["scan", str(tmp_path)])
    assert result.exit_code == 0
    assert "No emoji-ridden files found" in result.output


def test_nuke_no_emoji_files(tmp_path: Path) -> None:
    plain_file = tmp_path / "plain.txt"
    plain_file.write_text("No emojis", encoding="utf-8")
    result = runner.invoke(app, ["nuke", str(tmp_path), "--yes"])
    assert result.exit_code == 0
    assert "No emoji-ridden files found" in result.output


def test_nuke_with_exclude_task_lists() -> None:
    testdata = Path(__file__).parent / "testdata"
    task_file = testdata / "file4.txt"
    file1 = testdata / "file1.txt"
    file2 = testdata / "file2.txt"
    # Backup all files
    original = task_file.read_text(encoding="utf-8")
    orig1 = file1.read_text(encoding="utf-8")
    orig2 = file2.read_text(encoding="utf-8")
    try:
        result = runner.invoke(app, ["nuke", str(testdata), "--yes", "--exclude-task-lists"])
        assert result.exit_code == 0
        assert "exclude-task-lists is set" in result.output
        # Task list emojis preserved
        content = task_file.read_text(encoding="utf-8")
        assert "🔼" in content
        assert "📅" in content
    finally:
        task_file.write_text(original, encoding="utf-8")
        file1.write_text(orig1, encoding="utf-8")
        file2.write_text(orig2, encoding="utf-8")


def test_nuke_user_cancels(tmp_path: Path) -> None:
    emoji_file = tmp_path / "emoji.txt"
    emoji_file.write_text("Hello 😊", encoding="utf-8")
    result = runner.invoke(app, ["nuke", str(tmp_path)], input="n\n")
    assert "cancelled" in result.output.lower()
    # File should be unchanged
    assert "😊" in emoji_file.read_text(encoding="utf-8")
