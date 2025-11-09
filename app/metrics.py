# app/metrics.py
import re
from typing import Dict, List

DQUOTE = re.compile(r"\"[^\"]+\"|'[^']+'")
SPLIT_SENT = re.compile(r'([.!?])')

def split_sentences(text: str) -> List[str]:
    chunks = SPLIT_SENT.split(text)
    sents = ["".join(chunks[i:i+2]).strip() for i in range(0, len(chunks), 2)]
    return [s for s in sents if s]

def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w']+\b", text))

def letter_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z]", text))

def dialogue_lines(text: str) -> int:
    # crude heuristic: each quoted span counts as one line of dialogue
    return len(DQUOTE.findall(text))

def avg_sentence_len(text: str) -> float:
    sents = split_sentences(text)
    if not sents:
        return 0.0
    return sum(word_count(s) for s in sents) / len(sents)

def coleman_liau_index(text: str) -> float:
    # CLI = 0.0588 * L - 0.296 * S - 15.8
    # L = letters per 100 words; S = sentences per 100 words
    wc = max(word_count(text), 1)
    sc = max(len(split_sentences(text)), 1)
    L = letter_count(text) * 100.0 / wc
    S = sc * 100.0 / wc
    return 0.0588 * L - 0.296 * S - 15.8

def has_bedtime_tail(text: str) -> bool:
    return text.strip().endswith(("Good night.", "Goodnight.", "Sleep well.", "Sweet dreams."))

def missing_tokens(text: str, tokens: List[str]) -> List[str]:
    low = text.lower()
    miss = []
    for t in tokens or []:
        t = str(t).strip().lower()
        if t and t not in low:
            miss.append(t)
    return miss

def compute_metrics(
    story: str,
    must_include: List[str],
    intended_use: str,
    word_limit: int
) -> Dict:
    # coerce word_limit defensively
    try:
        if not isinstance(word_limit, int):
            # light inline coerce to avoid cross-import
            import re
            if isinstance(word_limit, (float,)):
                word_limit = int(round(word_limit))
            elif isinstance(word_limit, str):
                m = re.search(r"\d{2,4}", word_limit)
                word_limit = int(m.group(0)) if m else 500
            else:
                word_limit = 500
    except:
        word_limit = 500
    wc = word_count(story)
    avg_len = avg_sentence_len(story)
    cli = coleman_liau_index(story)
    dlg = dialogue_lines(story)
    miss = missing_tokens(story, must_include or [])
    tail_ok = (intended_use != "bedtime") or has_bedtime_tail(story)
    return {
        "word_count": wc,
        "over_word_limit": wc > word_limit,
        "avg_sentence_len": round(avg_len, 2),
        "coleman_liau_index": round(cli, 2),
        "dialogue_lines": dlg,
        "dialogue_over_2": dlg > 2,
        "missing_must_include": miss,
        "bedtime_tail_ok": tail_ok,
        "intended_use": intended_use,
        "word_limit": word_limit,
    }
