# app/utils.py
import json, re
from typing import Any, List

def extract_json(s: str) -> Any:
    s = s.strip()
    s = re.sub(r"^```(?:json)?\s*|\s*```$", "", s, flags=re.I).strip()
    m = re.search(r"\{.*\}", s, re.S)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass
    return json.loads(s)

def force_list(x) -> List[str]:
    if x is None:
        return []
    if isinstance(x, list):
        return [str(i).strip() for i in x if str(i).strip()]
    if isinstance(x, str):
        parts = re.split(r"[;\n,]+", x)   # <-- fixed
        parts = [p.strip() for p in parts if p.strip()]
        return parts if parts else [x.strip()]
    return [str(x).strip()]

def with_goodnight(story: str) -> str:
    story = story.strip()
    if not story.endswith(("Good night.", "Goodnight.", "Sleep well.", "Sweet dreams.")):
        story += "\n\nSweet dreams."
    return story

def coerce_int(value, default=500):
    """
    Turn model outputs like 500, "500", "450-600", "about 480" into an int.
    Falls back to default if nothing sensible is found.
    """
    try:
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(round(value))
        if isinstance(value, str):
            m = re.search(r"\d{2,4}", value)
            if m:
                return int(m.group(0))
    except:
        pass
    return default
