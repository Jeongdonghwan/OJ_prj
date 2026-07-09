"""도움됐어요(토글)·스크랩·팔로우 + 조회수 세션 중복 차단."""
import sqlalchemy as sa
from flask import session

from app.db import schema
from app.db.engine import get_conn

VIEWED_CAP = 50  # 세션 '본 글' 목록 상한 (§11)


def toggle_like(user_id, target_type, target_id):
    conn = get_conn()
    r = schema.reactions
    where = (r.c.user_id == user_id) & (r.c.target_type == target_type) & (r.c.target_id == target_id)
    existing = conn.execute(sa.select(r.c.user_id).where(where)).first()
    delta, on = (-1, False) if existing else (1, True)
    if existing:
        conn.execute(sa.delete(r).where(where))
    else:
        conn.execute(r.insert().values(user_id=user_id, target_type=target_type, target_id=target_id))
    count = None
    if target_type == "post":
        conn.execute(sa.update(schema.posts).where(schema.posts.c.id == target_id)
                     .values(like_count=schema.posts.c.like_count + delta))
        count = conn.execute(sa.select(schema.posts.c.like_count)
                             .where(schema.posts.c.id == target_id)).scalar()
    conn.commit()
    return on, count or 0


def has_liked(user_id, target_type, target_id, conn=None):
    conn = conn or get_conn()
    r = schema.reactions
    return conn.execute(sa.select(r.c.user_id).where(
        (r.c.user_id == user_id) & (r.c.target_type == target_type) & (r.c.target_id == target_id)
    )).first() is not None


def toggle_scrap(user_id, post_id):
    conn = get_conn()
    s = schema.scraps
    where = (s.c.user_id == user_id) & (s.c.post_id == post_id)
    existing = conn.execute(sa.select(s.c.user_id).where(where)).first()
    if existing:
        conn.execute(sa.delete(s).where(where))
        on = False
    else:
        conn.execute(s.insert().values(user_id=user_id, post_id=post_id))
        on = True
    conn.commit()
    return on


def has_scrapped(user_id, post_id, conn=None):
    conn = conn or get_conn()
    s = schema.scraps
    return conn.execute(sa.select(s.c.user_id).where(
        (s.c.user_id == user_id) & (s.c.post_id == post_id))).first() is not None


def toggle_follow(follower_id, followee_id):
    if follower_id == followee_id:
        return "self", None
    conn = get_conn()
    f = schema.follows
    where = (f.c.follower_id == follower_id) & (f.c.followee_id == followee_id)
    existing = conn.execute(sa.select(f.c.follower_id).where(where)).first()
    if existing:
        conn.execute(sa.delete(f).where(where))
        on = False
    else:
        conn.execute(f.insert().values(follower_id=follower_id, followee_id=followee_id))
        on = True
    conn.commit()
    return "ok", on


def is_following(follower_id, followee_id, conn=None):
    conn = conn or get_conn()
    f = schema.follows
    return conn.execute(sa.select(f.c.follower_id).where(
        (f.c.follower_id == follower_id) & (f.c.followee_id == followee_id))).first() is not None


def count_view(post_id):
    """세션당 1회만 조회수 증가. 증가했으면 True."""
    viewed = session.get("viewed_posts", [])
    if post_id in viewed:
        return False
    conn = get_conn()
    conn.execute(sa.update(schema.posts).where(schema.posts.c.id == post_id)
                 .values(view_count=schema.posts.c.view_count + 1))
    conn.commit()
    viewed.append(post_id)
    session["viewed_posts"] = viewed[-VIEWED_CAP:]
    return True
