# rmoji

A command-line tool for scanning, listing, and removing emojis from files in your project.  
Built with Python, Typer, Rich, and Ripgrepy.

## Features

- **Scan directories** for files containing emojis with detailed counts
- **Interactively select** files using fuzzy finder (fzf)
- **Remove emojis** from specific files with confirmation prompts
- **Print all known emojis** (excluding blacklisted ones)
- **Comprehensive emoji detection** covering all Unicode ranges

## Installation

Install with [uv](https://github.com/astral-sh/uv):

```bash
uv tool install rmoji
```

Or with [uvx](https://github.com/astral-sh/uv) for an ephemeral environment:

```bash
uvx rmoji
```

### Development

```bash
uv sync
```

### Requirements

- Python 3.8+
- [`fd`](https://github.com/sharkdp/fd) (for file discovery)
- [`fzf`](https://github.com/junegunn/fzf) (for interactive selection)
- [`ripgrep`](https://github.com/BurntSushi/ripgrep) (for fast emoji scanning)

## Usage

### Commands

#### `scan`

Scan directories for emoji-containing files with counts:

```bash
rmoji scan [PATH] [-D DEPTH]
```

- `PATH`: Directory to scan (default: current directory)
- `-D, --depth`: Max directory recursion depth (default: 10)

**Example output:**

```
Found 15 emojis in 3 files.
5    src/main.py
3    docs/README.md  
2    tests/test_utils.py
```

#### `interactive`

Interactively select and clean files using fzf:

```bash
rmoji interactive
```

#### `remove`

Remove emojis from a specific file:

```bash
rmoji remove <filename>
```

Shows found emojis before removal and asks for confirmation.

#### `print`

Output all known emojis separated by `|`:

```bash
rmoji print
```

Useful for piping to other tools or custom processing.

## Examples

Scan current directory:

```bash
rmoji scan .
```

Scan with limited depth:

```bash
rmoji scan --depth 5 /path/to/project
```

Clean specific file:

```bash
rmoji remove notes.txt
```

Interactive cleaning:

```bash
rmoji interactive
```

## Technical Details

- Preserves UTF-8 file encoding
- Detects comprehensive emoji ranges including emoticons, symbols, flags, and regional indicators
- Uses ripgrep for fast directory scanning
- Confirmation prompts prevent accidental changes
- Blacklist excludes problematic emoji variants

## License

MIT
