import hashlib
import secrets
from datetime import datetime, timezone

from . import db


def hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()


def new_token(nbytes=24):
    return secrets.token_urlsafe(nbytes)


def utcnow():
    return datetime.now(timezone.utc)


class Trip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(16), unique=True, nullable=False, index=True)
    admin_key_hash = db.Column(db.String(64), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, default="")
    min_days = db.Column(db.Integer, nullable=False)
    max_days = db.Column(db.Integer)
    window_start = db.Column(db.Date, nullable=False)
    window_end = db.Column(db.Date, nullable=False)
    is_open = db.Column(db.Boolean, default=True, nullable=False)
    results_public = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)

    locations = db.relationship(
        "LocationOption", backref="trip", cascade="all, delete-orphan", order_by="LocationOption.id"
    )
    responses = db.relationship(
        "Response", backref="trip", cascade="all, delete-orphan", order_by="Response.created_at"
    )

    def check_admin_key(self, key):
        return secrets.compare_digest(self.admin_key_hash, hash_token(key or ""))


class LocationOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey("trip.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)

    ranks = db.relationship("LocationRank", backref="location", cascade="all, delete-orphan")


class Response(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey("trip.id"), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    edit_token_hash = db.Column(db.String(64), nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    ranks = db.relationship(
        "LocationRank", backref="response", cascade="all, delete-orphan", order_by="LocationRank.rank"
    )
    days = db.relationship("AvailableDay", backref="response", cascade="all, delete-orphan")


class LocationRank(db.Model):
    response_id = db.Column(db.Integer, db.ForeignKey("response.id"), primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey("location_option.id"), primary_key=True)
    rank = db.Column(db.Integer, nullable=False)  # 1 = favourite


class AvailableDay(db.Model):
    response_id = db.Column(db.Integer, db.ForeignKey("response.id"), primary_key=True)
    date = db.Column(db.Date, primary_key=True)
