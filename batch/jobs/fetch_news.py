"""뉴스 수집 (매시 정각) — RSS 파싱 → 키워드 분류 → url 기준 upsert.
저작권: 제목 + 요약(300자 이내)만 저장, 본문 전재 금지.
feed_parser 주입 가능(테스트 목).
"""
from datetime import datetime
from time import mktime

import sqlalchemy as sa

from app.db import schema

FEEDS = [
    ("한국경제", "https://www.hankyung.com/feed/economy"),
    ("연합뉴스", "https://www.yna.co.kr/rss/economy.xml"),
    ("매일경제", "https://www.mk.co.kr/rss/30100041/"),
    ("머니투데이", "https://rss.mt.co.kr/mt_news_economy.xml"),
    ("서울경제", "https://www.sedaily.com/rss/newsall.xml"),
]

CATEGORY_KEYWORDS = [
    ("realestate", ["아파트", "부동산", "전세", "청약", "재건축", "분양", "집값", "임대"]),
    ("coin", ["비트코인", "코인", "이더리움", "가상자산", "암호화폐", "크립토"]),
    ("policy", ["금리", "한은", "한국은행", "연준", "FOMC", "기준금리", "정책", "세제", "정부"]),
    ("stock", ["코스피", "코스닥", "주가", "증시", "상장", "실적", "주식", "반도체"]),
]

SUMMARY_MAX = 300


def classify(title, summary=""):
    text = f"{title} {summary}"
    for category, keywords in CATEGORY_KEYWORDS:
        if any(k in text for k in keywords):
            return category
    return "stock"  # 기본 분류


def _published_at(entry):
    parsed = getattr(entry, "published_parsed", None) or entry.get("published_parsed")
    if parsed:
        return datetime.fromtimestamp(mktime(parsed))
    return datetime.now()


def _clean_summary(entry):
    import re
    raw = entry.get("summary") or ""
    text = re.sub(r"<[^>]+>", "", raw).strip()
    return text[:SUMMARY_MAX] or None


def run(engine, feed_parser=None, feeds=None):
    if feed_parser is None:
        import feedparser as feed_parser
    feeds = feeds or FEEDS
    inserted = updated = 0
    na = schema.news_articles
    with engine.begin() as conn:
        for source, url in feeds:
            parsed = feed_parser.parse(url)
            for entry in parsed.entries:
                link = entry.get("link")
                title = (entry.get("title") or "").strip()
                if not link or not title:
                    continue
                summary = _clean_summary(entry)
                values = dict(
                    source=source, title=title[:200], summary=summary,
                    category=classify(title, summary or ""),
                    published_at=_published_at(entry),
                )
                existing = conn.execute(
                    sa.select(na.c.id).where(na.c.url == link)).first()
                if existing:
                    conn.execute(sa.update(na).where(na.c.url == link).values(**values))
                    updated += 1
                else:
                    conn.execute(na.insert().values(url=link, comment_count=0, **values))
                    inserted += 1
    return dict(inserted=inserted, updated=updated)
