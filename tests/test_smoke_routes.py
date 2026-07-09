"""Step 1: 라우트 응답 + 템플릿 chrome 구조 검증."""


def test_public_pages_200(client):
    for path in ["/", "/community", "/news", "/columns", "/login",
                 "/policy", "/terms", "/search", "/quiz/archive"]:
        res = client.get(path)
        assert res.status_code == 200, f"{path} -> {res.status_code}"


def test_login_required_redirects(client):
    for path in ["/write", "/my", "/notifications"]:
        res = client.get(path)
        assert res.status_code == 302, f"{path} -> {res.status_code}"
        assert "/login" in res.headers["Location"]


def test_home_chrome(client):
    html = client.get("/").get_data(as_text=True)
    for token in ['class="topnav"', 'class="gnb"', 'class="rail"', 'class="side"',
                  'class="adwing l"', 'class="cats"']:
        assert token in html, f"missing {token}"
    for name in ["부동산", "주식", "코인", "펀드·ETF", "예적금·절약", "자유수다"]:
        assert name in html
    assert "common.css" in html and "home.css" in html


def test_write_login_have_no_chrome(client, login, user):
    login(user)
    for path, css in [("/write", "write.css"), ("/login", "login.css")]:
        html = client.get(path).get_data(as_text=True)
        assert 'class="topnav"' not in html
        assert 'class="gnb"' not in html
        assert 'class="rail"' not in html
        assert 'class="adwing' not in html
        assert css in html


def test_community_page_structure(client):
    html = client.get("/community").get_data(as_text=True)
    assert 'class="chipbar"' in html
    assert 'class="sortbar"' in html
    assert 'class="fab"' in html
    assert 'class="wprompt"' in html
    assert "최신순" in html and "수익인증" in html


def test_static_assets_served(client):
    assert client.get("/static/css/common.css").status_code == 200
    for i in range(1, 13):
        res = client.get(f"/static/avatars/av_{i:02d}.svg")
        assert res.status_code == 200, f"avatar {i} missing"
    assert client.get("/static/img/favicon.svg").status_code == 200
    for js in ["quiz.js", "vote.js", "chips.js", "feed.js", "post.js", "write.js"]:
        assert client.get(f"/static/js/{js}").status_code == 200


def test_my_page_renders_for_user(client, login, user):
    login(user)
    html = client.get("/my").get_data(as_text=True)
    assert "마이페이지" in html
    assert user["nickname"] in html
    assert "내 글" in html and "스크랩" in html


def test_topnav_login_state(client, login, user):
    html = client.get("/").get_data(as_text=True)
    assert "로그인" in html  # 비로그인: 로그인 버튼
    login(user)
    html = client.get("/").get_data(as_text=True)
    assert "/static/avatars/av_" in html  # 로그인: 아바타
