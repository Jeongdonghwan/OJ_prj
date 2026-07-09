"""투표 마감 (00:00) — 종료 시각 지난 투표 비활성화 + 익일 퀴즈 존재 확인."""
from datetime import datetime, timedelta

import sqlalchemy as sa

from app.db import schema


def run(engine, now=None):
    now = now or datetime.now()
    with engine.begin() as conn:
        result = conn.execute(
            sa.update(schema.polls)
            .where(schema.polls.c.is_active == 1, schema.polls.c.ends_at < now)
            .values(is_active=0))
        closed = result.rowcount

        tomorrow = (now + timedelta(days=1)).date()
        quiz_ready = conn.execute(
            sa.select(schema.quizzes.c.id)
            .where(schema.quizzes.c.quiz_date == tomorrow)).first() is not None
    if not quiz_ready:
        print(f"[close_poll] 경고: {tomorrow} 퀴즈가 등록되지 않았습니다 — 관리자 확인 필요")
    return dict(closed=closed, quiz_ready=quiz_ready)
