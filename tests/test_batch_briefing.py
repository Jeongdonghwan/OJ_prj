"""Step 6: daily_briefing 배치 — FakeLLM, idempotent, 헤드라인 포함."""
from datetime import date, datetime, timedelta

import sqlalchemy as sa

from app.db import engine as db_engine
from app.db import schema
from batch.jobs import daily_briefing


class FakeLLM:
    def __init__(self, response="아파트 상승 · 금리 동결 · 코인 들썩"):
        self.response = response
        self.prompts = []

    def summarize(self, prompt):
        self.prompts.append(prompt)
        return self.response


def _add_news(app, title, hours_ago=2):
    engine = db_engine.get_engine(app)
    with engine.begin() as conn:
        conn.execute(schema.news_articles.insert().values(
            source="테스트", title=title, url=f"https://n.example.com/{title}",
            category="stock", published_at=datetime.now() - timedelta(hours=hours_ago),
            comment_count=0))


def test_briefing_created_with_headlines(app, db):
    _add_news(app, "서울 아파트값 상승")
    _add_news(app, "연준 금리 동결")
    llm = FakeLLM()
    result = daily_briefing.run(db_engine.get_engine(app), llm_client=llm)
    assert result == "created"
    assert "서울 아파트값 상승" in llm.prompts[0]
    assert "연준 금리 동결" in llm.prompts[0]
    row = db.execute(sa.select(schema.daily_briefings)).mappings().one()
    assert row["brief_date"] == date.today()
    assert row["content"] == "아파트 상승 · 금리 동결 · 코인 들썩"


def test_briefing_idempotent_per_day(app, db):
    _add_news(app, "뉴스")
    engine = db_engine.get_engine(app)
    llm = FakeLLM()
    assert daily_briefing.run(engine, llm_client=llm) == "created"
    assert daily_briefing.run(engine, llm_client=llm) == "exists"
    assert len(llm.prompts) == 1  # 두 번째는 LLM 호출 없음
    count = db.execute(sa.select(sa.func.count()).select_from(schema.daily_briefings)).scalar_one()
    assert count == 1


def test_briefing_skipped_without_news(app):
    result = daily_briefing.run(db_engine.get_engine(app), llm_client=FakeLLM())
    assert result == "no_news"


def test_briefing_rendered_on_news_page(app, client, db):
    _add_news(app, "뉴스")
    daily_briefing.run(db_engine.get_engine(app), llm_client=FakeLLM())
    html = client.get("/news").get_data(as_text=True)
    assert "오늘의 브리핑" in html
    assert "아파트 상승 · 금리 동결 · 코인 들썩" in html


def test_content_truncated_500(app, db):
    _add_news(app, "뉴스")
    daily_briefing.run(db_engine.get_engine(app), llm_client=FakeLLM("나" * 800))
    content = db.execute(sa.select(schema.daily_briefings.c.content)).scalar_one()
    assert len(content) == 500
