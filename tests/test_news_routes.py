"""Step 6: 뉴스 상세(/news/<id>) — 댓글, 아웃링크, 404."""
from datetime import datetime

import pytest
import sqlalchemy as sa

from app.db import engine as db_engine
from app.db import schema


@pytest.fixture()
def news_factory(app):
    def make(title="테스트 뉴스", url=None, category="stock", summary="요약입니다"):
        engine = db_engine.get_engine(app)
        with engine.begin() as conn:
            res = conn.execute(schema.news_articles.insert().values(
                source="테스트", title=title,
                url=url or f"https://n.example.com/{title}",
                summary=summary, category=category,
                published_at=datetime.now(), comment_count=0))
            return res.inserted_primary_key[0]
    return make


def test_news_detail_renders(client, news_factory):
    nid = news_factory(title="상세 뉴스")
    html = client.get(f"/news/{nid}").get_data(as_text=True)
    assert "상세 뉴스" in html
    assert "원문 기사 보기" in html
    assert "요약입니다" in html


def test_news_detail_404(client):
    assert client.get("/news/9999").status_code == 404


def test_news_comment_flow(client, login, user, news_factory, db):
    nid = news_factory()
    # 비로그인 → 로그인 유도
    res = client.post(f"/api/news/{nid}/comment", data={"content": "비로그인"})
    assert res.status_code == 302 and "/login" in res.headers["Location"]

    login(user)
    res = client.post(f"/api/news/{nid}/comment", data={"content": "뉴스 댓글!"})
    assert res.status_code == 302
    html = client.get(f"/news/{nid}").get_data(as_text=True)
    assert "뉴스 댓글!" in html
    cc = db.execute(sa.select(schema.news_articles.c.comment_count).where(
        schema.news_articles.c.id == nid)).scalar_one()
    assert cc == 1
