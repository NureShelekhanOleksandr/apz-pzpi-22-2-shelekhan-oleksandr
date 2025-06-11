from celery import Task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from app.core.config import settings

# Replace "asyncpg" with "psycopg2" for sync connection
sqlalchemy_url = str(settings.SQLALCHEMY_DATABASE_URL).replace("asyncpg", "psycopg2")
engine = create_engine(sqlalchemy_url, pool_recycle=3600, pool_size=10)

class DatabaseTask(Task):
    """Abstract Celery Task that manages the database session lifecycle."""
    abstract = True

    def __init__(self):
        self._session = None
        self._fns_after_return = []

    @property
    def get_session(self):
        if self._session is None:
            self._session = scoped_session(
                sessionmaker(autocommit=False, autoflush=False, bind=engine)
            )
        return self._session

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        if self._session is not None:
            self._session.commit()
            self._session.remove()
        super().after_return(status, retval, task_id, args, kwargs, einfo)

        for _fn, _args in self._fns_after_return:
            _ = _fn(*_args) if _args else _fn()
        self._fns_after_return = []

    def add_fn_after_return(self, fn, *args):
        self._fns_after_return.append((fn, args))
