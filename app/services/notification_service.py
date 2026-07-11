"""알림 생성/조회/읽음 처리."""
import sqlalchemy as sa

from app.db import schema
from app.db.engine import get_conn

_n = schema.notifications


def notify(user_id, type_, ref_id, message, conn=None, commit=True):
    from app.services.settings_service import is_enabled
    own = conn is None
    conn = conn or get_conn()
    if not is_enabled(user_id, type_, conn):
        return
    conn.execute(_n.insert().values(
        user_id=user_id, type=type_, ref_id=ref_id, message=message, is_read=0))
    if own and commit:
        conn.commit()


def list_notifications(user_id, limit=50):
    conn = get_conn()
    rows = conn.execute(
        sa.select(_n).where(_n.c.user_id == user_id)
        .order_by(_n.c.id.desc()).limit(limit)
    ).mappings().all()
    items = []
    for r in rows:
        d = dict(r)
        if d["type"] in ("comment", "reply", "column"):
            d["link"] = f"/post/{d['ref_id']}"
        else:
            d["link"] = "#"
        items.append(d)
    return items


def unread_count(user_id):
    conn = get_conn()
    return conn.execute(
        sa.select(sa.func.count()).where(_n.c.user_id == user_id, _n.c.is_read == 0)
    ).scalar_one()


def mark_all_read(user_id):
    conn = get_conn()
    conn.execute(sa.update(_n).where(_n.c.user_id == user_id, _n.c.is_read == 0)
                 .values(is_read=1))
    conn.commit()
