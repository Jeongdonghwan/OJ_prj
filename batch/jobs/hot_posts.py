"""인기글 집계 (10분 주기) — 24h 내 글, 조회×1 + 댓글×5 + 좋아요×3 상위 5 → hot_cache.
수익 인증 보드(최근 7일 profit 글 상위/하위)도 함께 캐시.
"""
import json
from datetime import datetime, timedelta

import sqlalchemy as sa

from app.db import schema

HOT_KEY = "hot_posts"
PROFIT_KEY = "profit_board"
HOT_LIMIT = 5
PROFIT_LIMIT = 4


def _upsert(conn, key, payload):
    data = json.dumps(payload, ensure_ascii=False, default=str)
    exists = conn.execute(sa.select(schema.hot_cache.c.cache_key)
                          .where(schema.hot_cache.c.cache_key == key)).first()
    if exists:
        conn.execute(sa.update(schema.hot_cache)
                     .where(schema.hot_cache.c.cache_key == key)
                     .values(payload=data, updated_at=datetime.now()))
    else:
        conn.execute(schema.hot_cache.insert().values(
            cache_key=key, payload=data, updated_at=datetime.now()))


def run(engine, now=None):
    now = now or datetime.now()
    p, u, c = schema.posts, schema.users, schema.categories
    score = (p.c.view_count * 1 + p.c.comment_count * 5 + p.c.like_count * 3).label("score")

    with engine.begin() as conn:
        hot_rows = conn.execute(
            sa.select(p.c.id, p.c.title, p.c.comment_count, score)
            .where(p.c.deleted_at.is_(None),
                   p.c.created_at >= now - timedelta(hours=24))
            .order_by(score.desc(), p.c.id.desc())
            .limit(HOT_LIMIT)
        ).mappings().all()
        _upsert(conn, HOT_KEY, [
            dict(id=r["id"], title=r["title"], comment_count=r["comment_count"])
            for r in hot_rows])

        profit_rows = conn.execute(
            sa.select(p.c.id, p.c.profit_amount, u.c.nickname, c.c.name.label("category"))
            .select_from(p.join(u, p.c.user_id == u.c.id).join(c, p.c.category_id == c.c.id))
            .where(p.c.deleted_at.is_(None),
                   p.c.post_type == "profit",
                   p.c.profit_amount.isnot(None),
                   p.c.created_at >= now - timedelta(days=7))
            .order_by(sa.func.abs(p.c.profit_amount).desc())
            .limit(PROFIT_LIMIT)
        ).mappings().all()
        _upsert(conn, PROFIT_KEY, [
            dict(id=r["id"], nickname=r["nickname"], category=r["category"],
                 amount=r["profit_amount"])
            for r in profit_rows])
    return len(hot_rows)
