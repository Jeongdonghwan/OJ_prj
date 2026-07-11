"""Step 12: sitemap.xml, robots.txt, meta/canonical/og."""
from datetime import datetime


def test_sitemap_basics(client, user, post_factory):
    pid = post_factory(user, title="사이트맵 글")
    deleted = post_factory(user, title="삭제 글", deleted_at=datetime.now())
    res = client.get("/sitemap.xml")
    assert res.status_code == 200
    assert "application/xml" in res.content_type
    xml = res.get_data(as_text=True)
    assert "<urlset" in xml
    for path in ["/community", "/news", "/columns", "/quiz/archive", "/policy", "/terms"]:
        assert f"http://localhost:5000{path}</loc>" in xml
    assert f"/post/{pid}</loc>" in xml
    assert f"/post/{deleted}</loc>" not in xml  # soft delete 제외
    assert "<lastmod>" in xml


def test_robots(client):
    res = client.get("/robots.txt")
    assert res.status_code == 200
    body = res.get_data(as_text=True)
    assert "Disallow: /admin" in body
    assert "Disallow: /my" in body
    assert "Disallow: /api/" in body
    assert "Sitemap: http://localhost:5000/sitemap.xml" in body


def test_home_meta(client):
    html = client.get("/").get_data(as_text=True)
    assert '<meta name="description"' in html
    assert '<link rel="canonical" href="http://localhost:5000/">' in html
    assert 'og:site_name' in html


def test_post_detail_meta(client, user, post_factory):
    pid = post_factory(user, title="OG 테스트 글", content="본문 요약이 들어갑니다")
    html = client.get(f"/post/{pid}").get_data(as_text=True)
    assert f'<link rel="canonical" href="http://localhost:5000/post/{pid}">' in html
    assert f'<meta property="og:url" content="http://localhost:5000/post/{pid}">' in html
    assert '<meta property="og:title" content="OG 테스트 글">' in html
    assert "본문 요약이 들어갑니다" in html


def test_community_canonical_keeps_cat_drops_sort(client):
    html = client.get("/community?cat=stock&sort=hot").get_data(as_text=True)
    assert 'rel="canonical" href="http://localhost:5000/community?cat=stock"' in html
    assert "sort=hot" not in html.split('rel="canonical"')[1].split(">")[0]
