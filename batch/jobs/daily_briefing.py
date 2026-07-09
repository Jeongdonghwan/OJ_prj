"""오늘의 브리핑 (06:00) — 전일 뉴스 헤드라인을 Claude API로 3줄 요약 → daily_briefings.
llm_client 주입 가능(테스트 목). 같은 날짜에 이미 있으면 재생성하지 않음(idempotent).
"""
import os
from datetime import date, datetime, timedelta

import sqlalchemy as sa

from app.db import schema

HEADLINE_LIMIT = 15
CONTENT_MAX = 500

PROMPT_TEMPLATE = """다음은 지난 24시간의 한국 경제 뉴스 헤드라인입니다.

{headlines}

재테크 커뮤니티 사용자를 위해 오늘의 핵심을 세 가지로 요약해주세요.
- 형식: "항목1 · 항목2 · 항목3" 처럼 가운뎃점으로 구분한 한 문단
- 각 항목은 20자 이내로 간결하게
- 과장이나 투자 권유 표현 금지"""


class AnthropicClient:
    """실 배포용 Claude API 클라이언트 (테스트에서는 Fake로 교체)."""

    def summarize(self, prompt):
        import anthropic
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        message = client.messages.create(
            model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5"),
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text.strip()


def run(engine, llm_client=None, today=None):
    today = today or date.today()
    db = schema.daily_briefings
    with engine.begin() as conn:
        existing = conn.execute(
            sa.select(db.c.brief_date).where(db.c.brief_date == today)).first()
        if existing:
            return "exists"
        since = datetime.combine(today, datetime.min.time()) - timedelta(days=1)
        headlines = conn.execute(
            sa.select(schema.news_articles.c.title)
            .where(schema.news_articles.c.published_at >= since)
            .order_by(schema.news_articles.c.published_at.desc())
            .limit(HEADLINE_LIMIT)
        ).scalars().all()
        if not headlines:
            return "no_news"
        prompt = PROMPT_TEMPLATE.format(headlines="\n".join(f"- {h}" for h in headlines))
        client = llm_client or AnthropicClient()
        content = client.summarize(prompt)[:CONTENT_MAX]
        conn.execute(db.insert().values(brief_date=today, content=content))
    return "created"
