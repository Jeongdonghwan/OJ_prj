"""Step 5: 포인트 — 합계 불변식, 출석 1일 1회."""
import sqlalchemy as sa

from app.db import schema


def _cached_points(db, uid):
    return db.execute(sa.select(schema.users.c.points)
                      .where(schema.users.c.id == uid)).scalar_one()


def test_award_updates_log_and_cache(app, user, db):
    from app.services.point_service import award, total_points
    with app.test_request_context():
        award(user["id"], 10, "quiz")
        award(user["id"], 3, "vote")
        award(user["id"], 2, "attendance")
        assert total_points(user["id"]) == 15
    assert _cached_points(db, user["id"]) == 15  # 캐시 == 로그 합


def test_attendance_once_per_day(client, login, user, db):
    login(user)
    client.get("/")   # 첫 요청 → +2P
    client.get("/community")  # 같은 날 추가 요청 → no-op
    client.get("/")
    logs = db.execute(sa.select(schema.point_logs).where(
        schema.point_logs.c.user_id == user["id"],
        schema.point_logs.c.reason == "attendance")).mappings().all()
    assert len(logs) == 1
    assert logs[0]["amount"] == 2
    assert _cached_points(db, user["id"]) == 2


def test_attendance_fresh_session_same_day_no_dup(app, client, login, user, db):
    login(user)
    client.get("/")
    # 세션이 새로 생겨도 DB 확인으로 이중 적립 방지
    fresh = app.test_client()
    with fresh.session_transaction() as sess:
        sess["_user_id"] = str(user["id"])
        sess["_fresh"] = True
    fresh.get("/")
    logs = db.execute(sa.select(sa.func.count()).where(
        schema.point_logs.c.user_id == user["id"],
        schema.point_logs.c.reason == "attendance")).scalar_one()
    assert logs == 1
