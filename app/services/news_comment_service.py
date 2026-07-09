"""뉴스 댓글 (news_comments 테이블, 게시글 comments와 분리)."""
from datetime import datetime

import sqlalchemy as sa

from app.db import schema
from app.db.engine import get_conn

_nc, _u, _na = schema.news_comments, schema.users, schema.news_articles


def list_news_comments(news_id):
    conn = get_conn()
    rows = conn.execute(
        sa.select(_nc, _u.c.nickname, _u.c.avatar_no, _u.c.profile_img, _u.c.is_verified)
        .select_from(_nc.join(_u, _nc.c.user_id == _u.c.id))
        .where(_nc.c.news_id == news_id, _nc.c.deleted_at.is_(None))
        .order_by(_nc.c.id)
    ).mappings().all()
    return [dict(r) for r in rows]


def add_news_comment(news_id, user_id, content):
    conn = get_conn()
    exists = conn.execute(sa.select(_na.c.id).where(_na.c.id == news_id)).first()
    if not exists:
        return "not_found", None
    res = conn.execute(_nc.insert().values(news_id=news_id, user_id=user_id, content=content))
    conn.execute(sa.update(_na).where(_na.c.id == news_id)
                 .values(comment_count=_na.c.comment_count + 1))
    conn.commit()
    return "ok", res.inserted_primary_key[0]


def delete_news_comment(comment_id, user_id, is_admin=False):
    conn = get_conn()
    row = conn.execute(sa.select(_nc).where(
        _nc.c.id == comment_id, _nc.c.deleted_at.is_(None))).mappings().first()
    if not row:
        return "not_found"
    if row["user_id"] != user_id and not is_admin:
        return "forbidden"
    conn.execute(sa.update(_nc).where(_nc.c.id == comment_id)
                 .values(deleted_at=datetime.now()))
    conn.execute(sa.update(_na).where(_na.c.id == row["news_id"])
                 .values(comment_count=_na.c.comment_count - 1))
    conn.commit()
    return "ok"
