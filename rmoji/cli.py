"""CLI commands for rmoji."""

import re
from pathlib import Path

import emoji
import typer
from iterfzf import iterfzf
from rich import print

from .constants import BLACKLIST
from .emoji import extract_emojis, remove_emojis
from .files import get_file_list
from .scanner import _display_scan_results, _nuke_file, _scan_for_emojis

app = typer.Typer()


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
    all_emojis = list(emoji.EMOJI_DATA.keys())  # type: ignore[attr-defined]

    # remove the blacklist emojis
    all_emojis = list(filter(lambda x: x not in BLACKLIST, all_emojis))
    print("|".join(all_emojis))


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
