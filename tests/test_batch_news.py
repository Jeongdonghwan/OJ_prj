"""Step 6: fetch_news 배치 — 목 피드, 키워드 분류, url dedup, 본문 미저장."""
import sqlalchemy as sa

from app.db import engine as db_engine
from app.db import schema
from batch.jobs import fetch_news
from tests.fixtures.fake_feeds import SAMPLE_ENTRIES, SAMPLE_FEED_URL, FakeFeedParser


def _run(app, entries=None):
    parser = FakeFeedParser({SAMPLE_FEED_URL: entries or SAMPLE_ENTRIES})
    result = fetch_news.run(db_engine.get_engine(app), feed_parser=parser,
                            feeds=[("테스트뉴스", SAMPLE_FEED_URL)])
    return result, parser


def test_insert_and_classify(app, db):
    result, _ = _run(app)
    assert result == {"inserted": 4, "updated": 0}
    rows = {r["title"]: r for r in
            db.execute(sa.select(schema.news_articles)).mappings().all()}
    assert rows["서울 아파트값 3주 연속 상승"]["category"] == "realestate"
    assert rows["비트코인 1억 돌파 임박"]["category"] == "coin"
    assert rows["연준, 7월 기준금리 동결 시사"]["category"] == "policy"
    assert rows["코스피 2900 돌파, 반도체 강세"]["category"] == "stock"
    # HTML 태그 제거된 요약만 저장 (본문 전재 금지)
    assert rows["서울 아파트값 3주 연속 상승"]["summary"] == "강남권 신고가가 잇따르고 있다."


def test_url_dedup_upsert(app, db):
    _run(app)
    result, _ = _run(app)  # 같은 피드 재수집
    assert result == {"inserted": 0, "updated": 4}
    count = db.execute(sa.select(sa.func.count()).select_from(schema.news_articles)).scalar_one()
    assert count == 4


def test_summary_truncated_300(app, db):
    from tests.fixtures.fake_feeds import _entry
    long = _entry("긴 요약 기사", "https://news.example.com/long", "가" * 500)
    _run(app, entries=[long])
    row = db.execute(sa.select(schema.news_articles.c.summary).where(
        schema.news_articles.c.url == "https://news.example.com/long")).scalar_one()
    assert len(row) == 300


def test_news_page_renders_articles(app, client):
    _run(app)
    html = client.get("/news").get_data(as_text=True)
    assert "서울 아파트값 3주 연속 상승" in html
    assert 'target="_blank"' in html  # 아웃링크
    assert "https://news.example.com/1" in html
    # 칩 필터 — 본문 리스트(.nlist)만 검사 (레일 위젯은 전체 최신 뉴스라 제외)
    import re
    html = client.get("/news?category=coin").get_data(as_text=True)
    nlist = re.search(r'class="nlist"(.*?)</main>', html, re.S).group(1)
    assert "비트코인 1억 돌파 임박" in nlist
    assert "서울 아파트값" not in nlist
