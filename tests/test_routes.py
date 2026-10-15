import re

from app.models import Trip

TRIP_FORM = {
    "name": "Summer trip",
    "locations": ["Lisbon", "Rome", "Oslo"],
    "min_days": "3",
    "window_start": "2027-06-01",
    "window_end": "2027-06-30",
}


def create(client, **overrides):
    resp = client.post("/", data={**TRIP_FORM, **overrides})
    assert resp.status_code == 302, resp.data
    slug, key = re.match(r".*/t/([^/]+)/admin/([^/?]+)/", resp.headers["Location"]).groups()
    return slug, key


def test_homepage(client):
    assert b"Create trip" in client.get("/").data


def test_create_validation(client):
    resp = client.post("/", data={**TRIP_FORM, "locations": ["Only one"]})
    assert resp.status_code == 400
    assert b"at least two locations" in resp.data


def test_full_flow(client, app):
    slug, key = create(client)

    with app.app_context():
        trip = Trip.query.filter_by(slug=slug).one()
        assert trip.admin_key_hash != key  # only the hash is stored
        ids = {loc.name: loc.id for loc in trip.locations}

    # Two people respond, each with their own browser.
    ann = app.test_client()
    ann.post(f"/t/{slug}", data={
        "name": "Ann",
        "ranking": f"{ids['Rome']},{ids['Lisbon']},{ids['Oslo']}",
        "days": "2027-06-10,2027-06-11,2027-06-12,2027-06-13",
    })
    bob = app.test_client()
    resp = bob.post(f"/t/{slug}", data={
        "name": "Bob",
        "ranking": f"{ids['Rome']},{ids['Oslo']},{ids['Lisbon']}",
        "days": "2027-06-11,2027-06-12,2027-06-13,2027-06-14",
    })
    assert resp.status_code == 302

    page = client.get(f"/t/{slug}/admin/{key}/").data.decode()
    assert "Rome" in page.split("Most popular location")[1][:200]
    assert "Fri 11 Jun – Sun 13 Jun" in page
    assert "2 of 2 can come" in page

    # Ann edits her response instead of creating a second one.
    ann.post(f"/t/{slug}", data={"name": "Ann B", "ranking": "", "days": "2027-06-01"})
    with app.app_context():
        trip = Trip.query.filter_by(slug=slug).one()
        assert sorted(r.name for r in trip.responses) == ["Ann B", "Bob"]


def test_wrong_admin_key_is_404(client):
    slug, _ = create(client)
    assert client.get(f"/t/{slug}/admin/wrong/").status_code == 404


def test_results_private_until_toggled(client):
    slug, key = create(client)
    assert client.get(f"/t/{slug}/results").status_code == 404
    client.post(f"/t/{slug}/admin/{key}/toggle-public")
    assert client.get(f"/t/{slug}/results").status_code == 200


def test_closed_trip_rejects_responses(client):
    slug, key = create(client)
    client.post(f"/t/{slug}/admin/{key}/toggle-open")
    resp = client.post(f"/t/{slug}", data={"name": "Late", "days": "2027-06-01"})
    assert resp.status_code == 403


def test_response_requires_days(client):
    slug, _ = create(client)
    resp = client.post(f"/t/{slug}", data={"name": "Ann", "days": ""})
    assert resp.status_code == 400


def test_delete_trip_needs_name(client, app):
    slug, key = create(client)
    client.post(f"/t/{slug}/admin/{key}/delete", data={"confirm_name": "nope"})
    with app.app_context():
        assert Trip.query.filter_by(slug=slug).count() == 1
    client.post(f"/t/{slug}/admin/{key}/delete", data={"confirm_name": "Summer trip"})
    with app.app_context():
        assert Trip.query.filter_by(slug=slug).count() == 0
