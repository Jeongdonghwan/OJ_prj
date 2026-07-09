"""댓글: 1뎁스 대댓글, soft delete, comment_count 동기화, 알림 연동."""
from datetime import datetime

import sqlalchemy as sa

from app.db import schema
from app.db.engine import get_conn

_cm, _u, _p = schema.comments, schema.users, schema.posts


def list_comments(post_id):
    """부모 → 그 아래 대댓글 순서로 정렬해 반환."""
    conn = get_conn()
    rows = conn.execute(
        sa.select(_cm, _u.c.nickname, _u.c.avatar_no, _u.c.profile_img, _u.c.is_verified)
        .select_from(_cm.join(_u, _cm.c.user_id == _u.c.id))
        .where(_cm.c.post_id == post_id)
        .order_by(_cm.c.id)
    ).mappings().all()
    parents = [dict(r) for r in rows if not r["parent_id"]]
    children = {}
    for r in rows:
        if r["parent_id"]:
            children.setdefault(r["parent_id"], []).append(dict(r))
    ordered = []
    for p in parents:
        # 대댓글 없이 삭제된 댓글은 표시 생략
        kids = children.get(p["id"], [])
        if p["deleted_at"] and not kids:
            continue
        ordered.append(p)
        ordered.extend(kids)
    return ordered


def add_comment(post_id, user_id, content, parent_id=None):
    """반환: (status, comment_id). 대댓글의 대댓글은 'bad_parent'."""
    from app.services.notification_service import notify
    conn = get_conn()
    post = conn.execute(sa.select(_p.c.id, _p.c.user_id, _p.c.title).where(
        _p.c.id == post_id, _p.c.deleted_at.is_(None))).mappings().first()
    if not post:
        return "not_found", None
    parent = None
    if parent_id:
        parent = conn.execute(sa.select(_cm).where(
            _cm.c.id == parent_id, _cm.c.post_id == post_id)).mappings().first()
        if not parent:
            return "bad_parent", None
        if parent["parent_id"] is not None:  # 1뎁스 제한
            return "bad_parent", None
    res = conn.execute(_cm.insert().values(
        post_id=post_id, user_id=user_id, parent_id=parent_id, content=content))
    conn.execute(sa.update(_p).where(_p.c.id == post_id)
                 .values(comment_count=_p.c.comment_count + 1))
    cid = res.inserted_primary_key[0]
    nickname = conn.execute(sa.select(_u.c.nickname).where(_u.c.id == user_id)).scalar_one()
    if parent and parent["user_id"] != user_id:
        notify(parent["user_id"], "reply", post_id,
               f"{nickname}님이 회원님의 댓글에 답글을 남겼어요", conn=conn, commit=False)
    if post["user_id"] != user_id and (not parent or parent["user_id"] != post["user_id"]):
        notify(post["user_id"], "comment", post_id,
               f"{nickname}님이 회원님의 글에 댓글을 남겼어요: {post['title'][:20]}", conn=conn, commit=False)
    conn.commit()
    return "ok", cid


def delete_comment(comment_id, user_id, is_admin=False):
    conn = get_conn()
    row = conn.execute(sa.select(_cm).where(
        _cm.c.id == comment_id, _cm.c.deleted_at.is_(None))).mappings().first()
    if not row:
        return "not_found"
    if row["user_id"] != user_id and not is_admin:
        return "forbidden"
    conn.execute(sa.update(_cm).where(_cm.c.id == comment_id)
                 .values(deleted_at=datetime.now()))
    conn.execute(sa.update(_p).where(_p.c.id == row["post_id"])
                 .values(comment_count=_p.c.comment_count - 1))
    conn.commit()
    return "ok"
