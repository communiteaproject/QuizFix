from sqlmodel import Session, SQLModel, create_engine
from contextlib import contextmanager
from typing import Generator

DATABASE_URL = "sqlite:///./trivia.db"

engine = create_engine(DATABASE_URL, echo=False)


def init_db() -> None:
    """Create all database tables."""
    import backend.models  # noqa: F401  # Ensure models are registered before create_all
    SQLModel.metadata.create_all(engine)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Yield a SQLModel Session with proper cleanup."""
    with Session(engine) as session:
        yield session 