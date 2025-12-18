import re
import subprocess
from pathlib import Path
from typing import Any

import emoji
import typer
from iterfzf import iterfzf
from rich import print
from ripgrepy import Ripgrepy

from .constants import BLACKLIST, EMOJI_PATTERN

app = typer.Typer()


def extract_emojis(text: str) -> list[str]:
    """Extract emojis from a string.

    Parameters
    ----------
    text : str
        The input string to search for emojis.

    Returns
    -------
    list[str]
        List of emoji characters found in the text.
    """
    result = EMOJI_PATTERN.findall(text)
    if not result:
        return []
    return list(map(str, set(result)))


def remove_emojis(text: str, exclude: list[str] | None = None) -> str:
    """Remove emojis from a string.

    Parameters
    ----------
    text : str
        string to remove emojis from
    exclude : list[str], optional
        the list of emojis to exclude, by default all emojis are removed

    Returns
    -------
    str
        string with emojis removed
    """
    if exclude is None:
        exclude = []

    def emoji_replacer(match: re.Match[str]) -> str:
        char = match.group(0)
        return char if char in exclude else ""

    result: str = EMOJI_PATTERN.sub(emoji_replacer, text)
    return result


def get_file_list() -> list[str] | list[Any]:
    """Get a list of all files in the current directory using fd.

    Returns
    -------
    list[str]
        List of file paths, or empty list if fd fails.
    """
    # get the list of files using fd
    try:
        result = subprocess.run(
            ["fd", "--type", "f"],
            capture_output=True,
            text=True,
            check=True,
            shell=False,
        )
        return result.stdout.strip().split("\n")
    except subprocess.CalledProcessError as e:
        typer.echo(f"Error running fd: {e.stderr}")
        return []


@app.command()
def interactive(
    exclude: list[str] = typer.Option(
        None,
        "--exclude",
        help="Emoji(s) to exclude from removal. Can be used multiple times.",
    ),
    exclude_task_lists: bool = typer.Option(
        False,
        "--exclude-task-lists",
        help="Do not remove emojis from markdown task list lines.",
    ),
) -> None:
    """Interactive mode: select a file using fzf to remove emojis.

    Launches fzf to allow file selection, then scans the selected file
    for emojis and prompts for confirmation before removal.

    Parameters
    ----------
    exclude : list[str], optional
        Emoji(s) to preserve during removal.
    exclude_task_lists : bool, optional
        If True, preserves emojis on markdown task list lines.
    """
    files = get_file_list()
    if not files:
        typer.echo("No files found.")
        raise typer.Exit()

    selected_file = iterfzf(files)
    if not selected_file:
        typer.echo("No file selected.")
        raise typer.Exit()

    with Path(selected_file).open(encoding="utf-8") as f:
        content = f.read()

    emojis = extract_emojis(content)

    if exclude:
        emojis = list(filter(lambda x: x not in exclude, emojis))

    if not emojis:
        print(f"[yellow]No emojis found in {selected_file}.[/yellow]")
        raise typer.Exit()
    print(f"[green]Found {len(emojis)} emojis in {selected_file}.[/green]")
    if typer.confirm("Do you want to remove them?", abort=True):
        if exclude_task_lists:
            lines = content.splitlines(keepends=True)
            new_lines = []
            for line in lines:
                if re.match(r"^\s*[-+*]\s*\[[ xX]\]", line):
                    new_lines.append(line)
                else:
                    new_lines.append(remove_emojis(line, exclude=exclude or []))
            cleaned_content = "".join(new_lines)
        else:
            cleaned_content = remove_emojis(content, exclude=exclude or [])
        with Path(selected_file).open("w", encoding="utf-8") as f:
            f.write(cleaned_content)
        typer.echo("Emojis removed.")


@app.command("remove")
def remove_emojis_from_file(
    filename: str,
    exclude: list[str] = typer.Option(
        None,
        "--exclude",
        help="Emoji(s) to exclude from removal. Can be used multiple times.",
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Automatically confirm emoji removal without prompting.",
    ),
    exclude_task_lists: bool = typer.Option(
        False,
        "--exclude-task-lists",
        help="Do not remove emojis from markdown task list lines.",
    ),
) -> None:
    """Remove emojis from the specified file.

    Reads the file, identifies emojis, displays them to the user, and removes
    them after confirmation (or automatically with --yes flag).

    Parameters
    ----------
    filename : str
        Path to the file to process.
    exclude : list[str], optional
        Emoji(s) to preserve during removal.
    yes : bool, optional
        If True, skip confirmation prompt.
    exclude_task_lists : bool, optional
        If True, preserves emojis on markdown task list lines.
    """
    try:
        with Path(filename).open(encoding="utf-8") as f:
            content = f.read()

        emojis = extract_emojis(content)
        if exclude:
            emojis = [e for e in emojis if e not in exclude]

        if emojis:
            print(f"[green]Found {len(emojis)} emojis in {filename}.[/green]")
            print(f"[yellow]{' '.join(emojis)}[/yellow]")

            if yes or typer.confirm("Do you want to remove them?", abort=True):
                if exclude_task_lists:
                    print("[yellow]exclude-task-lists is set: Excluding task lists from emoji removal[/yellow]")
                    lines = content.splitlines(keepends=True)
                    new_lines = []
                    for line in lines:
                        if re.match(r"^\s*[-+*]\s*\[[ xX]\]", line):
                            new_lines.append(line)
                        else:
                            new_lines.append(remove_emojis(line, exclude=exclude or []))
                    cleaned_content = "".join(new_lines)
                else:
                    cleaned_content = remove_emojis(content, exclude=exclude or [])
                with Path(filename).open("w", encoding="utf-8") as f:
                    f.write(cleaned_content)
                typer.echo("Emojis removed.")
        else:
            print("[red]No emojis found in the file.[/red]")

    except Exception as e:
        typer.echo(f"Error reading file {filename}: {e}")


@app.command("print")
def print_emojis() -> None:
    """Print all known emojis separated by '|'.

    Outputs all emojis from the emoji database (excluding blacklisted ones)
    as a pipe-separated string, useful for piping to ripgrep or other tools.
    """
    all_emojis = list(emoji.EMOJI_DATA.keys())

    # remove the blacklist emojis
    all_emojis = list(filter(lambda x: x not in BLACKLIST, all_emojis))
    print("|".join(all_emojis))


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
    all_emojis = list(emoji.EMOJI_DATA.keys())
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


@app.command("scan")
def scan(
    depth: int = typer.Option(
        10,
        "-D",
        help="Max depth to recurse through directories",
    ),
    path: str = typer.Argument(".", help="Path to scan for emojis"),
) -> None:
    """Scan the specified directory for files containing emojis.

    Uses ripgrep to find files containing emojis and displays a summary
    with emoji counts per file, sorted by count in descending order.

    Parameters
    ----------
    depth : int, optional
        Maximum recursion depth for directory traversal.
    path : str, optional
        Directory path to scan, defaults to current directory.
    """
    total_emojis, display_tuples = _scan_for_emojis(path, depth)

    if not display_tuples:
        typer.echo("No emoji-ridden files found. Get some at https://www.chatgpt.com")
        return

    print(f"[green]Found {total_emojis} emojis in {len(display_tuples)} files.[/green]")
    _display_scan_results(display_tuples)


@app.command("nuke")
def nuke(
    depth: int = typer.Option(
        10,
        "-D",
        help="Max depth to recurse through directories",
    ),
    path: str = typer.Argument(".", help="Path to scan and nuke emojis from"),
    exclude: list[str] = typer.Option(
        None,
        "--exclude",
        help="Emoji(s) to exclude from removal. Can be used multiple times.",
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Automatically confirm emoji removal without prompting.",
    ),
    exclude_task_lists: bool = typer.Option(
        False,
        "--exclude-task-lists",
        help="Do not remove emojis from markdown task list lines.",
    ),
) -> None:
    """Scan directory and remove all emojis from all files.

    Scans the directory for files containing emojis, displays a summary,
    and upon confirmation removes all emojis from every matched file.

    Parameters
    ----------
    depth : int, optional
        Maximum recursion depth for directory traversal.
    path : str, optional
        Directory path to scan, defaults to current directory.
    exclude : list[str], optional
        Emoji(s) to preserve during removal.
    yes : bool, optional
        If True, skip confirmation prompt.
    exclude_task_lists : bool, optional
        If True, preserves emojis on markdown task list lines.
    """
    print(f"[yellow]Scanning {path} for emoji files...[/yellow]")

    total_emojis, display_tuples = _scan_for_emojis(path, depth)

    if not display_tuples:
        typer.echo("No emoji-ridden files found. Nothing to nuke!")
        return

    # Show scan results and options
    print(f"[green]Found {total_emojis} emojis in {len(display_tuples)} files.[/green]")
    _display_scan_results(display_tuples)
    print(f"\n[yellow]This will remove emojis from {len(display_tuples)} files.[/yellow]")

    if exclude_task_lists:
        print("[yellow]exclude-task-lists is set: Task lists will be preserved[/yellow]")
    if exclude:
        print(f"[yellow]Excluding emojis: {' '.join(exclude)}[/yellow]")

    # Get confirmation
    if not yes and not typer.confirm("\n[red] NUKE ALL EMOJIS? This cannot be undone![/red]"):
        print("[yellow]Nuke cancelled.[/yellow]")
        return

    # Process all files
    success_count = 0
    error_count = sum(1 for count, _, _ in display_tuples if count == -1)

    for count, emoji_file_display, file_path in display_tuples:
        if count == -1:
            continue

        try:
            _nuke_file(file_path, exclude, exclude_task_lists)
            success_count += 1
            print(f"[green][/green] [cyan]{emoji_file_display}[/cyan]")
        except Exception as e:
            error_count += 1
            print(f"[red][/red] [cyan]{emoji_file_display}[/cyan] - {e}")

    # Summary
    print("\n[green] Nuke complete![/green]")
    print(f"[green]Files processed: {success_count}[/green]")
    if error_count > 0:
        print(f"[red]Files with errors: {error_count}[/red]")


if __name__ == "__main__":
    app()
