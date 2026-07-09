"""재테크 캘린더 — 이번 주(오늘부터 30일 내) 일정."""
from datetime import date, timedelta

import sqlalchemy as sa

from app.db import schema
from app.db.engine import get_conn


def week_events(today=None, limit=5):
    conn = get_conn()
    today = today or date.today()
    rows = conn.execute(
        sa.select(schema.calendar_events)
        .where(schema.calendar_events.c.event_date >= today,
               schema.calendar_events.c.event_date <= today + timedelta(days=30))
        .order_by(schema.calendar_events.c.event_date).limit(limit)
    ).mappings().all()
    return [dict(r) for r in rows]
