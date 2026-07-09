"""데일리 퀴즈: 조회/응답/아카이브/포인트."""
from datetime import date

import sqlalchemy as sa
from flask_login import current_user

from app.db import schema
from app.db.engine import get_conn

POINT_CORRECT = 10
POINT_ATTEMPT = 3


def _quiz_row(conn, quiz_date):
    return conn.execute(
        sa.select(schema.quizzes).where(schema.quizzes.c.quiz_date == quiz_date)
    ).mappings().first()


def _choices(row):
    return [c for c in (row["choice1"], row["choice2"], row["choice3"], row["choice4"]) if c]


def _answer_text(row):
    return _choices(row)[row["answer_no"] - 1]


def get_today_quiz_view(today=None):
    """홈/레일 퀴즈 카드용 뷰 모델. 오늘 퀴즈 없으면 None."""
    conn = get_conn()
    today = today or date.today()
    row = _quiz_row(conn, today)
    if not row:
        return None
    attempted, my_choice, is_correct = False, None, None
    if current_user.is_authenticated:
        att = conn.execute(
            sa.select(schema.quiz_attempts).where(
                schema.quiz_attempts.c.user_id == current_user.id,
                schema.quiz_attempts.c.quiz_id == row["id"],
            )
        ).mappings().first()
        if att:
            attempted, my_choice, is_correct = True, att["choice_no"], bool(att["is_correct"])
    return dict(
        id=row["id"], question=row["question"], choices=_choices(row),
        answer_no=row["answer_no"], answer_text=_answer_text(row),
        explanation=row["explanation"],
        attempted=attempted, my_choice=my_choice, is_correct=is_correct,
        history=get_recent_history(exclude_date=today, limit=3),
    )


def get_recent_history(exclude_date=None, limit=3):
    conn = get_conn()
    q = sa.select(schema.quizzes).order_by(schema.quizzes.c.quiz_date.desc()).limit(limit + 1)
    if exclude_date:
        q = sa.select(schema.quizzes).where(schema.quizzes.c.quiz_date < exclude_date) \
            .order_by(schema.quizzes.c.quiz_date.desc()).limit(limit)
    rows = conn.execute(q).mappings().all()[:limit]
    return [dict(question=r["question"], answer_text=_answer_text(r), explanation=r["explanation"])
            for r in rows]


def list_archive():
    conn = get_conn()
    rows = conn.execute(
        sa.select(schema.quizzes).where(schema.quizzes.c.quiz_date <= date.today())
        .order_by(schema.quizzes.c.quiz_date.desc())
    ).mappings().all()
    return [dict(r, answer_text=_answer_text(r)) for r in rows]


def answer_quiz(user_id, quiz_id, choice_no):
    """응답 저장 + 포인트. 이미 응답했으면 ('duplicate', None)."""
    from app.services.point_service import award
    conn = get_conn()
    row = conn.execute(
        sa.select(schema.quizzes).where(schema.quizzes.c.id == quiz_id)
    ).mappings().first()
    if not row:
        return "not_found", None
    is_correct = 1 if choice_no == row["answer_no"] else 0
    try:
        conn.execute(schema.quiz_attempts.insert().values(
            user_id=user_id, quiz_id=quiz_id, choice_no=choice_no, is_correct=is_correct,
        ))
    except sa.exc.IntegrityError:
        conn.rollback()
        return "duplicate", None
    award(user_id, POINT_CORRECT if is_correct else POINT_ATTEMPT, "quiz", conn=conn)
    conn.commit()
    return "ok", dict(is_correct=bool(is_correct), answer_no=row["answer_no"],
                      answer_text=_answer_text(row), explanation=row["explanation"])
