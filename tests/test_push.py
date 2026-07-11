"""Step 11: 푸시 토큰 API + notify() 발송 훅."""
import sqlalchemy as sa

from app.db import schema
from tests.fixtures.fake_push import FakePushSender


def _tokens(db):
    return db.execute(sa.select(schema.push_tokens)).mappings().all()


# ---------- POST /api/push-token ----------

def test_token_requires_login(client):
    res = client.post("/api/push-token", json={"token": "ExpoToken[x]", "platform": "ios"})
    assert res.status_code == 401


def test_token_validation(client, login, user):
    login(user)
    for bad in [{}, {"token": "", "platform": "ios"},
                {"token": "t", "platform": "windows"},
                {"token": "x" * 201, "platform": "ios"}]:
        assert client.post("/api/push-token", json=bad).status_code == 400


def test_token_register_and_reassign(client, login, user_factory, db):
    u1, u2 = user_factory(), user_factory()
    login(u1)
    assert client.post("/api/push-token", json={
        "token": "ExpoToken[abc]", "platform": "android"}).get_json()["ok"]
    rows = _tokens(db)
    assert len(rows) == 1 and rows[0]["user_id"] == u1["id"]

    # 같은 기기에서 다른 계정 로그인 → 토큰 재배정 (행 1개 유지)
    login(u2)
    client.post("/api/push-token", json={"token": "ExpoToken[abc]", "platform": "android"})
    rows = _tokens(db)
    assert len(rows) == 1 and rows[0]["user_id"] == u2["id"]


# ---------- notify() → 푸시 발송 ----------

def _register(client, login, u, token):
    login(u)
    client.post("/api/push-token", json={"token": token, "platform": "ios"})


def test_comment_triggers_push(app, client, login, user_factory, post_factory):
    fake = FakePushSender()
    app.extensions["push_sender"] = fake
    author, commenter = user_factory("글쓴이"), user_factory("댓글러")
    pid = post_factory(author)
    _register(client, login, author, "ExpoToken[author]")

    login(commenter)
    client.post(f"/post/{pid}/comment", data={"content": "댓글!"})

    assert len(fake.sent) == 1
    msg = fake.sent[0]
    assert msg["to"] == "ExpoToken[author]"
    assert msg["title"] == "오재"
    assert "댓글러" in msg["body"]
    assert msg["data"]["url"] == f"/post/{pid}"


def test_no_token_no_push(app, client, login, user_factory, post_factory):
    fake = FakePushSender()
    app.extensions["push_sender"] = fake
    author, commenter = user_factory(), user_factory()
    pid = post_factory(author)
    login(commenter)
    client.post(f"/post/{pid}/comment", data={"content": "댓글"})
    assert fake.sent == []


def test_setting_off_no_push(app, client, login, user_factory, post_factory):
    fake = FakePushSender()
    app.extensions["push_sender"] = fake
    author, commenter = user_factory(), user_factory()
    pid = post_factory(author)
    _register(client, login, author, "ExpoToken[a]")
    client.post("/my/settings", data={"on_reply": "1", "on_column": "1"})  # comment off

    login(commenter)
    client.post(f"/post/{pid}/comment", data={"content": "댓글"})
    assert fake.sent == []


def test_push_failure_does_not_break_comment(app, client, login, user_factory, post_factory, db):
    app.extensions["push_sender"] = FakePushSender(raise_error=True)
    author, commenter = user_factory(), user_factory()
    pid = post_factory(author)
    _register(client, login, author, "ExpoToken[a]")

    login(commenter)
    res = client.post(f"/post/{pid}/comment", data={"content": "그래도 저장돼야 함"})
    assert res.status_code == 302
    count = db.execute(sa.select(sa.func.count()).select_from(schema.comments)).scalar_one()
    assert count == 1
    noti = db.execute(sa.select(sa.func.count()).where(
        schema.notifications.c.user_id == author["id"])).scalar_one()
    assert noti == 1  # 인앱 알림도 정상


def test_dead_token_cleanup(app, client, login, user_factory, post_factory, db):
    fake = FakePushSender(dead_tokens=["ExpoToken[dead]"])
    app.extensions["push_sender"] = fake
    author, commenter = user_factory(), user_factory()
    pid = post_factory(author)
    _register(client, login, author, "ExpoToken[dead]")

    login(commenter)
    client.post(f"/post/{pid}/comment", data={"content": "댓글"})
    assert _tokens(db) == []  # DeviceNotRegistered → 삭제


def test_bridge_snippet_only_for_logged_in(client, login, user):
    assert "__ojaePushToken" not in client.get("/").get_data(as_text=True)
    login(user)
    assert "__ojaePushToken" in client.get("/").get_data(as_text=True)
