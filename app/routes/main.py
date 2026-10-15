from flask import Blueprint, redirect, render_template, request, url_for

from .. import db, limiter
from ..forms import parse_trip_form
from ..models import LocationOption, Trip, hash_token, new_token

bp = Blueprint("main", __name__)


def _unique_slug():
    while True:
        slug = new_token(6)
        if not Trip.query.filter_by(slug=slug).first():
            return slug


def _my_trips():
    """Trips this browser created, remembered by the admin cookie set on creation."""
    trips = []
    for cookie, key in request.cookies.items():
        if cookie.startswith("admin_"):
            trip = Trip.query.filter_by(slug=cookie[len("admin_"):]).first()
            if trip and trip.check_admin_key(key):
                trips.append((trip, key))
    return sorted(trips, key=lambda t: t[0].created_at, reverse=True)


@bp.get("/")
def index():
    return render_template("index.html", form={}, errors=[], my_trips=_my_trips())


@bp.post("/")
@limiter.limit("20 per hour", methods=["POST"])
def create_trip():
    data, errors = parse_trip_form(request.form)
    if errors:
        return render_template("index.html", form=request.form, errors=errors, my_trips=_my_trips()), 400

    admin_key = new_token()
    trip = Trip(
        slug=_unique_slug(),
        admin_key_hash=hash_token(admin_key),
        name=data["name"][:120],
        description=data["description"],
        min_days=data["min_days"],
        max_days=data["max_days"],
        window_start=data["window_start"],
        window_end=data["window_end"],
    )
    trip.locations = [LocationOption(name=name) for name in data["locations"]]
    db.session.add(trip)
    db.session.commit()

    # The admin key is only ever shown here and in the admin URL; we store just its hash.
    response = redirect(url_for("admin.dashboard", slug=trip.slug, key=admin_key, created=1))
    response.set_cookie(
        f"admin_{trip.slug}", admin_key, max_age=60 * 60 * 24 * 365, httponly=True, samesite="Lax"
    )
    return response
