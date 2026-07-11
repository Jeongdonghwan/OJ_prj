"""Step 10: 프로필 수정, 회원 탈퇴, 알림 설정."""
import io

import sqlalchemy as sa
from PIL import Image

from app.db import schema


def _png():
    buf = io.BytesIO()
    Image.new("RGB", (300, 300), (100, 150, 200)).save(buf, "PNG")
    buf.seek(0)
    return buf


def _user_row(db, uid):
    return db.execute(sa.select(schema.users).where(schema.users.c.id == uid)).mappings().one()


# ---------- 프로필 수정 ----------

def test_profile_requires_login(client):
    assert client.get("/my/profile").status_code == 302


def test_nickname_change_ok(client, login, user, db):
    login(user)
    res = client.post("/my/profile", data={"nickname": "새로운닉"})
    assert "닉네임이 변경되었습니다" in res.get_data(as_text=True)
    assert _user_row(db, user["id"])["nickname"] == "새로운닉"


def test_nickname_change_too_soon(client, login, user, db):
    login(user)
    client.post("/my/profile", data={"nickname": "첫변경"})
    res = client.post("/my/profile", data={"nickname": "둘째변경"})
    assert "30일에 1번만" in res.get_data(as_text=True)
    assert _user_row(db, user["id"])["nickname"] == "첫변경"


def test_nickname_taken(client, login, user_factory, db):
    user_factory("선점닉")
    me = user_factory()
    login(me)
    res = client.post("/my/profile", data={"nickname": "선점닉"})
    assert "이미 사용 중" in res.get_data(as_text=True)


def test_photo_upload_sets_profile_img(app, client, login, user, db, tmp_path):
    from app.utils import avatar_url
    app.config["UPLOAD_DIR"] = tmp_path
    login(user)
    res = client.post("/my/profile", data={
        "nickname": user["nickname"],
        "photo": (_png(), "me.png"),
    }, content_type="multipart/form-data")
    assert "프로필 사진이 변경되었습니다" in res.get_data(as_text=True)
    row = _user_row(db, user["id"])
    assert row["profile_img"] and row["profile_img"].endswith(".webp")
    assert avatar_url(dict(row)) == row["profile_img"]  # 아바타 대신 사진 사용


def test_photo_bad_file_rejected(app, client, login, user, db, tmp_path):
    app.config["UPLOAD_DIR"] = tmp_path
    login(user)
    res = client.post("/my/profile", data={
        "nickname": user["nickname"],
        "photo": (io.BytesIO(b"not an image"), "x.png"),
    }, content_type="multipart/form-data")
    assert "사진 파일을 확인해주세요" in res.get_data(as_text=True)
    assert _user_row(db, user["id"])["profile_img"] is None


# ---------- 회원 탈퇴 ----------

def test_withdraw_flow(client, login, user_factory, post_factory, db):
    from werkzeug.security import generate_password_hash
    me = user_factory("탈퇴할사람", email="bye@test.local",
                      password_hash=generate_password_hash("password123"))
    pid = post_factory(me, title="남는 글")
    login(me)
    res = client.post("/my/withdraw")
    assert res.status_code == 302

    row = _user_row(db, me["id"])
    assert row["status"] == "deleted"
    assert row["nickname"] == f"탈퇴회원{me['id']}"
    assert row["email"] is None and row["password_hash"] is None

    # 즉시 로그아웃 + 재로그인 불가
    assert client.get("/my").status_code == 302
    res = client.post("/auth/email/login", data={
        "email": "bye@test.local", "password": "password123"})
    assert client.get("/my").status_code == 302

    # 글은 남고 탈퇴회원으로 표시
    html = client.get(f"/post/{pid}").get_data(as_text=True)
    assert "남는 글" in html
    assert f"탈퇴회원{me['id']}" in html

    # 닉네임은 재사용 가능
    res = client.post("/auth/email/signup", data={
        "email": "new@test.local", "password": "password123", "nickname": "탈퇴할사람"})
    assert res.status_code == 302


def test_withdraw_confirm_page(client, login, user):
    login(user)
    html = client.get("/my/withdraw").get_data(as_text=True)
    assert "정말 탈퇴하시겠어요" in html
    assert "탈퇴회원" in html


# ---------- 알림 설정 ----------

def test_settings_default_all_on(client, login, user):
    login(user)
    html = client.get("/my/settings").get_data(as_text=True)
    assert html.count("checked") == 3


def test_settings_save_and_render(client, login, user, db):
    login(user)
    client.post("/my/settings", data={"on_comment": "1"})  # reply/column off
    html = client.get("/my/settings").get_data(as_text=True)
    assert html.count("checked") == 1
    row = db.execute(sa.select(schema.notification_settings).where(
        schema.notification_settings.c.user_id == user["id"])).mappings().one()
    assert (row["on_comment"], row["on_reply"], row["on_column"]) == (1, 0, 0)


def test_comment_notification_respects_setting(client, login, user_factory, post_factory, db):
    author, commenter = user_factory(), user_factory()
    pid = post_factory(author)
    login(author)
    client.post("/my/settings", data={"on_reply": "1", "on_column": "1"})  # comment off

    login(commenter)
    client.post(f"/post/{pid}/comment", data={"content": "댓글"})
    noti = db.execute(sa.select(schema.notifications).where(
        schema.notifications.c.user_id == author["id"])).mappings().all()
    assert noti == []  # 댓글 알림 꺼짐

    # 답글 알림은 살아 있음
    login(author)
    client.post(f"/post/{pid}/comment", data={"content": "작성자 댓글"})
    my_comment = db.execute(sa.select(schema.comments.c.id).where(
        schema.comments.c.user_id == author["id"])).scalar_one()
    login(commenter)
    client.post(f"/post/{pid}/comment", data={"content": "답글", "parent_id": my_comment})
    noti = db.execute(sa.select(schema.notifications).where(
        schema.notifications.c.user_id == author["id"])).mappings().all()
    assert len(noti) == 1
    assert noti[0]["type"] == "reply"


def test_column_notification_respects_setting(client, login, user_factory, expert_user, db):
    fan = user_factory()
    login(fan)
    client.post("/api/follow", json={"user_id": expert_user["id"]})
    client.post("/my/settings", data={"on_comment": "1", "on_reply": "1"})  # column off

    login(expert_user)
    client.post("/write", data={
        "category": "fund", "post_type": "normal", "column_tag": "절세",
        "title": "칼럼", "content": "본문"})
    noti = db.execute(sa.select(schema.notifications).where(
        schema.notifications.c.user_id == fan["id"])).mappings().all()
    assert noti == []
