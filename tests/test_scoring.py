from datetime import date, timedelta

from app.scoring import best_date_windows, calendar_months, daily_counts, is_tie, rank_locations


def days(start, n):
    return {start + timedelta(days=i) for i in range(n)}


# ---- locations


def test_borda_points_and_order():
    results = rank_locations(
        ["Lisbon", "Rome", "Oslo"],
        [["Lisbon", "Rome", "Oslo"], ["Rome", "Lisbon", "Oslo"], ["Lisbon", "Oslo", "Rome"]],
    )
    assert [(r.name, r.points, r.first_choices) for r in results] == [
        ("Lisbon", 8, 2),
        ("Rome", 6, 1),
        ("Oslo", 4, 0),
    ]
    assert not is_tie(results)


def test_ties_broken_by_first_choices_and_flagged():
    # Everyone ends on 4 points; A and C each have a first choice, B has none.
    results = rank_locations(["A", "B", "C"], [["A", "B", "C"], ["C", "B", "A"]])
    assert [r.name for r in results] == ["A", "C", "B"]
    assert is_tie(results)


def test_no_responses():
    results = rank_locations(["A", "B"], [])
    assert all(r.points == 0 for r in results)


def test_unknown_names_ignored():
    results = rank_locations(["A"], [["Z", "A"]])
    assert results[0].points == 0  # "A" was 2nd in that list, but N=1 so 1-1=0


# ---- dates

START = date(2027, 6, 1)
END = date(2027, 6, 30)


def test_finds_window_everyone_can_make():
    availability = {
        "Ann": days(date(2027, 6, 5), 10),  # 5–14
        "Bob": days(date(2027, 6, 8), 10),  # 8–17
        "Cat": days(date(2027, 6, 1), 12),  # 1–12
    }
    best = best_date_windows(START, END, 3, availability)[0]
    assert best.start == date(2027, 6, 8)
    assert best.end == date(2027, 6, 12)  # extended while all three stay free
    assert best.attendees == ["Ann", "Bob", "Cat"]
    assert best.missing == []


def test_respects_max_days():
    availability = {"Ann": days(START, 20)}
    best = best_date_windows(START, END, 3, availability, max_days=5)[0]
    assert best.days == 5


def test_prefers_more_people_over_longer_window():
    availability = {
        "Ann": days(date(2027, 6, 1), 10) | days(date(2027, 6, 20), 3),
        "Bob": days(date(2027, 6, 20), 3),
    }
    best = best_date_windows(START, END, 3, availability)[0]
    assert best.start == date(2027, 6, 20)
    assert len(best.attendees) == 2


def test_results_do_not_overlap():
    availability = {"Ann": days(START, 30)}
    windows = best_date_windows(START, END, 3, availability)
    for i, a in enumerate(windows):
        for b in windows[i + 1:]:
            assert a.end < b.start or b.end < a.start


def test_nobody_free_long_enough():
    availability = {"Ann": {date(2027, 6, 1), date(2027, 6, 3)}}
    assert best_date_windows(START, END, 2, availability) == []


def test_daily_counts_and_calendar():
    counts = daily_counts(START, END, {"A": {START}, "B": {START, END}})
    assert counts[START] == 2 and counts[END] == 1
    months = calendar_months(date(2027, 6, 28), date(2027, 7, 2))
    assert [m["title"] for m in months] == ["June 2027", "July 2027"]
