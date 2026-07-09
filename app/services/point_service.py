"""포인트 적립: point_logs 기록 + users.points 캐시 갱신 (단일 트랜잭션)."""
from datetime import date, datetime

import sqlalchemy as sa

from app.db import schema
from app.db.engine import get_conn

ATTENDANCE_POINT = 2
VOTE_POINT = 3


def award(user_id, amount, reason, conn=None, commit=False):
    """호출자가 conn/commit을 관리하면 같은 트랜잭션에 묶인다."""
    own = conn is None
    conn = conn or get_conn()
    conn.execute(schema.point_logs.insert().values(
        user_id=user_id, amount=amount, reason=reason))
    conn.execute(sa.update(schema.users).where(schema.users.c.id == user_id)
                 .values(points=schema.users.c.points + amount))
    if own or commit:
        conn.commit()


def total_points(user_id, conn=None):
    conn = conn or get_conn()
    return conn.execute(
        sa.select(sa.func.coalesce(sa.func.sum(schema.point_logs.c.amount), 0))
        .where(schema.point_logs.c.user_id == user_id)
    ).scalar_one()


def award_attendance(user_id):
    """오늘 첫 접속 시 +2P. 이미 적립했으면 no-op."""
    conn = get_conn()
    today = date.today()
    exists = conn.execute(
        sa.select(schema.point_logs.c.id).where(
            schema.point_logs.c.user_id == user_id,
            schema.point_logs.c.reason == "attendance",
            schema.point_logs.c.created_at >= datetime(today.year, today.month, today.day),
        ).limit(1)
    ).first()
    if exists:
        return False
    award(user_id, ATTENDANCE_POINT, "attendance", conn=conn, commit=True)
    return True
