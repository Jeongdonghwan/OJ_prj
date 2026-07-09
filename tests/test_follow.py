"""Step 7: 팔로우 — 토글, 자기 자신 400, 팔로워 칼럼 알림."""
import sqlalchemy as sa

from app.db import schema


def test_follow_toggle(client, login, user_factory, db):
    me, target = user_factory(), user_factory()
    login(me)
    r = client.post("/api/follow", json={"user_id": target["id"]}).get_json()
    assert r["on"] is True
    count = db.execute(sa.select(sa.func.count()).select_from(schema.follows)).scalar_one()
    assert count == 1
    r = client.post("/api/follow", json={"user_id": target["id"]}).get_json()
    assert r["on"] is False
    count = db.execute(sa.select(sa.func.count()).select_from(schema.follows)).scalar_one()
    assert count == 0


def test_self_follow_400(client, login, user):
    login(user)
    res = client.post("/api/follow", json={"user_id": user["id"]})
    assert res.status_code == 400


def test_follow_requires_login(client, user):
    assert client.post("/api/follow", json={"user_id": user["id"]}).status_code == 401


def test_follow_button_on_post_detail(client, login, user_factory, post_factory):
    author, visitor = user_factory(), user_factory()
    pid = post_factory(author)
    # 비로그인: 팔로우 버튼 없음
    assert 'class="follow' not in client.get(f"/post/{pid}").get_data(as_text=True)
    # 타인 글: 있음
    login(visitor)
    assert 'class="follow' in client.get(f"/post/{pid}").get_data(as_text=True)
    # 내 글: 없음
    login(author)
    assert 'class="follow' not in client.get(f"/post/{pid}").get_data(as_text=True)


def test_follower_notified_on_new_column(client, login, user_factory, expert_user, db):
    fan = user_factory("팬유저")
    login(fan)
    client.post("/api/follow", json={"user_id": expert_user["id"]})

    login(expert_user)
    res = client.post("/write", data={
        "category": "fund", "post_type": "normal", "column_tag": "절세",
        "title": "새 칼럼입니다", "content": "본문"})
    assert res.status_code == 302

    noti = db.execute(sa.select(schema.notifications).where(
        schema.notifications.c.user_id == fan["id"])).mappings().all()
    assert len(noti) == 1
    assert noti[0]["type"] == "column"
    assert "새 칼럼" in noti[0]["message"]
