import os
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.engine import make_url

from app.core.config import Settings
from app.db.session import build_engine


@pytest.fixture
def isolated_database(monkeypatch, tmp_path):
    raw_url = os.environ.get("INVOICEIQ_TEST_DATABASE_URL")
    if not raw_url:
        pytest.fail("Set INVOICEIQ_TEST_DATABASE_URL to the dedicated invoiceiq_test database")
    url = make_url(raw_url)
    if url.database != "invoiceiq_test" or url.drivername != "postgresql+psycopg":
        pytest.fail("Tests require postgresql+psycopg and database invoiceiq_test")
    engine = build_engine(raw_url)
    schemas = []

    def create():
        schema = f"test_{uuid4().hex}"
        with engine.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        schemas.append(schema)
        scoped_url = url.update_query_dict({"options": f"-csearch_path={schema}"})
        rendered = scoped_url.render_as_string(hide_password=False)
        monkeypatch.setenv("INVOICEIQ_DATABASE_URL", rendered)
        command.upgrade(Config("alembic.ini"), "head")
        return Settings(environment="test", database_url=rendered, upload_dir=tmp_path / schema)

    try:
        yield create
    finally:
        try:
            with engine.begin() as connection:
                for schema in schemas:
                    connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        finally:
            engine.dispose()


@pytest.fixture
def db_settings(isolated_database):
    return isolated_database()
