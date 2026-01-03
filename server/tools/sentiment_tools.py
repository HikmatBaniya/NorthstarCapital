from __future__ import annotations

from typing import Any, Dict


_POSITIVE = {
    "beat",
    "beats",
    "growth",
    "up",
    "surge",
    "record",
    "strong",
    "profit",
    "bull",
    "bullish",
    "outperform",
}
_NEGATIVE = {
    "miss",
    "misses",
    "down",
    "drop",
    "weak",
    "loss",
    "bear",
    "bearish",
    "underperform",
    "warning",
}


def sentiment_analyze(text: str) -> Dict[str, Any]:
    tokens = [t.strip(".,!?;:()[]").lower() for t in text.split()]
    pos = sum(1 for t in tokens if t in _POSITIVE)
    neg = sum(1 for t in tokens if t in _NEGATIVE)
    score = pos - neg
    label = "neutral"
    if score > 0:
        label = "positive"
    elif score < 0:
        label = "negative"
    return {"score": score, "positive_hits": pos, "negative_hits": neg, "label": label}
