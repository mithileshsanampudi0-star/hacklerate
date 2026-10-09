"""Attendance percentage and risk.

safe      >= 85%
warning   75% to < 85%
critical  < 75%  (below the usual exam-eligibility cut-off)
"""

import math

MIN_REQUIRED = 75
SAFE_FROM = 85


def percentage(attended: int, total: int) -> float | None:
    if total <= 0:
        return None
    return round(100 * attended / total, 2)


def risk_level(pct: float | None) -> str:
    if pct is None or pct >= SAFE_FROM:
        return "safe"
    if pct >= MIN_REQUIRED:
        return "warning"
    return "critical"


def classes_needed(attended: int, total: int, target: int = MIN_REQUIRED) -> int:
    """Consecutive classes the student must attend to get back to `target`%."""
    deficit = target * total - 100 * attended
    if total <= 0 or deficit <= 0:
        return 0
    return math.ceil(deficit / (100 - target))


def classes_can_skip(attended: int, total: int, target: int = MIN_REQUIRED) -> int:
    """Classes the student can still miss and stay at or above `target`%."""
    surplus = 100 * attended - target * total
    if surplus <= 0:
        return 0
    return surplus // target


def summarize(attended: int, total: int) -> dict:
    pct = percentage(attended, total)
    return {
        "attended": attended,
        "total": total,
        "percentage": pct,
        "risk": risk_level(pct),
        "classes_needed": classes_needed(attended, total),
        "can_skip": classes_can_skip(attended, total),
    }
