"""Step 3: rate limit — 글 2/분, 댓글 5/분 (limiter 활성 전용 앱)."""
import itertools

import pytest
import sqlalchemy as sa

from app import create_app
from app.db import engine as db_engine
from app.db import schema
from config import TestConfig
from tests.conftest import CATEGORY_SEED

_seq = itertools.count(1000)


class RLConfig(TestConfig):
    RATELIMIT_ENABLED = True


@pytest.fixture()
def rl_app():
    app = create_app(RLConfig)
    with app.app_context():
        engine = db_engine.get_engine(app)
        schema.metadata.create_all(engine)
        with engine.begin() as conn:
            for slug, name, order in CATEGORY_SEED:
                conn.execute(schema.categories.insert().values(slug=slug, name=name, sort_order=order))
    from app.extensions import limiter
    limiter.reset()
    yield app
    limiter.reset()
    engine.dispose()


@pytest.fixture()
def rl_login(rl_app):
    def make_and_login(client):
        n = next(_seq)
        engine = db_engine.get_engine(rl_app)
        with engine.begin() as conn:
            res = conn.execute(schema.users.insert().values(
                email=f"rl{n}@test.local", oauth_provider="email",
                nickname=f"율격유저{n}", avatar_no=1, status="active"))
            uid = res.inserted_primary_key[0]
        with client.session_transaction() as sess:
            sess["_user_id"] = str(uid)
            sess["_fresh"] = True
        return uid
    return make_and_login


def test_post_write_rate_limit_2_per_minute(rl_app, rl_login):
    client = rl_app.test_client()
    rl_login(client)
    codes = []
    for i in range(3):
        res = client.post("/write", data={
            "category": "free", "post_type": "normal",
            "title": f"연속 글 {i}", "content": "내용"})
        codes.append(res.status_code)
    assert codes[0] == 302 and codes[1] == 302
    assert codes[2] == 429


def test_write_get_not_rate_limited(rl_app, rl_login):
    client = rl_app.test_client()
    rl_login(client)
    for _ in range(5):
        assert client.get("/write").status_code == 200


def test_comment_rate_limit_5_per_minute(rl_app, rl_login):
    client = rl_app.test_client()
    uid = rl_login(client)
    engine = db_engine.get_engine(rl_app)
    with engine.begin() as conn:
        cat_id = conn.execute(sa.select(schema.categories.c.id).limit(1)).scalar_one()
        post_id = conn.execute(schema.posts.insert().values(
            user_id=uid, category_id=cat_id, post_type="normal",
            title="댓글용", content="c", view_count=0, like_count=0,
            comment_count=0, is_flagged=0)).inserted_primary_key[0]
    codes = [client.post(f"/post/{post_id}/comment",
                         data={"content": f"댓글 {i}"}).status_code for i in range(6)]
    assert codes[:5] == [302] * 5
    assert codes[5] == 429
