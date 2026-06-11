import logging
from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

logger = logging.getLogger(__name__)

engine = create_engine(
    get_settings().database_url,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


class Base(DeclarativeBase):
    pass


def verify_db_connection() -> None:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        logger.info("Successfully connected to the PostgreSQL database.")

    except SQLAlchemyError:
        logger.exception("Database connection failed.")
        raise


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()
