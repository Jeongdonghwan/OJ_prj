import sqlalchemy as sa
from sqlalchemy.schema import CreateTable

from app.db import schema


def test_app_factory_builds(app):
    assert app.testing
    assert app.config["SECRET_KEY"]
    assert app.config["DATABASE_URL"] == "sqlite://"


def test_health(client):
    assert client.get("/health").status_code == 200


def test_schema_creates_on_sqlite(db):
    names = set(schema.metadata.tables.keys())
    assert {"users", "posts", "comments", "quizzes", "polls", "news_articles",
            "hot_cache", "daily_briefings"} <= names
    # 실제 생성 확인
    row = db.execute(sa.text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
    created = {r[0] for r in row}
    assert names <= created


def test_schema_mysql_dialect_parity():
    """MariaDB 방언 컴파일 시 ENUM/utf8mb4가 유지되는지 (방언 드리프트 감지)."""
    from sqlalchemy.dialects import mysql
    ddl = str(CreateTable(schema.users).compile(dialect=mysql.dialect()))
    assert "ENUM('kakao','naver','email')" in ddl
    assert "CHARSET=utf8mb4" in ddl
    ddl_posts = str(CreateTable(schema.posts).compile(dialect=mysql.dialect()))
    assert "ENUM('normal','profit','trade','question')" in ddl_posts
    assert "profit_amount BIGINT" in ddl_posts
