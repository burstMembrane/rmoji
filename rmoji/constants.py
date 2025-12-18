import re

BLACKLIST = ["*⃣", "*️⃣"]
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
