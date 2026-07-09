"""투표: 활성 투표 조회/응답/비율."""
from datetime import datetime

import sqlalchemy as sa
from flask_login import current_user

from app.db import schema
from app.db.engine import get_conn


def get_active_poll(now=None, conn=None):
    conn = conn or get_conn()
    now = now or datetime.now()
    return conn.execute(
        sa.select(schema.polls).where(
            schema.polls.c.is_active == 1,
            schema.polls.c.starts_at <= now,
            schema.polls.c.ends_at >= now,
        ).order_by(schema.polls.c.id.desc())
    ).mappings().first()


def _counts(conn, poll_id):
    rows = conn.execute(
        sa.select(schema.poll_votes.c.side, sa.func.count())
        .where(schema.poll_votes.c.poll_id == poll_id)
        .group_by(schema.poll_votes.c.side)
    ).all()
    up = sum(c for s, c in rows if s == "up")
    down = sum(c for s, c in rows if s == "down")
    return up, down


def _pcts(up, down):
    total = up + down
    if total == 0:
        return 50, 50, 0
    up_pct = round(up * 100 / total)
    return up_pct, 100 - up_pct, total


def get_active_poll_view(now=None):
    conn = get_conn()
    row = get_active_poll(now=now, conn=conn)
    if not row:
        return None
    up, down = _counts(conn, row["id"])
    up_pct, down_pct, total = _pcts(up, down)
    voted, my_side = False, None
    if current_user.is_authenticated:
        v = conn.execute(
            sa.select(schema.poll_votes).where(
                schema.poll_votes.c.user_id == current_user.id,
                schema.poll_votes.c.poll_id == row["id"],
            )
        ).mappings().first()
        if v:
            voted, my_side = True, v["side"]
    return dict(id=row["id"], question=row["question"],
                option_up=row["option_up"], option_down=row["option_down"],
                voted=voted, my_side=my_side,
                up_pct=up_pct, down_pct=down_pct, total=total)


def vote(user_id, poll_id, side):
    """중복 투표는 'duplicate' 반환 (첫 투표 유지). 성공 시 +3P."""
    from app.services.point_service import award, VOTE_POINT
    conn = get_conn()
    poll = conn.execute(
        sa.select(schema.polls).where(schema.polls.c.id == poll_id)
    ).mappings().first()
    now = datetime.now()
    if not poll or not poll["is_active"] or not (poll["starts_at"] <= now <= poll["ends_at"]):
        return "not_found", None
    if side not in ("up", "down"):
        return "bad_request", None
    try:
        conn.execute(schema.poll_votes.insert().values(
            user_id=user_id, poll_id=poll_id, side=side))
    except sa.exc.IntegrityError:
        conn.rollback()
        return "duplicate", None
    award(user_id, VOTE_POINT, "vote", conn=conn)
    conn.commit()
    up, down = _counts(conn, poll_id)
    up_pct, down_pct, total = _pcts(up, down)
    return "ok", dict(up_pct=up_pct, down_pct=down_pct, total=total)
