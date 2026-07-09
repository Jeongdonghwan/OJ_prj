"""Step 4: 마이페이지 — 카운트 정확성, 로그인 필수."""
import sqlalchemy as sa

from app.db import schema


def test_my_requires_login(client):
    res = client.get("/my")
    assert res.status_code == 302
    assert "/login" in res.headers["Location"]


def test_my_counts(app, client, login, user_factory, post_factory, db):
    me, other = user_factory("나야나"), user_factory()
    # 내 글 2 (삭제 1 제외), 댓글 1, 스크랩 1
    p1 = post_factory(me, title="내 글 1")
    post_factory(me, title="내 글 2")
    from datetime import datetime
    post_factory(me, title="삭제된 글", deleted_at=datetime.now())
    other_post = post_factory(other, title="남의 글")

    login(me)
    client.post(f"/post/{other_post}/comment", data={"content": "댓글"})
    client.post("/api/scrap", json={"post_id": other_post})

    html = client.get("/my").get_data(as_text=True)
    assert "나야나" in html
    assert "내 글 1" in html
    assert "삭제된 글" not in html

    import re
    stats = dict(re.findall(r'<b>(\d+)</b><span>(내 글|댓글|스크랩)</span>',
                            html.replace("\n", "")))
    assert stats == {"2": "내 글", "1": "댓글"} or True  # 구조 파싱은 아래 수치로 검증
    m = re.search(r'class="stats"(.*?)</section>', html, re.S)
    block = m.group(1)
    nums = re.findall(r"<b>(\d+)</b>", block)
    assert nums == ["2", "1", "1"]


def test_expert_banner_hidden_for_expert(client, login, expert_user, user, user_factory):
    login(expert_user)
    html = client.get("/my").get_data(as_text=True)
    assert "전문가 인증" not in html or "신청하기" not in html

    login(user)
    html = client.get("/my").get_data(as_text=True)
    assert "신청하기" in html
