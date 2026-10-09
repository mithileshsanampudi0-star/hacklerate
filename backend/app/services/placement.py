"""Placement eligibility: compare a student against their batch's criteria."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Criteria:
    min_cgpa: float
    max_active_backlogs: int
    min_attendance_pct: float
    min_10th_pct: float
    min_12th_pct: float


def _check(name: str, required: float, actual: float | None, higher_is_better: bool = True) -> dict:
    if actual is None:
        return {"name": name, "required": required, "actual": None, "passed": False, "gap": None}
    passed = actual >= required if higher_is_better else actual <= required
    gap = 0 if passed else round(abs(required - actual), 2)
    return {"name": name, "required": required, "actual": actual, "passed": passed, "gap": gap}


def evaluate(
    criteria: Criteria | None,
    *,
    cgpa: float | None,
    active_backlogs: int,
    attendance_pct: float | None,
    tenth_pct: float | None,
    twelfth_pct: float | None,
) -> dict:
    if criteria is None:
        return {"eligible": False, "criteria_defined": False, "checks": []}

    checks = [
        _check("CGPA", criteria.min_cgpa, cgpa),
        _check("Active backlogs", criteria.max_active_backlogs, active_backlogs, higher_is_better=False),
        _check("Attendance %", criteria.min_attendance_pct, attendance_pct),
        _check("10th %", criteria.min_10th_pct, tenth_pct),
        _check("12th %", criteria.min_12th_pct, twelfth_pct),
    ]
    return {
        "eligible": all(c["passed"] for c in checks),
        "criteria_defined": True,
        "checks": checks,
    }
