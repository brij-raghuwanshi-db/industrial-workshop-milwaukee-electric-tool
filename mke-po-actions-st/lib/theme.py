"""Formatting + semantic color helpers, ported from the React app's money()/num() + palette."""
from __future__ import annotations

# palette (matches the dashboard theme)
BLUE = "#2272B4"
VIOLET = "#995495"
CORAL = "#FF7054"
EMERALD = "#22a06b"
RED = "#c0392b"
AMBER = "#FFB020"

TONE_COLOR = {"good": EMERALD, "warn": AMBER, "bad": RED, "neutral": "#64748b"}


def money(n) -> str:
    if n is None:
        return "—"
    n = float(n)
    if abs(n) >= 1e6:
        return f"${n/1e6:.1f}M"
    if abs(n) >= 1e3:
        return f"${n/1e3:.0f}K"
    return f"${round(n)}"


def num(n) -> str:
    if n is None:
        return "—"
    return f"{round(float(n)):,}"
