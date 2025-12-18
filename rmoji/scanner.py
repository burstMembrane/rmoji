"""Scanning and display utilities for emoji detection."""

import re
from pathlib import Path

import emoji as emoji_lib
from rich import print

from .constants import BLACKLIST
from .emoji import extract_emojis, remove_emojis


def _display_scan_results(display_tuples: list[tuple[int, str, str]]) -> None:
    """Display scan results showing emoji counts per file."""
    for count, emoji_file_display, _ in display_tuples:
        if count == -1:
            print(f"[cyan]{emoji_file_display}\t[red][error][/red][/cyan]")
        else:
            print(f"[green]{count}[/green]\t[cyan]{emoji_file_display}[/cyan]")


def _nuke_file(
    file_path: str,
    exclude: list[str] | None,
    exclude_task_lists: bool,
) -> bool:
    """Remove emojis from a single file.

    Returns True on success, False on failure.
    """
    with Path(file_path).open(encoding="utf-8") as f:
        content = f.read()

    if not content:
        return True

    if exclude_task_lists:
        lines = content.splitlines(keepends=True)
        cleaned_content = "".join(
            line if re.match(r"^\s*[-+*]\s*\[[ xX]\]", line) else remove_emojis(line, exclude=exclude or [])
            for line in lines
        )
    else:
        cleaned_content = remove_emojis(content, exclude=exclude or [])

    with Path(file_path).open("w", encoding="utf-8") as f:
        f.write(cleaned_content)

    return True


def _scan_for_emojis(path: str, depth: int = 10) -> tuple[int, list[tuple[int, str, str]]]:
    """Scan a directory for files containing emojis using ripgrep.

    Parameters
    ----------
    path : str
        The directory path to scan.
    depth : int, optional
        Maximum recursion depth (currently unused, reserved for future use).

    Returns
    -------
    tuple[int, list[tuple[int, str, str]]]
        A tuple of (total_emoji_count, files_with_emoji_data) where
        files_with_emoji_data is a list of (count, display_path, file_path) tuples.
    """
    from ripgrepy import Ripgrepy

    all_emojis = list(emoji_lib.EMOJI_DATA.keys())  # type: ignore[attr-defined]
    all_emojis = list(filter(lambda x: x not in BLACKLIST, all_emojis))
    rg = Ripgrepy("|".join(all_emojis), path)
    rg.json()

    results = rg.run().as_dict
    files_with_matches = set()
    if not results:
        return 0, []

    for match in results:
        if "data" in match and "path" in match["data"]:
            file_path = match["data"]["path"]["text"]
            files_with_matches.add(file_path)

    if files_with_matches:
        display_tuples = []
        for emoji_file in files_with_matches:
            try:
                with Path(emoji_file).open(encoding="utf-8") as f:
                    text = f.read()
                count = len(extract_emojis(text))
                emoji_file_display = emoji_file.replace("./", "")
                Path(emoji_file_display).relative_to(".").absolute()
                display_tuples.append((count, emoji_file_display, emoji_file))
            except Exception:
                emoji_file_display = emoji_file.replace("./", "")
                display_tuples.append((-1, emoji_file_display, emoji_file))

        # Sort display_tuples by count in descending order
        display_tuples.sort(key=lambda x: x[0], reverse=True)

        total_emojis = sum(count for count, _, _ in display_tuples if count > 0)
        return total_emojis, display_tuples
    return 0, []
