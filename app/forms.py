"""Reading and validating submitted forms. Each function returns (data, errors)."""

from datetime import date

MAX_WINDOW_DAYS = 366


def _parse_date(value):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _parse_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def parse_trip_form(form, require_locations=True):
    errors = []
    data = {
        "name": form.get("name", "").strip(),
        "description": form.get("description", "").strip(),
        "min_days": _parse_int(form.get("min_days")),
        "max_days": _parse_int(form.get("max_days")) if form.get("max_days") else None,
        "window_start": _parse_date(form.get("window_start")),
        "window_end": _parse_date(form.get("window_end")),
    }

    # Keep the order the admin typed, drop blanks and duplicates.
    locations = []
    for raw in form.getlist("locations"):
        name = raw.strip()
        if name and name.lower() not in (l.lower() for l in locations):
            locations.append(name[:120])
    data["locations"] = locations

    if not data["name"]:
        errors.append("Give the trip a name.")
    if require_locations and len(locations) < 2:
        errors.append("Add at least two locations to vote on.")
    if not data["min_days"] or data["min_days"] < 1:
        errors.append("Minimum trip length must be at least 1 day.")
    if data["max_days"] is not None and data["min_days"] and data["max_days"] < data["min_days"]:
        errors.append("Maximum trip length can't be shorter than the minimum.")
    if not data["window_start"] or not data["window_end"]:
        errors.append("Pick both a start and an end date for the date range.")
    elif data["window_end"] < data["window_start"]:
        errors.append("The date range ends before it starts.")
    else:
        length = (data["window_end"] - data["window_start"]).days + 1
        if length > MAX_WINDOW_DAYS:
            errors.append("Keep the date range to a year or less.")
        if data["min_days"] and length < data["min_days"]:
            errors.append(f"The date range is only {length} days, shorter than the minimum trip length.")
    return data, errors


def parse_response_form(form, trip):
    errors = []
    name = form.get("name", "").strip()[:80]

    valid_ids = {loc.id for loc in trip.locations}
    ranking = []
    for raw in form.get("ranking", "").split(","):
        loc_id = _parse_int(raw)
        if loc_id in valid_ids and loc_id not in ranking:
            ranking.append(loc_id)
    # Anything not sent (e.g. JavaScript off) goes to the bottom in its original order.
    ranking += [loc.id for loc in trip.locations if loc.id not in ranking]

    days = set()
    for raw in form.get("days", "").split(","):
        d = _parse_date(raw.strip())
        if d and trip.window_start <= d <= trip.window_end:
            days.add(d)

    if not name:
        errors.append("Enter your name.")
    if not days:
        errors.append("Select at least one day you're available.")
    return {"name": name, "ranking": ranking, "days": days}, errors
