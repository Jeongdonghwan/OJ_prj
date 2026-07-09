"""Step 6: 투표 — 중복 방지, 비율, 활성창 노출, 마감 배치."""
from datetime import datetime, timedelta

import pytest
import sqlalchemy as sa

from app.db import engine as db_engine
from app.db import schema
from batch.jobs import close_poll


@pytest.fixture()
def poll_factory(app):
    def make(question="이번 주 코스피, 어떻게 될까요?", hours_from=-1, hours_to=23,
             is_active=1, option_up="오른다", option_down="떨어진다"):
        now = datetime.now()
        engine = db_engine.get_engine(app)
        with engine.begin() as conn:
            res = conn.execute(schema.polls.insert().values(
                question=question, option_up=option_up, option_down=option_down,
                starts_at=now + timedelta(hours=hours_from),
                ends_at=now + timedelta(hours=hours_to), is_active=is_active))
            return res.inserted_primary_key[0]
    return make


def test_vote_and_ratio(client, login, user_factory, poll_factory, db):
    pid = poll_factory()
    u1, u2, u3 = user_factory(), user_factory(), user_factory()
    login(u1)
    r = client.post("/api/poll/vote", json={"poll_id": pid, "side": "up"}).get_json()
    assert (r["up_pct"], r["down_pct"], r["total"]) == (100, 0, 1)
    login(u2)
    client.post("/api/poll/vote", json={"poll_id": pid, "side": "up"})
    login(u3)
    r = client.post("/api/poll/vote", json={"poll_id": pid, "side": "down"}).get_json()
    assert r["total"] == 3
    assert r["up_pct"] == 67 and r["down_pct"] == 33
    # 투표 +3P
    amt = db.execute(sa.select(schema.point_logs.c.amount).where(
        schema.point_logs.c.user_id == u3["id"],
        schema.point_logs.c.reason == "vote")).scalar_one()
    assert amt == 3


def test_duplicate_vote_409_keeps_first(client, login, user, poll_factory, db):
    pid = poll_factory()
    login(user)
    client.post("/api/poll/vote", json={"poll_id": pid, "side": "up"})
    res = client.post("/api/poll/vote", json={"poll_id": pid, "side": "down"})
    assert res.status_code == 409
    side = db.execute(sa.select(schema.poll_votes.c.side).where(
        schema.poll_votes.c.user_id == user["id"])).scalar_one()
    assert side == "up"  # 첫 투표 유지
    votes = db.execute(sa.select(sa.func.count()).select_from(schema.poll_votes)).scalar_one()
    assert votes == 1


def test_anonymous_vote_401(client, poll_factory):
    pid = poll_factory()
    assert client.post("/api/poll/vote",
                       json={"poll_id": pid, "side": "up"}).status_code == 401


def test_card_shown_only_in_active_window(client, poll_factory):
    # 활성 투표 없음 → 카드 미노출
    html = client.get("/community").get_data(as_text=True)
    assert 'class="vtbox' not in html

    poll_factory(question="지난 투표", hours_from=-48, hours_to=-24)  # 종료됨
    poll_factory(question="미래 투표", hours_from=24, hours_to=48)    # 시작 전
    poll_factory(question="꺼진 투표", is_active=0)                    # 비활성
    html = client.get("/community").get_data(as_text=True)
    assert 'class="vtbox' not in html

    poll_factory(question="지금 활성 투표")
    html = client.get("/community").get_data(as_text=True)
    assert "지금 활성 투표" in html


def test_expired_vote_rejected(client, login, user, poll_factory):
    pid = poll_factory(hours_from=-48, hours_to=-24)
    login(user)
    res = client.post("/api/poll/vote", json={"poll_id": pid, "side": "up"})
    assert res.status_code == 404


def test_close_poll_batch(app, poll_factory, db):
    expired = poll_factory(question="만료", hours_from=-48, hours_to=-1)
    active = poll_factory(question="진행중", hours_from=-1, hours_to=23)
    result = close_poll.run(db_engine.get_engine(app))
    assert result["closed"] == 1
    rows = {r["question"]: r["is_active"] for r in
            db.execute(sa.select(schema.polls)).mappings().all()}
    assert rows["만료"] == 0
    assert rows["진행중"] == 1
    assert result["quiz_ready"] is False  # 익일 퀴즈 미등록 경고


def test_voted_state_rendered(client, login, user, poll_factory):
    pid = poll_factory()
    login(user)
    client.post("/api/poll/vote", json={"poll_id": pid, "side": "up"})
    html = client.get("/community").get_data(as_text=True)
    assert "vtbox done" in html
    assert "1명 참여" in html
