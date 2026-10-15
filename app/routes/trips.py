from flask import Blueprint, abort, redirect, render_template, request, url_for

from .. import db, limiter
from ..forms import parse_response_form
from ..models import AvailableDay, LocationRank, Response, Trip, hash_token, new_token
from ..scoring import calendar_months
from .results import build_results

bp = Blueprint("trips", __name__, url_prefix="/t")

COOKIE_AGE = 60 * 60 * 24 * 365


def get_trip_or_404(slug):
    trip = Trip.query.filter_by(slug=slug).first()
    if not trip:
        abort(404)
    return trip


def _own_response(trip):
    """The response this browser submitted earlier, found by its cookie token."""
    token = request.cookies.get(f"resp_{trip.slug}")
    if not token:
        return None
    return Response.query.filter_by(trip_id=trip.id, edit_token_hash=hash_token(token)).first()


def _render_form(trip, existing, form=None, errors=(), status=200):
    if form is not None:
        ranking = [int(x) for x in form.get("ranking", "").split(",") if x.isdigit()]
        days = {d for d in form.get("days", "").split(",") if d}
        name = form.get("name", "")
    elif existing:
        ranking = [r.location_id for r in existing.ranks]
        days = {d.date.isoformat() for d in existing.days}
        name = existing.name
    else:
        ranking, days, name = [], set(), ""

    by_id = {loc.id: loc for loc in trip.locations}
    ordered = [by_id[i] for i in ranking if i in by_id]
    ordered += [loc for loc in trip.locations if loc not in ordered]

    return (
        render_template(
            "respond.html",
            trip=trip,
            existing=existing,
            name=name,
            ordered_locations=ordered,
            selected_days=days,
            months=calendar_months(trip.window_start, trip.window_end),
            errors=errors,
        ),
        status,
    )


@bp.get("/<slug>")
def respond(slug):
    trip = get_trip_or_404(slug)
    existing = _own_response(trip)
    if not trip.is_open:
        return render_template("closed.html", trip=trip)
    return _render_form(trip, existing)


@bp.post("/<slug>")
@limiter.limit("30 per hour", methods=["POST"])
def submit_response(slug):
    trip = get_trip_or_404(slug)
    if not trip.is_open:
        return render_template("closed.html", trip=trip), 403

    existing = _own_response(trip)
    data, errors = parse_response_form(request.form, trip)
    if errors:
        return _render_form(trip, existing, form=request.form, errors=errors, status=400)

    token = None
    if existing:
        response = existing
        response.ranks.clear()
        response.days.clear()
        db.session.flush()
    else:
        token = new_token()
        response = Response(trip=trip, edit_token_hash=hash_token(token))
        db.session.add(response)

    response.name = data["name"]
    response.ranks = [LocationRank(location_id=loc_id, rank=i + 1) for i, loc_id in enumerate(data["ranking"])]
    response.days = [AvailableDay(date=d) for d in sorted(data["days"])]
    db.session.commit()

    redirect_response = redirect(url_for("trips.thanks", slug=trip.slug))
    if token:
        redirect_response.set_cookie(
            f"resp_{trip.slug}", token, max_age=COOKIE_AGE, httponly=True, samesite="Lax"
        )
    return redirect_response


@bp.get("/<slug>/thanks")
def thanks(slug):
    trip = get_trip_or_404(slug)
    return render_template("thanks.html", trip=trip)


@bp.get("/<slug>/results")
def public_results(slug):
    trip = get_trip_or_404(slug)
    if not trip.results_public:
        abort(404)
    return render_template("public_results.html", trip=trip, results=build_results(trip))
