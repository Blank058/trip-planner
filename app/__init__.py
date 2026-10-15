import os

from dotenv import load_dotenv
from flask import Flask, render_template
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix

db = SQLAlchemy()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, default_limits=[])


def _database_url():
    url = os.environ.get("DATABASE_URL")
    if not url:
        return None
    # Some providers hand out "postgres://", which SQLAlchemy no longer accepts.
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    return url


def create_app(test_config=None):
    load_dotenv()
    app = Flask(__name__, instance_relative_config=True)
    # Render sits in front of the app and terminates HTTPS; trust its headers so
    # generated links (share/admin URLs) use https:// and the real hostname.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    os.makedirs(app.instance_path, exist_ok=True)

    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-not-secret"),
        SQLALCHEMY_DATABASE_URI=_database_url()
        or "sqlite:///" + os.path.join(app.instance_path, "trip_planner.db"),
        SQLALCHEMY_ENGINE_OPTIONS={"pool_pre_ping": True},
        RATELIMIT_STORAGE_URI="memory://",
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    from .routes import admin, main, trips

    app.register_blueprint(main.bp)
    app.register_blueprint(trips.bp)
    app.register_blueprint(admin.bp)

    @app.errorhandler(404)
    def not_found(_):
        return render_template("404.html"), 404

    with app.app_context():
        from . import models  # noqa: F401  (registers the tables)

        db.create_all()

    return app
