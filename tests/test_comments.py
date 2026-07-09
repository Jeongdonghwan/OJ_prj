"""Step 3: 댓글/1뎁스 대댓글, soft delete, comment_count 동기화."""
import sqlalchemy as sa

from app.db import schema


def _count(db, post_id):
    return db.execute(sa.select(schema.posts.c.comment_count)
                      .where(schema.posts.c.id == post_id)).scalar_one()


def test_add_comment_and_count(client, login, user, post_factory, db):
    post_id = post_factory(user)
    login(user)
    res = client.post(f"/post/{post_id}/comment", data={"content": "첫 댓글입니다"})
    assert res.status_code == 302
    assert _count(db, post_id) == 1
    assert "첫 댓글입니다" in client.get(f"/post/{post_id}").get_data(as_text=True)


def test_reply_one_depth_only(client, login, user, post_factory, db):
    post_id = post_factory(user)
    login(user)
    client.post(f"/post/{post_id}/comment", data={"content": "부모 댓글"})
    parent_id = db.execute(sa.select(schema.comments.c.id)).scalar_one()

    res = client.post(f"/post/{post_id}/comment",
                      data={"content": "대댓글", "parent_id": parent_id})
    assert res.status_code == 302
    reply_id = db.execute(sa.select(schema.comments.c.id).where(
        schema.comments.c.parent_id == parent_id)).scalar_one()

    # 대댓글의 대댓글 → 400
    res = client.post(f"/post/{post_id}/comment",
                      data={"content": "2뎁스 시도", "parent_id": reply_id})
    assert res.status_code == 400
    assert _count(db, post_id) == 2


def test_comment_requires_login(client, user, post_factory):
    post_id = post_factory(user)
    res = client.post(f"/post/{post_id}/comment", data={"content": "비로그인"})
    assert res.status_code == 302
    assert "/login" in res.headers["Location"]


def test_delete_comment_soft_and_count(client, login, user_factory, post_factory, db):
    author, commenter = user_factory(), user_factory()
    post_id = post_factory(author)
    login(commenter)
    client.post(f"/post/{post_id}/comment", data={"content": "지워질 댓글"})
    cid = db.execute(sa.select(schema.comments.c.id)).scalar_one()

    login(author)  # 타인은 삭제 불가
    assert client.post(f"/comment/{cid}/delete").status_code == 403

    login(commenter)
    assert client.post(f"/comment/{cid}/delete").status_code == 302
    row = db.execute(sa.select(schema.comments).where(schema.comments.c.id == cid)).mappings().one()
    assert row["deleted_at"] is not None
    assert _count(db, post_id) == 0


def test_deleted_parent_with_replies_shows_placeholder(client, login, user, post_factory, db):
    post_id = post_factory(user)
    login(user)
    client.post(f"/post/{post_id}/comment", data={"content": "부모"})
    parent_id = db.execute(sa.select(schema.comments.c.id)).scalar_one()
    client.post(f"/post/{post_id}/comment", data={"content": "자식 답글", "parent_id": parent_id})
    client.post(f"/comment/{parent_id}/delete")

    html = client.get(f"/post/{post_id}").get_data(as_text=True)
    assert "삭제된 댓글입니다" in html
    assert "자식 답글" in html


def test_comment_on_deleted_post_404(client, login, user, post_factory):
    from datetime import datetime
    post_id = post_factory(user, deleted_at=datetime.now())
    login(user)
    assert client.post(f"/post/{post_id}/comment",
                       data={"content": "x"}).status_code == 404
