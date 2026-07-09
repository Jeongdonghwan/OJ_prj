"""DB 엔진/커넥션 관리. 요청당 커넥션 1개 (Flask g), 엔진 풀은 앱 수명 공유."""
import sqlalchemy as sa
from flask import current_app, g
from sqlalchemy.pool import StaticPool

_engines = {}


def create_db_engine(database_url):
    if database_url.startswith("sqlite"):
        # 테스트(인메모리)·개발 편의: 단일 커넥션 공유 + FK 강제
        engine = sa.create_engine(
            database_url,
            poolclass=StaticPool if database_url == "sqlite://" else None,
            connect_args={"check_same_thread": False},
        )

        @sa.event.listens_for(engine, "connect")
        def _fk_on(dbapi_conn, _):
            dbapi_conn.execute("PRAGMA foreign_keys=ON")
    else:
        engine = sa.create_engine(
            database_url, pool_size=10, max_overflow=5, pool_pre_ping=True, pool_recycle=3600,
        )
    return engine


def get_engine(app=None):
    app = app or current_app
    key = id(app._get_current_object() if hasattr(app, "_get_current_object") else app)
    if "db_engine" not in app.extensions:
        app.extensions["db_engine"] = create_db_engine(app.config["DATABASE_URL"])
    return app.extensions["db_engine"]


def get_conn():
    """요청 스코프 커넥션 (자동 커밋은 호출자 책임 — conn.commit())."""
    if "db_conn" not in g:
        g.db_conn = get_engine().connect()
    return g.db_conn


def close_conn(_exc=None):
    conn = g.pop("db_conn", None)
    if conn is not None:
        conn.close()


def init_app(app):
    app.teardown_appcontext(close_conn)
