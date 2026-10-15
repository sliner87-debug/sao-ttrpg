"""
backend/database/engine.py
==========================
SQLAlchemy 2.0 Database Engine Factory, WAL Mode Configuration & Transaction Manager.

Provides:
- SQLite WAL mode configuration with PRAGMAs:
    * PRAGMA journal_mode = WAL;
    * PRAGMA synchronous = NORMAL;
    * PRAGMA busy_timeout = 30000;
    * PRAGMA foreign_keys = ON;
- PostgreSQL connection pooling with QueuePool (pool_size=10, max_overflow=20).
- Atomic transaction context manager `db_transaction()` with commit/rollback and post-commit hook support.
- Schema creation helper `init_db()` and teardown helper `drop_db()`.
- Thread-safe session factories and health check diagnostics.
"""

from __future__ import annotations

from contextlib import contextmanager
import logging
import os
from typing import Any, Callable, Dict, Generator, Optional

from sqlalchemy import Engine, MetaData, create_engine, event, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, scoped_session, sessionmaker
from sqlalchemy.pool import QueuePool, StaticPool

logger = logging.getLogger("backend.database.engine")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

# ==============================================================================
# Configuration Constants
# ==============================================================================
DEFAULT_DATABASE_URL: str = "sqlite:///sao_sandbox.db"
ENV_DATABASE_URL_KEY: str = "SAO_DATABASE_URL"

# SQLite WAL Configuration
SQLITE_BUSY_TIMEOUT_MS: int = 30000  # 30 seconds
SQLITE_TIMEOUT_SEC: float = 30.0

# PostgreSQL Connection Pool Configuration
POSTGRES_POOL_SIZE: int = 10
POSTGRES_MAX_OVERFLOW: int = 20
POSTGRES_POOL_RECYCLE_SEC: int = 3600  # 1 hour
POSTGRES_POOL_TIMEOUT_SEC: int = 30

# Module-level singletons
_cached_engine: Optional[Engine] = None
_cached_session_factory: Optional[sessionmaker[Session]] = None


# ==============================================================================
# SQLite PRAGMA Listener
# ==============================================================================
def set_sqlite_pragma(dbapi_connection: Any, connection_record: Any) -> None:
    """
    Sets performance, concurrency, and integrity PRAGMAs on every new SQLite connection.

    PRAGMAs configured:
    - journal_mode = WAL:
        Write-Ahead Logging enables simultaneous readers and writers without lock contention.
    - synchronous = NORMAL:
        Syncs at critical checkpoints only; ACID-compliant, prevents corruption while maximizing write throughput.
    - busy_timeout = 30000:
        Waits up to 30,000ms (30 seconds) on lock contention before raising OperationalError.
    - foreign_keys = ON:
        Enforces relational foreign key constraints and cascade deletes on child tables.
    """
    try:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode = WAL;")
        cursor.execute("PRAGMA synchronous = NORMAL;")
        cursor.execute(f"PRAGMA busy_timeout = {SQLITE_BUSY_TIMEOUT_MS};")
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.close()
    except Exception as exc:  # pragma: no cover
        logger.warning("Failed to apply SQLite PRAGMAs on connection: %s", exc)


# ==============================================================================
# Engine Factory
# ==============================================================================
def resolve_database_url(database_url: Optional[str] = None) -> str:
    """
    Resolves database URL from argument, environment variable, or default SQLite path.
    Normalizes legacy 'postgres://' prefixes to 'postgresql+psycopg2://' for SQLAlchemy 2.0 compliance.
    """
    url = database_url or os.environ.get(ENV_DATABASE_URL_KEY) or DEFAULT_DATABASE_URL
    if url.startswith("postgres://"):
        url = "postgresql+psycopg2://" + url[len("postgres://") :]
    return url


def create_sao_engine(
    database_url: Optional[str] = None,
    echo: bool = False,
) -> Engine:
    """
    Factory function creating a configured SQLAlchemy 2.0 Engine.

    Supports:
    - SQLite (File): QueuePool with WAL mode PRAGMAs and 30s busy timeout.
    - SQLite (Memory): StaticPool to preserve tables across connections.
    - PostgreSQL: QueuePool with pool_size=10, max_overflow=20, pre-ping, and recycling.
    """
    resolved_url = resolve_database_url(database_url)
    parsed_url = make_url(resolved_url)
    backend_name = parsed_url.get_backend_name().lower()

    if backend_name == "sqlite":
        # Detect in-memory databases
        is_memory = (
            parsed_url.database in (None, "", ":memory:")
            or ":memory:" in resolved_url
            or "mode=memory" in resolved_url
        )

        if is_memory:
            engine = create_engine(
                resolved_url,
                poolclass=StaticPool,
                connect_args={"check_same_thread": False},
                echo=echo,
            )
        else:
            # Ensure target directory exists for file-based SQLite
            db_file = parsed_url.database
            if db_file and not os.path.isabs(db_file):
                db_dir = os.path.dirname(os.path.abspath(db_file))
            elif db_file:
                db_dir = os.path.dirname(db_file)
            else:
                db_dir = ""

            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)

            engine = create_engine(
                resolved_url,
                poolclass=QueuePool,
                pool_size=10,
                max_overflow=20,
                connect_args={
                    "check_same_thread": False,
                    "timeout": SQLITE_TIMEOUT_SEC,
                },
                echo=echo,
            )

        # Attach SQLite PRAGMA hook to connection event
        event.listen(engine, "connect", set_sqlite_pragma)
        logger.info("Configured SQLite engine with WAL mode: %s", resolved_url)

    elif backend_name in ("postgresql", "postgres"):
        try:
            engine = create_engine(
                resolved_url,
                poolclass=QueuePool,
                pool_size=POSTGRES_POOL_SIZE,
                max_overflow=POSTGRES_MAX_OVERFLOW,
                pool_pre_ping=True,
                pool_recycle=POSTGRES_POOL_RECYCLE_SEC,
                pool_timeout=POSTGRES_POOL_TIMEOUT_SEC,
                echo=echo,
            )
            logger.info("Configured PostgreSQL engine with QueuePool: %s", parsed_url.render_as_string(hide_password=True))
        except ModuleNotFoundError as err:
            if "psycopg" in str(err):
                raise ModuleNotFoundError(
                    f"PostgreSQL driver is missing for '{resolved_url}'. "
                    f"Please install 'psycopg2-binary' or 'psycopg' (e.g. pip install psycopg2-binary). Original error: {err}"
                ) from err
            raise

    else:
        # Fallback generic configuration for other dialects (e.g. MySQL, Oracle)
        engine = create_engine(
            resolved_url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            echo=echo,
        )
        logger.info("Configured generic engine for %s: %s", backend_name, resolved_url)

    return engine


def get_engine(
    database_url: Optional[str] = None,
    echo: bool = False,
    reset: bool = False,
) -> Engine:
    """
    Returns the singleton SQLAlchemy Engine, instantiating it if not yet created.

    Args:
        database_url: Optional explicit URL. If provided and different from current engine URL,
                      the previous engine is disposed and a new one is instantiated.
        echo: If True, enables SQLAlchemy statement echo logging.
        reset: If True, disposes existing engine and creates a fresh instance.
    """
    global _cached_engine, _cached_session_factory

    target_url = resolve_database_url(database_url)

    if reset or _cached_engine is None:
        if _cached_engine is not None:
            _cached_engine.dispose()
        _cached_engine = create_sao_engine(target_url, echo=echo)
        _cached_session_factory = None
    elif database_url is not None and str(_cached_engine.url) != target_url:
        _cached_engine.dispose()
        _cached_engine = create_sao_engine(target_url, echo=echo)
        _cached_session_factory = None

    return _cached_engine


def reset_engine() -> None:
    """
    Disposes active database engine pool and resets global singleton caches.
    Essential for teardown in automated test suites and file unlocking on Windows.
    """
    global _cached_engine, _cached_session_factory
    if _cached_engine is not None:
        try:
            _cached_engine.dispose()
        except Exception as exc:  # pragma: no cover
            logger.warning("Error disposing engine: %s", exc)
    _cached_engine = None
    _cached_session_factory = None


# ==============================================================================
# Session Management & Factories
# ==============================================================================
def get_session_factory(engine: Optional[Engine] = None) -> sessionmaker[Session]:
    """
    Returns a SQLAlchemy sessionmaker configured with:
    - expire_on_commit=False: Objects remain fully accessible after commit & session close,
      preventing DetachedInstanceError in Streamlit session state and repository returns.
    - autoflush=False: Prevents premature flushes during complex multi-step entity assembly.
    """
    global _cached_session_factory
    active_engine = engine or get_engine()

    if engine is not None:
        return sessionmaker(bind=active_engine, expire_on_commit=False, autoflush=False)

    if _cached_session_factory is None:
        _cached_session_factory = sessionmaker(
            bind=active_engine,
            expire_on_commit=False,
            autoflush=False,
        )
    return _cached_session_factory


def get_scoped_session(engine: Optional[Engine] = None) -> scoped_session[Session]:
    """
    Returns a thread-local scoped session.
    Useful for multi-threaded CLI tools or worker processes requiring thread-scoped sessions.
    """
    factory = get_session_factory(engine)
    return scoped_session(factory)


def get_db_session() -> Generator[Session, None, None]:
    """
    Generator yielding a standalone session with deterministic closure.
    Suitable as a dependency in FastAPI / Streamlit or manual scripts.
    """
    factory = get_session_factory()
    session = factory()
    try:
        yield session
    finally:
        session.close()


# ==============================================================================
# Post-Commit Hooks
# ==============================================================================
def register_post_commit_hook(db_session: Session, callback: Callable[[], None]) -> None:
    """
    Registers a callback function to be executed strictly AFTER the database
    transaction commits successfully. If the transaction rolls back, the callback
    is discarded and never executed.
    """
    if not hasattr(db_session, "info"):
        return
    callbacks = db_session.info.setdefault("_post_commit_hooks", [])
    callbacks.append(callback)


def execute_post_commit_hooks(db_session: Session) -> None:
    """Executes and clears all registered post-commit hooks on a committed session."""
    if not hasattr(db_session, "info"):
        return
    callbacks = db_session.info.pop("_post_commit_hooks", [])
    for cb in callbacks:
        try:
            cb()
        except Exception as exc:
            logger.error("Error executing post-commit hook %s: %s", cb, exc)


# ==============================================================================
# Atomic Transaction Context Manager
# ==============================================================================
@contextmanager
def db_transaction(
    session_id: Optional[str] = None,
    session: Optional[Session] = None,
    engine: Optional[Engine] = None,
) -> Generator[Session, None, None]:
    """
    Context manager providing atomic commit/rollback semantics with thread/session isolation.

    Behavior:
    1. If an outer `session` is passed:
       - Operates via a nested savepoint (`session.begin_nested()`).
       - If an exception occurs, rolls back to savepoint without breaking outer transaction.
       - Does NOT close the outer session on exit.
    2. If no `session` is passed:
       - Checks out a new Session instance from `SessionLocal`.
       - On normal exit: commits changes atomically (`session.commit()`) and executes post-commit hooks.
       - On unhandled exception: executes `session.rollback()`, drops post-commit hooks, logs error,
         and re-raises the exception.
       - In `finally`: always closes the session (`session.close()`), returning connection to pool.

    Args:
        session_id: Optional campaign or player session identifier for logging/tracing.
        session: Optional existing SQLAlchemy Session to reuse (uses savepoints).
        engine: Optional explicit Engine instance to bind session to.

    Yields:
        Session: The active SQLAlchemy session.
    """
    if session is not None:
        # Nested transaction / savepoint inside existing session
        with session.begin_nested():
            yield session
    else:
        factory = get_session_factory(engine)
        db_session = factory()
        try:
            yield db_session
            db_session.commit()
            execute_post_commit_hooks(db_session)
        except Exception as exc:
            db_session.rollback()
            if hasattr(db_session, "info"):
                db_session.info.pop("_post_commit_hooks", None)
            logger.error(
                "Transaction rolled back due to error (session_id=%s): %s",
                session_id or "unspecified",
                exc,
                exc_info=True,
            )
            raise
        finally:
            db_session.close()


# ==============================================================================
# Schema Management Helpers
# ==============================================================================
def init_db(
    engine: Optional[Engine] = None,
    metadata: Optional[MetaData] = None,
) -> None:
    """
    Initializes database schema by creating all tables defined in models.py.
    Idempotent: tables that already exist will not be overwritten or modified.

    Args:
        engine: Optional Engine instance. If None, uses default singleton engine.
        metadata: Optional MetaData instance. If None, dynamically imports `Base.metadata`
                  from `backend.database.models`.
    """
    active_engine = engine or get_engine()

    if metadata is None:
        from backend.database.models import Base
        metadata = Base.metadata

    metadata.create_all(bind=active_engine)
    logger.info("Schema initialized successfully on engine: %s (tables=%s)", active_engine.url, list(metadata.tables.keys()))


def drop_db(
    engine: Optional[Engine] = None,
    metadata: Optional[MetaData] = None,
) -> None:
    """
    Drops all database tables. Primarily used for automated testing teardown.
    """
    active_engine = engine or get_engine()

    if metadata is None:
        from backend.database.models import Base
        metadata = Base.metadata

    metadata.drop_all(bind=active_engine)
    logger.info("Schema dropped successfully on engine: %s", active_engine.url)


# ==============================================================================
# Diagnostics & Health Check Helpers
# ==============================================================================
def get_sqlite_pragmas(engine: Optional[Engine] = None) -> Dict[str, Any]:
    """
    Queries and returns active SQLite PRAGMA settings for the engine.
    Returns empty dict if engine is not SQLite.
    """
    active_engine = engine or get_engine()
    if active_engine.dialect.name != "sqlite":
        return {}

    pragmas = {}
    with active_engine.connect() as conn:
        for pragma_name in ("journal_mode", "synchronous", "busy_timeout", "foreign_keys"):
            val = conn.execute(text(f"PRAGMA {pragma_name};")).scalar()
            pragmas[pragma_name] = val
    return pragmas


def check_db_health(engine: Optional[Engine] = None) -> Dict[str, Any]:
    """
    Executes a heartbeat query against the database and reports dialect and PRAGMA status.
    """
    active_engine = engine or get_engine()
    health: Dict[str, Any] = {
        "status": "healthy",
        "url": active_engine.url.render_as_string(hide_password=True),
        "dialect": active_engine.dialect.name,
        "pool_class": type(active_engine.pool).__name__,
    }

    try:
        with active_engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
        if active_engine.dialect.name == "sqlite":
            health["pragmas"] = get_sqlite_pragmas(active_engine)
    except Exception as exc:
        health["status"] = "unhealthy"
        health["error"] = str(exc)

    return health
