"""뉴스 목록/브리핑 조회."""
from datetime import date

import sqlalchemy as sa

from app.db import schema
from app.db.engine import get_conn


def list_articles(category=None, limit=30):
    conn = get_conn()
    q = sa.select(schema.news_articles).order_by(schema.news_articles.c.published_at.desc()).limit(limit)
    if category:
        q = q.where(schema.news_articles.c.category == category)
    return [dict(r) for r in conn.execute(q).mappings().all()]


def get_article(news_id):
    conn = get_conn()
    row = conn.execute(
        sa.select(schema.news_articles).where(schema.news_articles.c.id == news_id)
    ).mappings().first()
    return dict(row) if row else None


def get_today_briefing(today=None):
    conn = get_conn()
    row = conn.execute(
        sa.select(schema.daily_briefings)
        .where(schema.daily_briefings.c.brief_date <= (today or date.today()))
        .order_by(schema.daily_briefings.c.brief_date.desc()).limit(1)
    ).mappings().first()
    return dict(row) if row else None
