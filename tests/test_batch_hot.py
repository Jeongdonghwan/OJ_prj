"""Step 4: hot_posts 배치 — 가중치(조회×1+댓글×5+좋아요×3), 24h 윈도, 캐시 기록."""
import json
from datetime import datetime, timedelta

import sqlalchemy as sa

from app.db import engine as db_engine
from app.db import schema
from batch.jobs import hot_posts


def _cache(db, key):
    row = db.execute(sa.select(schema.hot_cache.c.payload)
                     .where(schema.hot_cache.c.cache_key == key)).first()
    return json.loads(row[0]) if row else None


def test_weight_ordering(app, db, user, post_factory):
    now = datetime.now()
    # score: A=10 (조회10), B=25 (댓글5), C=9 (좋아요3)
    a = post_factory(user, title="A조회왕", view_count=10)
    b = post_factory(user, title="B댓글왕", comment_count=5)
    c = post_factory(user, title="C좋아요", like_count=3)
    engine = db_engine.get_engine(app)
    hot_posts.run(engine, now=now)
    cached = _cache(db, "hot_posts")
    assert [x["title"] for x in cached] == ["B댓글왕", "A조회왕", "C좋아요"]


def test_24h_window_and_deleted_excluded(app, db, user, post_factory):
    now = datetime.now()
    post_factory(user, title="오래된 글", view_count=999,
                 created_at=now - timedelta(hours=25))
    post_factory(user, title="삭제된 글", view_count=999, deleted_at=now)
    post_factory(user, title="살아있는 글", view_count=5)
    hot_posts.run(db_engine.get_engine(app), now=now)
    titles = [x["title"] for x in _cache(db, "hot_posts")]
    assert titles == ["살아있는 글"]


def test_top5_limit_and_home_renders_from_cache(app, client, db, user, post_factory):
    for i in range(7):
        post_factory(user, title=f"인기글{i}", view_count=100 - i)
    hot_posts.run(db_engine.get_engine(app))
    cached = _cache(db, "hot_posts")
    assert len(cached) == 5

    html = client.get("/").get_data(as_text=True)
    assert "지금 뜨는 글" in html
    for item in cached:
        assert item["title"] in html
    assert "인기글5" not in html  # 6위는 미노출


def test_profit_board_cache(app, db, user_factory, post_factory):
    u1 = user_factory("티끌모아")
    u2 = user_factory("단타그만")
    post_factory(u1, category="saving", post_type="profit",
                 title="적금", profit_amount=1847200)
    post_factory(u2, category="stock", post_type="profit",
                 title="손실", profit_amount=-2108500)
    post_factory(u1, title="일반글", view_count=10)  # profit 아님 → 제외
    hot_posts.run(db_engine.get_engine(app))
    board = _cache(db, "profit_board")
    assert len(board) == 2
    assert {b["nickname"] for b in board} == {"티끌모아", "단타그만"}
    amounts = {b["nickname"]: b["amount"] for b in board}
    assert amounts["단타그만"] == -2108500


def test_home_empty_state_safe(client):
    """데이터가 하나도 없어도 홈은 200 + 섹션 미노출."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "지금 뜨는 글" not in html
