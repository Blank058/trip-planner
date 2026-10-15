from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from .. import db
from ..forms import parse_trip_form
from ..models import LocationOption, Response
from .results import build_results
from .trips import get_trip_or_404

bp = Blueprint("admin", __name__, url_prefix="/t/<slug>/admin/<key>")


def _admin_trip(slug, key):
    trip = get_trip_or_404(slug)
    if not trip.check_admin_key(key):
        abort(404)  # don't reveal that the trip exists
    return trip


def _back(trip, key):
    return redirect(url_for("admin.dashboard", slug=trip.slug, key=key))


@bp.get("/")
def dashboard(slug, key):
    trip = _admin_trip(slug, key)
    return render_template(
        "admin.html",
        trip=trip,
        key=key,
        results=build_results(trip),
        share_url=url_for("trips.respond", slug=trip.slug, _external=True),
        admin_url=url_for("admin.dashboard", slug=trip.slug, key=key, _external=True),
        just_created=request.args.get("created") == "1",
        errors=[],
    )


@bp.post("/toggle-open")
def toggle_open(slug, key):
    trip = _admin_trip(slug, key)
    trip.is_open = not trip.is_open
    db.session.commit()
    flash("Responses reopened." if trip.is_open else "Responses closed.")
    return _back(trip, key)


@bp.post("/toggle-public")
def toggle_public(slug, key):
    trip = _admin_trip(slug, key)
    trip.results_public = not trip.results_public
    db.session.commit()
    flash("Results are now visible to everyone with the link." if trip.results_public else "Results are now private.")
    return _back(trip, key)


@bp.post("/edit")
def edit(slug, key):
    trip = _admin_trip(slug, key)
    data, errors = parse_trip_form(request.form, require_locations=False)

    keep_ids = {int(i) for i in request.form.getlist("keep_location") if i.isdigit()}
    remaining = [loc for loc in trip.locations if loc.id in keep_ids]
    if len(remaining) + len(data["locations"]) < 2:
        errors.append("A trip needs at least two locations.")

    if errors:
        return (
            render_template(
                "admin.html",
                trip=trip,
                key=key,
                results=build_results(trip),
                share_url=url_for("trips.respond", slug=trip.slug, _external=True),
                admin_url=url_for("admin.dashboard", slug=trip.slug, key=key, _external=True),
                just_created=False,
                errors=errors,
            ),
            400,
        )

    trip.name = data["name"][:120]
    trip.description = data["description"]
    trip.min_days = data["min_days"]
    trip.max_days = data["max_days"]
    trip.window_start = data["window_start"]
    trip.window_end = data["window_end"]
    for loc in list(trip.locations):
        if loc.id not in keep_ids:
            trip.locations.remove(loc)  # cascades to everyone's ranks for it
    existing_names = {loc.name.lower() for loc in remaining}
    for name in data["locations"]:
        if name.lower() not in existing_names:
            trip.locations.append(LocationOption(name=name))
    db.session.commit()
    flash("Trip updated.")
    return _back(trip, key)


@bp.post("/responses/<int:response_id>/delete")
def delete_response(slug, key, response_id):
    trip = _admin_trip(slug, key)
    response = Response.query.filter_by(id=response_id, trip_id=trip.id).first_or_404()
    db.session.delete(response)
    db.session.commit()
    flash(f"Removed {response.name}'s response.")
    return _back(trip, key)


@bp.post("/delete")
def delete_trip(slug, key):
    trip = _admin_trip(slug, key)
    if request.form.get("confirm_name", "").strip() != trip.name:
        flash("Type the trip name exactly to delete it.")
        return _back(trip, key)
    db.session.delete(trip)
    db.session.commit()
    flash("Trip deleted.")
    return redirect(url_for("main.index"))
