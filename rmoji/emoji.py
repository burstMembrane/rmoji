"""Core emoji extraction and removal functions."""

import re

from .constants import EMOJI_PATTERN


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
