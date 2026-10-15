"""Turns a trip's database rows into the numbers shown on the results pages."""

from ..scoring import best_date_windows, calendar_months, daily_counts, is_tie, rank_locations


def build_results(trip):
    loc_names = {loc.id: loc.name for loc in trip.locations}
    rankings = [[loc_names[r.location_id] for r in resp.ranks if r.location_id in loc_names] for resp in trip.responses]
    locations = rank_locations(list(loc_names.values()), rankings)

    # Two people can share a name, so label duplicates "Sam (2)".
    availability, seen = {}, {}
    for resp in trip.responses:
        seen[resp.name] = seen.get(resp.name, 0) + 1
        label = resp.name if seen[resp.name] == 1 else f"{resp.name} ({seen[resp.name]})"
        availability[label] = {d.date for d in resp.days}

    counts = daily_counts(trip.window_start, trip.window_end, availability)
    total = len(trip.responses)
    return {
        "total": total,
        "locations": locations,
        "location_tie": is_tie(locations),
        "max_points": max((l.points for l in locations), default=0) or 1,
        "windows": best_date_windows(
            trip.window_start, trip.window_end, trip.min_days, availability, max_days=trip.max_days
        ),
        "counts": counts,
        "max_count": max(counts.values(), default=0) or 1,
        "months": calendar_months(trip.window_start, trip.window_end),
    }
