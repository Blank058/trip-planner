import sqlalchemy as sa

from app import _database_url


def test_supabase_url_uses_installed_psycopg2_driver(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://postgres.abc:pw@aws-0-eu.pooler.supabase.com:5432/postgres")
    url = _database_url()
    assert url == "postgresql+psycopg2://postgres.abc:pw@aws-0-eu.pooler.supabase.com:5432/postgres"
    sa.create_engine(url)  # would raise ModuleNotFoundError: psycopg without the fix


def test_old_postgres_scheme(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://u:p@h/db")
    assert _database_url() == "postgresql+psycopg2://u:p@h/db"


def test_explicit_driver_left_alone(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg2://u:p@h/db")
    assert _database_url() == "postgresql+psycopg2://u:p@h/db"


def test_no_url_means_sqlite(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert _database_url() is None
