from app.services import attendance as att
from app.services import gpa
from app.services import placement as plc
from app.services.results import course_total


def G(sem, cid, credits, points):
    return gpa.CourseGrade(sem, cid, credits, points)


def test_grade_scale_boundaries():
    assert gpa.grade_for_total(90) == ("O", 10)
    assert gpa.grade_for_total(89.99) == ("A+", 9)
    assert gpa.grade_for_total(40) == ("P", 4)
    assert gpa.grade_for_total(39.9) == ("F", 0)


def test_sgpa_is_credit_weighted():
    # (4*10 + 3*8 + 2*6) / 9 = 76/9 = 8.44
    assert gpa.weighted_gpa([G(1, 1, 4, 10), G(1, 2, 3, 8), G(1, 3, 2, 6)]) == 8.44
    assert gpa.weighted_gpa([]) is None


def test_cgpa_uses_best_attempt_and_counts_backlogs():
    grades = [G(1, 1, 4, 0), G(1, 2, 4, 8), G(2, 3, 4, 9), G(2, 1, 4, 6)]  # course 1 failed, cleared in sem 2
    summary = gpa.summarize(grades)
    assert summary["semesters"][0]["sgpa"] == 4.0  # F counts as 0 in its semester
    assert summary["semesters"][0]["cgpa_upto"] == 4.0
    assert summary["cgpa"] == round((6 * 4 + 8 * 4 + 9 * 4) / 12, 2)
    assert summary["active_backlogs"] == 0
    assert gpa.active_backlogs(grades[:2]) == 1


def test_year_gpa_groups_two_semesters():
    summary = gpa.summarize([G(1, 1, 4, 10), G(2, 2, 4, 8), G(3, 3, 4, 6)])
    assert summary["years"] == [
        {"year": 1, "semesters": [1, 2], "gpa": 9.0},
        {"year": 2, "semesters": [3], "gpa": 6.0},
    ]


def test_attendance_risk_thresholds():
    assert att.risk_level(85) == "safe"
    assert att.risk_level(84.99) == "warning"
    assert att.risk_level(75) == "warning"
    assert att.risk_level(74.99) == "critical"
    assert att.risk_level(None) == "safe"


def test_classes_needed_and_can_skip():
    assert att.classes_needed(6, 10) == 6  # 12/16 = 75%
    assert att.classes_needed(8, 10) == 0
    assert att.classes_can_skip(9, 10) == 2  # 9/12 = 75%
    assert att.classes_can_skip(6, 10) == 0
    assert att.summarize(0, 0)["percentage"] is None


def test_placement_eligibility():
    criteria = plc.Criteria(6.5, 0, 75, 60, 60)
    ok = plc.evaluate(criteria, cgpa=7.2, active_backlogs=0, attendance_pct=80, tenth_pct=70, twelfth_pct=65)
    assert ok["eligible"] is True
    bad = plc.evaluate(criteria, cgpa=6.0, active_backlogs=1, attendance_pct=80, tenth_pct=70, twelfth_pct=65)
    assert bad["eligible"] is False
    failed = {c["name"]: c for c in bad["checks"] if not c["passed"]}
    assert set(failed) == {"CGPA", "Active backlogs"}
    assert failed["CGPA"]["gap"] == 0.5
    assert plc.evaluate(None, cgpa=9, active_backlogs=0, attendance_pct=90, tenth_pct=90, twelfth_pct=90)[
        "eligible"
    ] is False


def test_course_total_weights_marks():
    # 24/30 of 15 + 15/20 of 10 + 70/100 of 60, internal2 missing -> 0
    assert course_total([(30, 15, 24), (20, 10, 15), (30, 15, None), (100, 60, 70)]) == 12 + 7.5 + 42
