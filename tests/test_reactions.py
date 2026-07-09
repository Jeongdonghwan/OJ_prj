"""Step 3: 도움됐어요 토글, 스크랩, 조회수 세션 중복 차단."""
import sqlalchemy as sa

from app.db import schema


def test_like_toggle(client, login, user, post_factory, db):
    post_id = post_factory(user)
    login(user)
    r1 = client.post("/api/like", json={"post_id": post_id}).get_json()
    assert r1 == {"on": True, "count": 1}
    r2 = client.post("/api/like", json={"post_id": post_id}).get_json()
    assert r2 == {"on": False, "count": 0}
    assert db.execute(sa.select(schema.posts.c.like_count)
                      .where(schema.posts.c.id == post_id)).scalar_one() == 0


def test_like_requires_login(client, user, post_factory):
    post_id = post_factory(user)
    res = client.post("/api/like", json={"post_id": post_id})
    assert res.status_code == 401
    assert res.get_json()["error"] == "login_required"


def test_scrap_toggle(client, login, user, post_factory, db):
    post_id = post_factory(user)
    login(user)
    assert client.post("/api/scrap", json={"post_id": post_id}).get_json()["on"] is True
    assert db.execute(sa.select(sa.func.count()).select_from(schema.scraps)).scalar_one() == 1
    assert client.post("/api/scrap", json={"post_id": post_id}).get_json()["on"] is False
    assert db.execute(sa.select(sa.func.count()).select_from(schema.scraps)).scalar_one() == 0


def test_view_count_session_dedup(app, client, user, post_factory, db):
    post_id = post_factory(user)

    def views():
        return db.execute(sa.select(schema.posts.c.view_count)
                          .where(schema.posts.c.id == post_id)).scalar_one()

    client.get(f"/post/{post_id}")
    assert views() == 1
    client.get(f"/post/{post_id}")  # 같은 세션 → 증가 없음
    assert views() == 1

    fresh = app.test_client()  # 새 세션 → 증가
    fresh.get(f"/post/{post_id}")
    assert views() == 2


def test_viewed_list_capped_at_50(client, user, post_factory):
    ids = [post_factory(user, title=f"글{i}") for i in range(55)]
    for pid in ids:
        client.get(f"/post/{pid}")
    with client.session_transaction() as sess:
        viewed = sess["viewed_posts"]
        assert len(viewed) == 50
        assert viewed[-1] == ids[-1]  # 최근 것 유지
        assert ids[0] not in viewed   # 오래된 것 제거
