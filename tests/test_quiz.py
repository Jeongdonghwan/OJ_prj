"""Step 5: 데일리 퀴즈 — 하루 1회, 포인트, 홈 카드, 아카이브 SSR."""
from datetime import date, timedelta

import pytest
import sqlalchemy as sa

from app.db import engine as db_engine
from app.db import schema


@pytest.fixture()
def quiz_factory(app):
    def make(quiz_date=None, answer_no=2, question="예금자보호 한도는 얼마까지일까요?",
             explanation="2025년 9월부터 1억원으로 상향됐어요.",
             choice1="5,000만원", choice2="1억원", **kw):
        engine = db_engine.get_engine(app)
        with engine.begin() as conn:
            res = conn.execute(schema.quizzes.insert().values(
                quiz_date=quiz_date or date.today(), question=question,
                choice1=choice1, choice2=choice2, answer_no=answer_no,
                explanation=explanation, **kw))
            return res.inserted_primary_key[0]
    return make


def _points(db, user_id):
    return db.execute(sa.select(schema.users.c.points)
                      .where(schema.users.c.id == user_id)).scalar_one()


def test_home_shows_today_quiz(client, quiz_factory):
    quiz_factory()
    html = client.get("/").get_data(as_text=True)
    assert 'class="qzbox' in html
    assert "예금자보호 한도" in html
    assert "1억원" in html


def test_correct_answer_awards_10(client, login, user, quiz_factory, db):
    qid = quiz_factory(answer_no=2)
    login(user)
    res = client.post("/api/quiz/answer", json={"quiz_id": qid, "choice_no": 2})
    data = res.get_json()
    assert data["is_correct"] is True
    assert "1억원" in data["answer_text"]
    assert _points(db, user["id"]) >= 10  # 출석 +2 포함 가능
    log = db.execute(sa.select(schema.point_logs).where(
        schema.point_logs.c.reason == "quiz")).mappings().one()
    assert log["amount"] == 10


def test_wrong_answer_awards_3(client, login, user, quiz_factory, db):
    qid = quiz_factory(answer_no=2)
    login(user)
    data = client.post("/api/quiz/answer", json={"quiz_id": qid, "choice_no": 1}).get_json()
    assert data["is_correct"] is False
    log = db.execute(sa.select(schema.point_logs).where(
        schema.point_logs.c.reason == "quiz")).mappings().one()
    assert log["amount"] == 3


def test_second_attempt_409_and_no_double_points(client, login, user, quiz_factory, db):
    qid = quiz_factory(answer_no=2)
    login(user)
    client.post("/api/quiz/answer", json={"quiz_id": qid, "choice_no": 2})
    before = _points(db, user["id"])
    res = client.post("/api/quiz/answer", json={"quiz_id": qid, "choice_no": 1})
    assert res.status_code == 409
    assert _points(db, user["id"]) == before
    count = db.execute(sa.select(sa.func.count()).select_from(schema.quiz_attempts)).scalar_one()
    assert count == 1


def test_anonymous_answer_401(client, quiz_factory):
    qid = quiz_factory()
    res = client.post("/api/quiz/answer", json={"quiz_id": qid, "choice_no": 1})
    assert res.status_code == 401


def test_answered_state_rendered_on_home(client, login, user, quiz_factory):
    qid = quiz_factory(answer_no=2)
    login(user)
    client.post("/api/quiz/answer", json={"quiz_id": qid, "choice_no": 2})
    html = client.get("/").get_data(as_text=True)
    assert "qzbox done" in html
    assert "정답!" in html


def test_recent_history_inline(client, quiz_factory):
    for i in range(1, 5):
        quiz_factory(quiz_date=date.today() - timedelta(days=i),
                     question=f"지난 문제 {i}")
    quiz_factory(question="오늘의 문제")
    html = client.get("/").get_data(as_text=True)
    for i in (1, 2, 3):  # 최근 3개만 인라인
        assert f"지난 문제 {i}" in html
    assert "지난 문제 4" not in html


def test_archive_page_ssr(client, quiz_factory):
    quiz_factory(quiz_date=date.today() - timedelta(days=1),
                 question="아카이브 문제", explanation="아카이브 해설")
    html = client.get("/quiz/archive").get_data(as_text=True)
    assert "아카이브 문제" in html
    assert "아카이브 해설" in html
    # 미래 예약 퀴즈는 노출 금지
    quiz_factory(quiz_date=date.today() + timedelta(days=1), question="내일 문제")
    html = client.get("/quiz/archive").get_data(as_text=True)
    assert "내일 문제" not in html
