"""Step 8: 알림 — 댓글/대댓글 알림, 자기 글 제외, 읽음 처리."""
import sqlalchemy as sa

from app.db import schema


def _notis(db, uid):
    return db.execute(sa.select(schema.notifications).where(
        schema.notifications.c.user_id == uid)).mappings().all()


def test_comment_notifies_author(client, login, user_factory, post_factory, db):
    author, commenter = user_factory("글쓴이"), user_factory("댓글러")
    pid = post_factory(author, title="알림 테스트 글")
    login(commenter)
    client.post(f"/post/{pid}/comment", data={"content": "댓글!"})
    noti = _notis(db, author["id"])
    assert len(noti) == 1
    assert noti[0]["type"] == "comment"
    assert "댓글러" in noti[0]["message"]
    assert noti[0]["is_read"] == 0


def test_self_comment_no_notification(client, login, user, post_factory, db):
    pid = post_factory(user)
    login(user)
    client.post(f"/post/{pid}/comment", data={"content": "혼잣말"})
    assert _notis(db, user["id"]) == []


def test_reply_notifies_parent_commenter(client, login, user_factory, post_factory, db):
    author, c1, c2 = user_factory(), user_factory("먼저댓글"), user_factory("답글러")
    pid = post_factory(author)
    login(c1)
    client.post(f"/post/{pid}/comment", data={"content": "부모 댓글"})
    parent_id = db.execute(sa.select(schema.comments.c.id)).scalar_one()
    login(c2)
    client.post(f"/post/{pid}/comment", data={"content": "답글", "parent_id": parent_id})

    c1_noti = _notis(db, c1["id"])
    assert len(c1_noti) == 1 and c1_noti[0]["type"] == "reply"
    author_noti = _notis(db, author["id"])
    assert len(author_noti) == 2  # 댓글 1 + 답글로 인한 댓글 알림 1


def test_notifications_page_and_mark_read(client, login, user_factory, post_factory, db):
    author, commenter = user_factory(), user_factory()
    pid = post_factory(author, title="읽음 테스트")
    login(commenter)
    client.post(f"/post/{pid}/comment", data={"content": "댓글"})

    login(author)
    html = client.get("/notifications").get_data(as_text=True)
    assert "댓글을 남겼어요" in html
    # 페이지 열람 시 읽음 처리
    unread = db.execute(sa.select(sa.func.count()).where(
        schema.notifications.c.user_id == author["id"],
        schema.notifications.c.is_read == 0)).scalar_one()
    assert unread == 0


def test_notifications_requires_login(client):
    assert client.get("/notifications").status_code == 302
