# Trip Planner

A "Google Forms for trips". Create a trip with some candidate locations and a date range, share the link, and everyone ranks the locations and marks the days they're free. The admin page shows the most popular location and the best dates.

- **No logins.** Creating a trip gives you a secret admin link. Anyone with the share link can respond; respondents can edit their answer from the same browser.
- **Locations** are ranked by everyone and scored with a Borda count (1st choice = N points, 2nd = N-1, ...).
- **Dates**: every run of at least the minimum trip length is scored by how many people are free for all of it, then stretched while that group stays free.

Built with Python, Flask, SQLAlchemy, Jinja templates, [Pico CSS](https://picocss.com) and a little JavaScript for the calendar.

## Run it locally

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # optional: set SECRET_KEY / DATABASE_URL
flask --app app run --debug
```

Open http://127.0.0.1:5000. Without `DATABASE_URL` the app uses a local SQLite file at `instance/trip_planner.db`. Tables are created automatically on start-up.

Run the tests:

```bash
python -m pytest
```

## Deploying

See [docs/DEPLOY.md](docs/DEPLOY.md) for setting up Supabase (database) and Render (hosting).

## Project layout

```
app/
  __init__.py        create_app(): config, database, CSRF, rate limiting
  models.py          Trip, LocationOption, Response, LocationRank, AvailableDay
  scoring.py         the result calculations (pure Python, no Flask)
  forms.py           reading and validating submitted forms
  routes/
    main.py          homepage + create trip
    trips.py         response form, thanks page, public results
    admin.py         admin dashboard and actions
    results.py       turns database rows into the numbers the results page shows
  templates/         Jinja pages (_calendar.html and _results.html are shared macros)
  static/            style.css, respond.js (ranking + calendar), vendor/ (Pico, SortableJS)
tests/               pytest tests for scoring and the main flows
render.yaml          Render deployment config
```

## How the pieces fit

| URL | What it is |
|---|---|
| `/` | Create a trip; lists trips you created in this browser |
| `/t/<slug>` | Share link: the response form |
| `/t/<slug>/admin/<key>/` | Admin dashboard (secret) |
| `/t/<slug>/results` | Read-only results, only if the admin turns it on |

The admin key and respondents' edit tokens are only stored as SHA-256 hashes, so the database alone can't be used to take over a trip.

## Ideas for later

- Database migrations with Flask-Migrate (tables are currently created with `db.create_all()`, which won't alter existing tables if you change a model)
- Email the admin when someone responds
- Per-location availability
