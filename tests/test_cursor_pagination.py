"""Step 3: 커서 페이지네이션 — OFFSET 금지, (created_at, id) 커서."""
from datetime import datetime, timedelta


def _make_posts(post_factory, user, n, same_ts=False):
    base = datetime(2026, 7, 1, 12, 0, 0)
    ids = []
    for i in range(n):
        ts = base if same_ts else base + timedelta(minutes=i)
        ids.append(post_factory(user, title=f"글 {i}", created_at=ts))
    return ids


def test_first_page_and_cursor(app, client, user, post_factory):
    _make_posts(post_factory, user, 25)
    res = client.get("/api/posts")
    data = res.get_json()
    assert len(data["items"]) == 20
    assert data["next_cursor"]

    res2 = client.get(f"/api/posts?cursor={data['next_cursor']}")
    data2 = res2.get_json()
    assert len(data2["items"]) == 5
    assert data2["next_cursor"] is None


def test_no_duplicates_or_gaps_across_pages(app, client, user, post_factory):
    _make_posts(post_factory, user, 25)

    def titles(items):
        import re
        found = []
        for html in items:
            m = re.search(r'p-tt">(?:<[^>]+>[^<]*</span>)?([^<]+)<', html)
            found.append(m.group(1) if m else None)
        return found

    d1 = client.get("/api/posts").get_json()
    d2 = client.get(f"/api/posts?cursor={d1['next_cursor']}").get_json()
    all_titles = titles(d1["items"]) + titles(d2["items"])
    assert len(all_titles) == 25
    assert len(set(all_titles)) == 25  # 중복 없음


def test_same_timestamp_tie_broken_by_id(app, client, user, post_factory):
    """created_at이 전부 같아도 id로 안정 정렬·페이지 이동."""
    _make_posts(post_factory, user, 25, same_ts=True)
    d1 = client.get("/api/posts").get_json()
    assert len(d1["items"]) == 20
    d2 = client.get(f"/api/posts?cursor={d1['next_cursor']}").get_json()
    assert len(d2["items"]) == 5
    assert d2["next_cursor"] is None


def test_category_filter(app, client, user, post_factory):
    _make_posts(post_factory, user, 3)
    post_factory(user, category="stock", title="주식글")
    data = client.get("/api/posts?cat=stock").get_json()
    assert len(data["items"]) == 1
    assert "주식글" in data["items"][0]


def test_sort_profit_filter(app, client, user, post_factory):
    _make_posts(post_factory, user, 3)
    post_factory(user, post_type="profit", title="수익인증글", profit_amount=100000)
    data = client.get("/api/posts?sort=profit").get_json()
    assert len(data["items"]) == 1
    assert "수익인증글" in data["items"][0]


def test_invalid_cursor_falls_back_to_first_page(app, client, user, post_factory):
    _make_posts(post_factory, user, 5)
    data = client.get("/api/posts?cursor=@@invalid@@").get_json()
    assert len(data["items"]) == 5
