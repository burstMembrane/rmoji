import pytest

from rmoji.emoji import extract_emojis, remove_emojis


@pytest.fixture
def sample_text() -> str:
    return "Hello 😊! Let's grab some 🍕 and 🎉 tonight!"


@pytest.fixture
def clean_text() -> str:
    return "Hello! There is no emoji here."


def test_extract_emojis(sample_text: str) -> None:
    emojis = extract_emojis(sample_text)
    assert set(emojis) == {"😊", "🍕", "🎉"}


def test_remove_emojis(sample_text: str) -> None:
    cleaned_text = remove_emojis(sample_text)
    assert cleaned_text == "Hello ! Let's grab some  and  tonight!"


def test_remove_emojis_with_exclude(sample_text: str) -> None:
    cleaned_text = remove_emojis(sample_text, exclude=["🍕"])
    assert cleaned_text == "Hello ! Let's grab some 🍕 and  tonight!"


def test_extract_emojis_no_emojis(clean_text: str) -> None:
    emojis = extract_emojis(clean_text)
    assert emojis == []
