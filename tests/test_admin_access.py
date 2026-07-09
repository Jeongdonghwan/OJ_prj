"""Step 5: 관리자 — 접근 제어 + 퀴즈/투표/캘린더 등록."""
from datetime import date, datetime, timedelta

import sqlalchemy as sa

from app.db import schema

ADMIN_PATHS = ["/admin/", "/admin/quiz", "/admin/poll", "/admin/calendar",
               "/admin/experts", "/admin/reports", "/admin/flagged"]


def test_admin_blocked_for_anonymous(client):
    for path in ADMIN_PATHS:
        assert client.get(path).status_code == 403, path


def test_admin_blocked_for_normal_user(client, login, user):
    login(user)
    for path in ADMIN_PATHS:
        assert client.get(path).status_code == 403, path


def test_admin_pages_ok_for_admin(client, login, admin_user):
    login(admin_user)
    for path in ADMIN_PATHS:
        assert client.get(path).status_code == 200, path


def test_admin_create_quiz(client, login, admin_user, db):
    login(admin_user)
    res = client.post("/admin/quiz", data={
        "quiz_date": (date.today() + timedelta(days=1)).isoformat(),
        "question": "내일의 문제", "choice1": "O", "choice2": "X",
        "answer_no": "1", "explanation": "해설입니다"})
    assert res.status_code == 302
    row = db.execute(sa.select(schema.quizzes)).mappings().one()
    assert row["question"] == "내일의 문제"

    # 같은 날짜 중복 등록 → 에러 메시지
    res = client.post("/admin/quiz", data={
        "quiz_date": (date.today() + timedelta(days=1)).isoformat(),
        "question": "중복", "choice1": "O", "choice2": "X",
        "answer_no": "1", "explanation": "e"})
    assert res.status_code == 200
    assert "이미 퀴즈가 있습니다" in res.get_data(as_text=True)


def test_admin_create_poll_and_visibility(client, login, admin_user, user):
    login(admin_user)
    now = datetime.now()
    res = client.post("/admin/poll", data={
        "question": "이번 주 코스피, 어떻게 될까요?",
        "option_up": "오른다", "option_down": "떨어진다",
        "starts_at": (now - timedelta(hours=1)).isoformat(timespec="minutes"),
        "ends_at": (now + timedelta(hours=23)).isoformat(timespec="minutes")})
    assert res.status_code == 302
    html = client.get("/community").get_data(as_text=True)
    assert "이번 주 코스피" in html
    assert 'class="vtbox' in html


def test_admin_create_calendar_event(client, login, admin_user):
    login(admin_user)
    res = client.post("/admin/calendar", data={
        "event_date": (date.today() + timedelta(days=3)).isoformat(),
        "title": "미 FOMC 금리 결정", "is_hot": "1"})
    assert res.status_code == 302
    html = client.get("/").get_data(as_text=True)
    assert "미 FOMC 금리 결정" in html  # 레일 캘린더 위젯
