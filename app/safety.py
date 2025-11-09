import re
DISALLOWED = [
    r"\bgun\b", r"\bweapon\b", r"\bkill\b", r"\bblood\b", r"\bbomb\b",
    r"\bwar\b", r"\bsuicide\b", r"\bself[- ]?harm\b", r"\bdrug\b",
    r"\balcohol\b", r"\bnightmare(s)?\b", r"\bghost(s)?\b"
]

def unsafe(text: str) -> bool:
    low = text.lower()
    return any(re.search(p, low) for p in DISALLOWED)
