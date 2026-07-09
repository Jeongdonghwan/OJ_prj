"""Step 8: 검색 — 제목+본문 LIKE, 와일드카드 이스케이프, 삭제 제외."""
from datetime import datetime


def test_search_title_and_content(client, user, post_factory):
    post_factory(user, title="청약통장 올릴까요", content="본문입니다")
    post_factory(user, title="다른 글", content="본문에 청약통장 이야기")
    post_factory(user, title="무관한 글", content="무관")
    html = client.get("/search?q=청약통장").get_data(as_text=True)
    assert "청약통장 올릴까요" in html
    assert "다른 글" in html
    assert "무관한 글" not in html


def test_search_excludes_deleted(client, user, post_factory):
    post_factory(user, title="삭제된 청약 글", deleted_at=datetime.now())
    html = client.get("/search?q=청약").get_data(as_text=True)
    assert "삭제된 청약 글" not in html
    assert "검색 결과가 없습니다" in html


def test_search_escapes_wildcards(client, user, post_factory):
    post_factory(user, title="수익률 100% 달성")
    post_factory(user, title="아무 글", content="전혀 다른 내용")
    html = client.get("/search?q=100%").get_data(as_text=True)
    assert "수익률 100% 달성" in html
    assert "아무 글" not in html  # '%'가 와일드카드로 동작하면 전부 매칭됨


def test_empty_query_safe(client):
    res = client.get("/search")
    assert res.status_code == 200
    assert client.get("/search?q=").status_code == 200
