import re
import subprocess
from pathlib import Path

import emoji
import typer
from iterfzf import iterfzf
from rich import print
from ripgrepy import Ripgrepy

app = typer.Typer()


BLACKLIST = ["*⃣", "*️⃣"]


# Comprehensive emoji pattern covering various Unicode ranges
EMOJI_PATTERN = re.compile(
    "["
    "\U0001f600-\U0001f64f"  # Emoticons
    "\U0001f300-\U0001f5ff"  # Symbols & Pictographs
    "\U0001f680-\U0001f6ff"  # Transport & Map Symbols
    "\U0001f1e0-\U0001f1ff"  # Flags
    "\U00002700-\U000027bf"  # Dingbats
    "\U0001f900-\U0001f9ff"  # Supplemental Symbols & Pictographs
    "\U0001fa70-\U0001faff"  # Symbols & Pictographs Extended-A
    "\U00002600-\U000026ff"  # Miscellaneous Symbols
    "\U00002300-\U000023ff"  # Miscellaneous Technical
    "\U0001f700-\U0001f77f"  # Alchemical Symbols
    "\U0001f780-\U0001f7ff"  # Geometric Shapes Extended
    "\U0001f800-\U0001f8ff"  # Supplemental Arrows-C
    "\U0001f000-\U0001f02f"  # Mahjong Tiles
    "\U0001f0a0-\U0001f0ff"  # Playing Cards
    "\U0001f1e6-\U0001f1ff"  # Regional Indicator Symbols
    "\U0001f191-\U0001f251"  # Enclosed Characters
    "\U0001f004"  # Mahjong Tile Red Dragon
    "\U0001f0cf"  # Playing Card Black Joker
    "\u200d"  # Zero Width Joiner
    "\u2640-\u2642"  # Gender Symbols
    "\u2600-\u2b55"  # Miscellaneous Symbols and Arrows
    "\u23cf"  # Eject Symbol
    "\u23e9-\u23f3"  # Additional Miscellaneous Technical
    "\u25fd-\u25fe"  # White Medium Small Square
    "\u2614-\u2615"  # Umbrella and Hot Beverage
    "\u267f"  # Wheelchair Symbol
    "\u2693"  # Anchor
    "\u26a1"  # High Voltage
    "\u26aa-\u26ab"  # Medium White/Black Circle
    "\u26bd-\u26be"  # Soccer and Baseball
    "\u26c4-\u26c5"  # Snowman Without/With Snow
    "\u26ce"  # Ophiuchus
    "\u26d4"  # No Entry
    "\u26ea"  # Church
    "\u26f2-\u26f3"  # Fountain and Flag in Hole
    "\u26f5"  # Sailboat
    "\u26fa"  # Tent
    "\u26fd"  # Fuel Pump
    "\u2702"  # Scissors
    "\u2705"  # White Heavy Check Mark
    "\u2708-\u2709"  # Airplane and Envelope
    "\u270a-\u270b"  # Raised Fist and Raised Hand
    "\u2728"  # Sparkles
    "\u274c"  # Cross Mark
    "\u274e"  # Negative Squared Cross Mark
    "\u2753-\u2755"  # Question Marks
    "\u2757"  # Exclamation Mark
    "\u2795-\u2797"  # Plus, Minus, Division
    "\u27b0"  # Curly Loop
    "\u27bf"  # Double Curly Loop
    "\u2b1b-\u2b1c"  # Black and White Large Square
    "\u2b50"  # Star
    "\u2b55"  # Heavy Large Circle
    "\u2934-\u2935"  # Arrow Symbols
    "\u3030"  # Wavy Dash
    "\u303d"  # Part Alternation Mark
    "\u3297"  # Circled Ideograph Congratulation
    "\u3299"  # Circled Ideograph Secret
    "]+",
    flags=re.UNICODE,
)


def extract_emojis(text: str):
    return EMOJI_PATTERN.findall(text)


def remove_emojis(text: str, exclude: list[str] = []):
    # Remove only emojis not in the exclude list
    def emoji_replacer(match):
        char = match.group(0)
        return char if char in exclude else ""

    return EMOJI_PATTERN.sub(emoji_replacer, text)


def get_file_list():
    try:
        result = subprocess.run(
            ["fd", "--type", "f"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
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
):
    """
    Interactive mode: select a file using fzf to remove emojis.
    """
    files = get_file_list()
    if not files:
        typer.echo("No files found.")
        raise typer.Exit()

    selected_file = iterfzf(files)
    if selected_file:
        try:
            with open(selected_file, "r", encoding="utf-8") as f:
                content = f.read()
            emojis = extract_emojis(content)
            if exclude:
                emojis = list(filter(lambda x: x not in exclude, emojis))
            if emojis:
                print(f"[green]Found {len(emojis)} emojis in {selected_file}.[/green]")
                if typer.confirm("Do you want to remove them?", abort=True):
                    if exclude_task_lists:
                        lines = content.splitlines(keepends=True)
                        new_lines = []
                        for line in lines:
                            if re.match(r"^\s*[-+*]\s*\[[ xX]\]", line):
                                new_lines.append(line)
                            else:
                                new_lines.append(
                                    remove_emojis(line, exclude=exclude or [])
                                )
                        cleaned_content = "".join(new_lines)
                    else:
                        cleaned_content = remove_emojis(content, exclude=exclude or [])
                    with open(selected_file, "w", encoding="utf-8") as f:
                        f.write(cleaned_content)
                    typer.echo("Emojis removed.")
            else:
                print(f"[yellow]No emojis found in {selected_file}.[/yellow]")
        except Exception as e:
            typer.echo(f"Error reading file {selected_file}: {e}")
    else:
        typer.echo("No file selected.")


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
):
    """
    Remove emojis from the specified file.
    """
    try:
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()

        emojis = extract_emojis(content)
        if exclude:
            emojis = [e for e in emojis if e not in exclude]

        if emojis:
            print(f"[green]Found {len(emojis)} emojis in {filename}.[/green]")
            print(f"[yellow]{' '.join(emojis)}[/yellow]")

            if yes or typer.confirm("Do you want to remove them?", abort=True):
                if exclude_task_lists:
                    print(
                        "[yellow]exclude-task-lists is set: Excluding task lists from emoji removal[/yellow]"
                    )
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
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(cleaned_content)
                typer.echo("Emojis removed.")
        else:
            print("[red]No emojis found in the file.[/red]")

    except Exception as e:
        typer.echo(f"Error reading file {filename}: {e}")


@app.command("print")
def print_emojis():
    """
    Print all known emojis separated by '|'.
    """
    all_emojis = list(emoji.EMOJI_DATA.keys())

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
):
    """
    Scan the specified directory for files containing emojis using ripgrepy.
    """
    all_emojis = list(emoji.EMOJI_DATA.keys())
    all_emojis = list(filter(lambda x: x not in BLACKLIST, all_emojis))
    rg = Ripgrepy("|".join(all_emojis), path)
    rg.json()

    # we shoudl exit if it's a huge file

    # rg.max_depth(depth)

    try:
        results = rg.run().as_dict
        files_with_matches = set()

        for match in results:
            if "data" in match and "path" in match["data"]:
                file_path = match["data"]["path"]["text"]
                files_with_matches.add(file_path)

        if files_with_matches:
            print(
                f"[green]Found {len(results)} emojis in {len(files_with_matches)} files.[/green]"
            )
            display_tuples = []
            for emoji_file in files_with_matches:
                try:
                    with open(emoji_file, "r", encoding="utf-8") as f:
                        text = f.read()
                    count = len(extract_emojis(text))
                    emoji_file_display = emoji_file.replace("./", "")
                    file_abspath = Path(emoji_file_display).relative_to(".").absolute()
                    display_tuples.append((count, emoji_file_display, file_abspath))
                except Exception:
                    emoji_file_display = emoji_file.replace("./", "")
                    # add the abspath
                    file_abspath = Path(emoji_file_display).relative_to(".")
                    display_tuples.append((-1, emoji_file_display, file_abspath))

            # Sort display_tuples by count in descending order
            display_tuples.sort(key=lambda x: x[0], reverse=True)

            for count, emoji_file_display, file_abspath in display_tuples:
                if count == -1:
                    print(f"[cyan]{emoji_file_display}\t[error][/cyan]")
                else:
                    print(f"[green]{count}[/green]\t[cyan]{emoji_file_display}[/cyan]")
        else:
            typer.echo(
                "No emoji-ridden files found. Get some at https://www.chatgpt.com"
            )
    except Exception as e:
        typer.echo(f"Error during scan: {e}")


if __name__ == "__main__":
    app()
