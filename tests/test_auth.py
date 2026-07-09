"""Step 2: 이메일 가입/로그인, 카카오 OAuth(목), 닉네임 규칙, 로그인 요구."""
from datetime import datetime, timedelta

import sqlalchemy as sa
from werkzeug.security import check_password_hash

from app.db import schema
from tests.fixtures.fake_kakao import FakeKakaoClient


def _get_user_by_email(db, email):
    return db.execute(sa.select(schema.users).where(schema.users.c.email == email)).mappings().first()


def test_email_signup_creates_user(client, db):
    res = client.post("/auth/email/signup", data={
        "email": "new@test.local", "password": "password123", "nickname": "새유저"})
    assert res.status_code == 302
    row = _get_user_by_email(db, "new@test.local")
    assert row is not None
    assert row["oauth_provider"] == "email"
    assert row["nickname"] == "새유저"
    assert row["password_hash"] != "password123"
    assert check_password_hash(row["password_hash"], "password123")
    assert row["avatar_no"] == (row["id"] % 12) + 1


def test_email_signup_duplicate_email(client, db):
    client.post("/auth/email/signup", data={
        "email": "dup@test.local", "password": "password123", "nickname": "유저A"})
    res = client.post("/auth/email/signup", data={
        "email": "dup@test.local", "password": "password123", "nickname": "유저B"})
    assert res.status_code == 200
    assert "이미 가입된 이메일" in res.get_data(as_text=True)


def test_email_signup_duplicate_nickname(client):
    client.post("/auth/email/signup", data={
        "email": "a@test.local", "password": "password123", "nickname": "중복닉"})
    res = client.post("/auth/email/signup", data={
        "email": "b@test.local", "password": "password123", "nickname": "중복닉"})
    assert "이미 사용 중인 닉네임" in res.get_data(as_text=True)


def test_email_login_logout_cycle(client):
    client.post("/auth/email/signup", data={
        "email": "cycle@test.local", "password": "password123", "nickname": "사이클"})
    client.get("/logout")
    assert client.get("/my").status_code == 302  # 로그아웃 상태

    res = client.post("/auth/email/login", data={
        "email": "cycle@test.local", "password": "wrong-password"})
    assert "올바르지 않습니다" in res.get_data(as_text=True)
    assert client.get("/my").status_code == 302

    res = client.post("/auth/email/login", data={
        "email": "cycle@test.local", "password": "password123"})
    assert res.status_code == 302
    assert client.get("/my").status_code == 200

    client.get("/logout")
    assert client.get("/my").status_code == 302


def test_kakao_callback_creates_and_reuses_user(app, client, db):
    fake = FakeKakaoClient()
    app.extensions["kakao_oauth"] = fake

    res = client.get("/auth/kakao/callback?code=abc")
    assert res.status_code == 302
    row = db.execute(sa.select(schema.users).where(
        schema.users.c.oauth_provider == "kakao",
        schema.users.c.oauth_id == "kakao-12345")).mappings().first()
    assert row is not None
    assert row["avatar_no"] == (row["id"] % 12) + 1
    assert client.get("/my").status_code == 200  # 로그인 상태

    client.get("/logout")
    res = client.get("/auth/kakao/callback?code=def")
    assert res.status_code == 302
    count = db.execute(sa.select(sa.func.count()).where(
        schema.users.c.oauth_provider == "kakao")).scalar_one()
    assert count == 1  # 재로그인 — 새 행 없음


def test_kakao_nickname_collision_gets_suffix(app, client, db, user_factory):
    user_factory("카카오유저")  # 선점된 닉네임
    app.extensions["kakao_oauth"] = FakeKakaoClient()
    client.get("/auth/kakao/callback?code=abc")
    row = db.execute(sa.select(schema.users).where(
        schema.users.c.oauth_id == "kakao-12345")).mappings().one()
    assert row["nickname"] != "카카오유저"
    assert row["nickname"].startswith("카카오유저")


def test_kakao_start_redirects_to_authorize(app, client):
    app.extensions["kakao_oauth"] = FakeKakaoClient()
    res = client.get("/auth/kakao")
    assert res.status_code == 302
    assert "kauth.kakao.com" in res.headers["Location"]


def test_nickname_change_30day_rule(app, user_factory):
    from app.services.user_service import change_nickname
    u_old = user_factory("옛닉네임", nickname_changed_at=datetime.now() - timedelta(days=31))
    u_recent = user_factory("최근변경", nickname_changed_at=datetime.now() - timedelta(days=5))
    with app.test_request_context():
        assert change_nickname(u_recent["id"], "새닉1") == "too_soon"
        assert change_nickname(u_old["id"], "새닉2") == "ok"
        assert change_nickname(u_old["id"], "새닉3") == "too_soon"  # 방금 변경했으므로


def test_banned_user_cannot_login(client, user_factory):
    from werkzeug.security import generate_password_hash
    user_factory("정지유저", email="banned@test.local",
                 password_hash=generate_password_hash("password123"), status="banned")
    res = client.post("/auth/email/login", data={
        "email": "banned@test.local", "password": "password123"})
    assert res.status_code == 200  # 로그인 실패 → 폼 재출력
    assert client.get("/my").status_code == 302


def test_login_rate_limit():
    """로그인 시도 분당 10회 초과 → 429 (전용 앱, limiter 활성)."""
    from app import create_app
    from app.db import engine as db_engine
    from app.db import schema as sch
    from config import TestConfig

    class RLConfig(TestConfig):
        RATELIMIT_ENABLED = True

    app = create_app(RLConfig)
    with app.app_context():
        sch.metadata.create_all(db_engine.get_engine(app))
    from app.extensions import limiter
    limiter.reset()
    client = app.test_client()
    codes = []
    for _ in range(11):
        res = client.post("/auth/email/login", data={
            "email": "x@test.local", "password": "whatever123"})
        codes.append(res.status_code)
    assert codes[-1] == 429
    assert 429 not in codes[:10]
    limiter.reset()
