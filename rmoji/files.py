"""File utilities for directory traversal and gitignore handling."""

import os
from pathlib import Path
from typing import Any

import pathspec


def _load_gitignore_spec(root: Path) -> pathspec.PathSpec | None:
    """Load .gitignore patterns from the given root directory.

    Parameters
    ----------
    root : Path
        The root directory to search for .gitignore.

    Returns
    -------
    pathspec.PathSpec | None
        A PathSpec object if .gitignore exists, None otherwise.
    """
    gitignore_path = root / ".gitignore"
    if not gitignore_path.exists():
        return None

    with gitignore_path.open(encoding="utf-8") as f:
        return pathspec.PathSpec.from_lines("gitwildmatch", f)


def get_file_list(root: str = ".") -> list[str] | list[Any]:
    """Get a list of all files in the directory, respecting .gitignore patterns.

    Parameters
    ----------
    root : str
        The root directory to scan, defaults to current directory.

    Returns
    -------
    list[str]
        List of file paths relative to root, excluding gitignored files.
    """
    root_path = Path(root).resolve()
    spec = _load_gitignore_spec(root_path)

    files: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root_path):
        rel_dir = Path(dirpath).relative_to(root_path)

        # Filter out .git directory
        if ".git" in dirnames:
            dirnames.remove(".git")

        for filename in filenames:
            rel_path = rel_dir / filename if str(rel_dir) != "." else Path(filename)
            rel_path_str = str(rel_path)

            # Skip if matches gitignore patterns
            if spec and spec.match_file(rel_path_str):
                continue

            files.append(rel_path_str)

    return files
