import itertools

import pytest
import sqlalchemy as sa

from app import create_app
from app.db import engine as db_engine
from app.db import schema
from config import TestConfig

CATEGORY_SEED = [
    ("realestate", "부동산", 1),
    ("stock", "주식", 2),
    ("coin", "코인", 3),
    ("fund", "펀드·ETF", 4),
    ("saving", "예적금·절약", 5),
    ("free", "자유수다", 6),
]

_nick_seq = itertools.count(1)


@pytest.fixture()
def app():
    app = create_app(TestConfig)
    with app.app_context():
        engine = db_engine.get_engine(app)
        schema.metadata.create_all(engine)
        with engine.begin() as conn:
            for slug, name, order in CATEGORY_SEED:
                conn.execute(schema.categories.insert().values(slug=slug, name=name, sort_order=order))
    yield app
    engine.dispose()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def db(app):
    """테스트에서 직접 쿼리할 때 쓰는 커넥션 (자동 커밋)."""
    engine = db_engine.get_engine(app)
    conn = engine.connect()
    yield conn
    conn.close()


@pytest.fixture()
def user_factory(app):
    def make(nickname=None, *, email=None, is_verified=0, is_admin=0,
             provider="email", password_hash=None, points=0, **kw):
        n = next(_nick_seq)
        nickname = nickname or f"유저{n}"
        engine = db_engine.get_engine(app)
        values = dict(
            email=email or f"u{n}_{nickname}@test.local",
            oauth_provider=provider,
            nickname=nickname,
            avatar_no=(n % 12) + 1,
            password_hash=password_hash,
            is_verified=is_verified,
            is_admin=is_admin,
            points=points,
            status="active",
        )
        values.update(kw)
        with engine.begin() as conn:
            res = conn.execute(schema.users.insert().values(**values))
            uid = res.inserted_primary_key[0]
            row = conn.execute(sa.select(schema.users).where(schema.users.c.id == uid)).mappings().one()
        return dict(row)
    return make


@pytest.fixture()
def user(user_factory):
    return user_factory()


@pytest.fixture()
def expert_user(user_factory):
    return user_factory(is_verified=1)


@pytest.fixture()
def admin_user(user_factory):
    return user_factory(is_admin=1)


@pytest.fixture()
def login(client):
    def do_login(u):
        with client.session_transaction() as sess:
            sess["_user_id"] = str(u["id"])
            sess["_fresh"] = True
        return client
    return do_login
