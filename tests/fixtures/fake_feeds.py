"""feedparser 목 — 실제 HTTP 없이 고정 엔트리 반환."""
import time
from types import SimpleNamespace


def _entry(title, link, summary="", published=None):
    e = {
        "title": title, "link": link, "summary": summary,
        "published_parsed": time.localtime(published or time.time()),
    }
    ns = SimpleNamespace(**e)
    ns.get = e.get
    return ns


class FakeFeedParser:
    """parse(url) 호출 시 url에 매핑된 엔트리 목록 반환."""

    def __init__(self, feed_map):
        self.feed_map = feed_map
        self.parsed_urls = []

    def parse(self, url):
        self.parsed_urls.append(url)
        return SimpleNamespace(entries=self.feed_map.get(url, []))


SAMPLE_FEED_URL = "https://example.com/rss"

SAMPLE_ENTRIES = [
    _entry("서울 아파트값 3주 연속 상승", "https://news.example.com/1",
           "<p>강남권 <b>신고가</b>가 잇따르고 있다.</p>"),
    _entry("비트코인 1억 돌파 임박", "https://news.example.com/2", "코인 시장이 들썩."),
    _entry("연준, 7월 기준금리 동결 시사", "https://news.example.com/3", "시장은 9월 인하에 무게."),
    _entry("코스피 2900 돌파, 반도체 강세", "https://news.example.com/4", "증시 요약."),
]
