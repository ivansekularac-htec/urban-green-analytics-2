import logging
from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import settings

logger = logging.getLogger("uvicorn.error")

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


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
