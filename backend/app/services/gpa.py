"""SGPA / CGPA calculation on a 10-point scale.

SGPA  = sum(credits * grade_points) / sum(credits) over one semester (fails count as 0).
CGPA  = the same formula over every course, using each course's best attempt so a
        cleared backlog replaces the earlier F.
Year GPA = the same formula over the two semesters of an academic year.
"""

from collections.abc import Iterable
from dataclasses import dataclass

# (minimum total %, grade, grade points), checked top-down
GRADE_SCALE: list[tuple[float, str, float]] = [
    (90, "O", 10),
    (80, "A+", 9),
    (70, "A", 8),
    (60, "B+", 7),
    (50, "B", 6),
    (45, "C", 5),
    (40, "P", 4),
    (0, "F", 0),
]


@dataclass(frozen=True)
class CourseGrade:
    semester: int
    course_id: int
    credits: int
    grade_points: float


def grade_for_total(total_pct: float) -> tuple[str, float]:
    for minimum, grade, points in GRADE_SCALE:
        if total_pct >= minimum:
            return grade, points
    return "F", 0.0


def year_of(semester: int) -> int:
    return (semester + 1) // 2


def weighted_gpa(grades: Iterable[CourseGrade]) -> float | None:
    grades = list(grades)
    total_credits = sum(g.credits for g in grades)
    if not total_credits:
        return None
    return round(sum(g.credits * g.grade_points for g in grades) / total_credits, 2)


def best_attempts(grades: Iterable[CourseGrade]) -> dict[int, CourseGrade]:
    best: dict[int, CourseGrade] = {}
    for g in grades:
        cur = best.get(g.course_id)
        if cur is None or (g.grade_points, g.semester) > (cur.grade_points, cur.semester):
            best[g.course_id] = g
    return best


def cgpa(grades: Iterable[CourseGrade]) -> float | None:
    return weighted_gpa(best_attempts(grades).values())


def active_backlogs(grades: Iterable[CourseGrade]) -> int:
    return sum(1 for g in best_attempts(grades).values() if g.grade_points == 0)


def summarize(grades: Iterable[CourseGrade]) -> dict:
    grades = list(grades)
    sems = sorted({g.semester for g in grades})

    semesters = []
    for s in sems:
        in_sem = [g for g in grades if g.semester == s]
        semesters.append(
            {
                "semester": s,
                "sgpa": weighted_gpa(in_sem),
                "credits": sum(g.credits for g in in_sem),
                "credits_earned": sum(g.credits for g in in_sem if g.grade_points > 0),
                "cgpa_upto": cgpa(g for g in grades if g.semester <= s),
            }
        )

    years = []
    for y in sorted({year_of(s) for s in sems}):
        years.append(
            {
                "year": y,
                "semesters": [s for s in sems if year_of(s) == y],
                "gpa": weighted_gpa(g for g in grades if year_of(g.semester) == y),
            }
        )

    best = best_attempts(grades)
    return {
        "semesters": semesters,
        "years": years,
        "cgpa": weighted_gpa(best.values()),
        "credits_earned": sum(g.credits for g in best.values() if g.grade_points > 0),
        "active_backlogs": sum(1 for g in best.values() if g.grade_points == 0),
    }
