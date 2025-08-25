# Pairs of opening -> closing quotation marks we should strip
_QUOTE_PAIRS = {
    '"': '"',
    "'": "'",
    "`": "`",
    "“": "”",
    "‘": "’",
    "«": "»",
    "‹": "›",
}


def normalize_wrapping_quotes(s: str) -> str:
    """Remove one or more layers of surrounding quotes/ticks."""
    s = s.strip()
    while len(s) >= 2:
        first, last = s[0], s[-1]
        closer = _QUOTE_PAIRS.get(first)
        if closer and last == closer:
            s = s[1:-1].strip()
            continue
        break
    return s
