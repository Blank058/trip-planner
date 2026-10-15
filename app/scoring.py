"""Result calculations. Plain Python with no Flask or database code, so it is easy to test."""

import calendar
from dataclasses import dataclass, field
from datetime import date, timedelta


# ---------------------------------------------------------------- locations


@dataclass
class LocationResult:
    name: str
    points: int = 0
    first_choices: int = 0


def rank_locations(location_names, rankings):
    """Score locations with a Borda count.

    location_names: list of all location names.
    rankings: one list per respondent, location names in order of preference
              (favourite first). Locations a respondent left out score 0 from them.

    With N locations, a 1st choice earns N points, 2nd earns N-1, and so on.
    Returns LocationResults sorted best first. Ties are broken by number of
    first choices, then alphabetically.
    """
    n = len(location_names)
    results = {name: LocationResult(name) for name in location_names}
    for ranking in rankings:
        for position, name in enumerate(ranking):
            if name not in results:
                continue
            results[name].points += n - position
            if position == 0:
                results[name].first_choices += 1
    return sorted(results.values(), key=lambda r: (-r.points, -r.first_choices, r.name.lower()))


def is_tie(results):
    return (
        len(results) >= 2
        and results[0].points == results[1].points
        and results[0].first_choices == results[1].first_choices
    )


# -------------------------------------------------------------------- dates


@dataclass
class DateWindow:
    start: date
    end: date
    attendees: list = field(default_factory=list)
    missing: list = field(default_factory=list)
    person_days: int = 0

    @property
    def days(self):
        return (self.end - self.start).days + 1


def daterange(start, end):
    day = start
    while day <= end:
        yield day
        day += timedelta(days=1)


def best_date_windows(window_start, window_end, min_days, availability, max_days=None, top=5):
    """Find the best trip dates.

    availability: dict of respondent name -> set of dates they are free.

    Every run of `min_days` consecutive days is scored by how many people are free
    on all of those days (tie-break: total person-days free in the run, then the
    earliest start). Each run is then extended day by day while everyone attending
    stays free, up to `max_days`. The top non-overlapping runs are returned.
    """
    everyone = sorted(availability)
    candidates = []
    start = window_start
    while start + timedelta(days=min_days - 1) <= window_end:
        end = start + timedelta(days=min_days - 1)
        span = list(daterange(start, end))
        attendees = [p for p in everyone if all(d in availability[p] for d in span)]
        if attendees:
            # Extend while the same group stays available.
            while (
                end + timedelta(days=1) <= window_end
                and (max_days is None or (end - start).days + 1 < max_days)
                and all(end + timedelta(days=1) in availability[p] for p in attendees)
            ):
                end += timedelta(days=1)
                span.append(end)
            person_days = sum(1 for p in everyone for d in span if d in availability[p])
            candidates.append(
                DateWindow(
                    start=start,
                    end=end,
                    attendees=attendees,
                    missing=[p for p in everyone if p not in attendees],
                    person_days=person_days,
                )
            )
        start += timedelta(days=1)

    candidates.sort(key=lambda w: (-len(w.attendees), -w.person_days, w.start))
    chosen = []
    for window in candidates:
        if any(window.start <= c.end and c.start <= window.end for c in chosen):
            continue
        chosen.append(window)
        if len(chosen) == top:
            break
    return chosen


def daily_counts(window_start, window_end, availability):
    counts = {d: 0 for d in daterange(window_start, window_end)}
    for days in availability.values():
        for d in days:
            if d in counts:
                counts[d] += 1
    return counts


def calendar_months(window_start, window_end):
    """Months covering the window, as week rows of dates (None = outside the window).

    Used by the templates to draw the availability calendar and heatmap.
    """
    months = []
    year, month = window_start.year, window_start.month
    cal = calendar.Calendar(firstweekday=0)  # Monday first
    while (year, month) <= (window_end.year, window_end.month):
        weeks = []
        for week in cal.monthdatescalendar(year, month):
            weeks.append(
                [d if d.month == month and window_start <= d <= window_end else None for d in week]
            )
        weeks = [w for w in weeks if any(w)]
        months.append({"title": date(year, month, 1).strftime("%B %Y"), "weeks": weeks})
        month += 1
        if month == 13:
            year, month = year + 1, 1
    return months
