"""Step 8: 신고 — 접수, 관리자 처리, 플래그 글 검토 큐."""
import sqlalchemy as sa

from app.db import schema


def test_report_post(client, login, user_factory, post_factory, db):
    author, reporter = user_factory(), user_factory()
    pid = post_factory(author)
    login(reporter)
    res = client.post("/api/report", json={
        "target_type": "post", "target_id": pid, "reason": "리딩방 홍보 같아요"})
    assert res.get_json()["ok"] is True
    row = db.execute(sa.select(schema.reports)).mappings().one()
    assert row["reporter_id"] == reporter["id"]
    assert row["status"] == "pending"


def test_report_requires_login_and_valid_input(client, user, post_factory):
    pid = post_factory(user)
    assert client.post("/api/report", json={
        "target_type": "post", "target_id": pid, "reason": "r"}).status_code == 401


def test_report_bad_target_type(client, login, user):
    login(user)
    res = client.post("/api/report", json={
        "target_type": "hack", "target_id": 1, "reason": "r"})
    assert res.status_code == 400


def test_admin_resolves_report(client, login, user_factory, post_factory, admin_user, db):
    author, reporter = user_factory(), user_factory()
    pid = post_factory(author)
    login(reporter)
    client.post("/api/report", json={"target_type": "post", "target_id": pid, "reason": "신고"})

    login(admin_user)
    html = client.get("/admin/reports").get_data(as_text=True)
    assert "신고" in html
    rid = db.execute(sa.select(schema.reports.c.id)).scalar_one()
    client.post("/admin/reports", data={"report_id": rid, "action": "resolve"})
    assert db.execute(sa.select(schema.reports.c.status)).scalar_one() == "resolved"


def test_flagged_queue_and_actions(client, login, user, admin_user, db):
    login(user)
    client.post("/write", data={
        "category": "free", "post_type": "normal",
        "title": "리딩방 모집", "content": "수익보장!"})
    login(admin_user)
    html = client.get("/admin/flagged").get_data(as_text=True)
    assert "리딩방 모집" in html

    pid = db.execute(sa.select(schema.posts.c.id)).scalar_one()
    # 문제없음 처리 → 플래그 해제
    client.post("/admin/flagged", data={"post_id": pid, "action": "clear"})
    assert db.execute(sa.select(schema.posts.c.is_flagged).where(
        schema.posts.c.id == pid)).scalar_one() == 0
