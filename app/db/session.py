from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, make_url


def build_engine(url: str) -> Engine:
    if make_url(url).drivername != "postgresql+psycopg":
        raise ValueError("Use a postgresql+psycopg database URL")
    return create_engine(url, pool_pre_ping=True)
