"""Step 9: 네이버 OAuth — state CSRF 검증, 신규/재로그인, 닉네임 충돌."""
import sqlalchemy as sa

from app.db import schema
from tests.fixtures.fake_naver import FakeNaverClient


def _naver_users(db):
    return db.execute(sa.select(schema.users).where(
        schema.users.c.oauth_provider == "naver")).mappings().all()


def _start_and_get_state(client):
    res = client.get("/auth/naver")
    assert res.status_code == 302
    assert "nid.naver.com" in res.headers["Location"]
    with client.session_transaction() as sess:
        state = sess["naver_state"]
    assert state and state in res.headers["Location"]
    return state


def test_start_sets_state_and_redirects(app, client):
    app.extensions["naver_oauth"] = FakeNaverClient()
    _start_and_get_state(client)


def test_callback_with_valid_state_creates_user(app, client, db):
    fake = FakeNaverClient()
    app.extensions["naver_oauth"] = fake
    state = _start_and_get_state(client)
    res = client.get(f"/auth/naver/callback?code=abc&state={state}")
    assert res.status_code == 302
    rows = _naver_users(db)
    assert len(rows) == 1
    assert rows[0]["oauth_id"] == "naver-98765"
    assert rows[0]["avatar_no"] == (rows[0]["id"] % 12) + 1
    assert fake.exchanged == [("abc", state)]
    assert client.get("/my").status_code == 200  # 로그인 상태


def test_callback_rejects_bad_state(app, client, db):
    app.extensions["naver_oauth"] = FakeNaverClient()
    _start_and_get_state(client)
    res = client.get("/auth/naver/callback?code=abc&state=tampered")
    assert res.status_code == 302
    assert "/login" in res.headers["Location"]
    assert _naver_users(db) == []
    assert client.get("/my").status_code == 302  # 로그인 안 됨


def test_callback_rejects_missing_state_session(app, client, db):
    app.extensions["naver_oauth"] = FakeNaverClient()
    res = client.get("/auth/naver/callback?code=abc&state=whatever")
    assert "/login" in res.headers["Location"]
    assert _naver_users(db) == []


def test_state_single_use(app, client, db):
    app.extensions["naver_oauth"] = FakeNaverClient()
    state = _start_and_get_state(client)
    client.get(f"/auth/naver/callback?code=abc&state={state}")
    client.get("/logout")
    # 같은 state 재사용 → 거부
    res = client.get(f"/auth/naver/callback?code=def&state={state}")
    assert "/login" in res.headers["Location"]
    assert client.get("/my").status_code == 302


def test_relogin_reuses_user(app, client, db):
    app.extensions["naver_oauth"] = FakeNaverClient()
    state = _start_and_get_state(client)
    client.get(f"/auth/naver/callback?code=a&state={state}")
    client.get("/logout")
    state = _start_and_get_state(client)
    client.get(f"/auth/naver/callback?code=b&state={state}")
    assert len(_naver_users(db)) == 1


def test_nickname_collision_suffix(app, client, db, user_factory):
    user_factory("네이버유저")
    app.extensions["naver_oauth"] = FakeNaverClient()
    state = _start_and_get_state(client)
    client.get(f"/auth/naver/callback?code=a&state={state}")
    row = _naver_users(db)[0]
    assert row["nickname"].startswith("네이버유저") and row["nickname"] != "네이버유저"


def test_login_page_links_naver(client):
    html = client.get("/login").get_data(as_text=True)
    assert "/auth/naver" in html
    assert "준비 중" not in html
