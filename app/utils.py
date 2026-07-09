"""템플릿 헬퍼: 아바타, 시간 표기, 카테고리 색상 클래스."""
from datetime import datetime

AVATAR_BG = {
    1: "#F9DDE7", 2: "#F5E9DC", 3: "#EDECFA", 4: "#FDF3D9",
    5: "#E5F3EC", 6: "#FADEDA", 7: "#FAEEDA", 8: "#E9EDFA",
    9: "#E9F1FA", 10: "#EAF5EC", 11: "#FAE7DC", 12: "#F5EFE6",
}

# 초안에 명시된 카테고리 메타 컬러 (미명시 카테고리는 기본 그레이)
CAT_META = {
    "realestate": ' class="cat-r"',
    "saving": ' class="cat-s"',
    "fund": ' class="cat-f"',
    "coin": ' style="color:#B87A18;font-weight:500"',
}


def _get(u, key, default=None):
    if u is None:
        return default
    if isinstance(u, dict):
        return u.get(key, default)
    return getattr(u, key, default)


def avatar_url(user):
    profile = _get(user, "profile_img")
    if profile:
        return profile
    no = _get(user, "avatar_no") or 1
    return f"/static/avatars/av_{int(no):02d}.svg"


def avatar_bg(user):
    profile = _get(user, "profile_img")
    if profile:
        return "#EEF0F2"
    no = _get(user, "avatar_no") or 1
    return AVATAR_BG.get(int(no), "#EEF0F2")


def cat_meta_attr(slug):
    return CAT_META.get(slug, "")


def time_ago(dt):
    if dt is None:
        return ""
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    now = datetime.now()
    diff = now - dt
    sec = diff.total_seconds()
    if sec < 60:
        return "방금 전"
    if sec < 3600:
        return f"{int(sec // 60)}분 전"
    if sec < 86400 and dt.date() == now.date():
        return f"{int(sec // 3600)}시간 전"
    days = (now.date() - dt.date()).days
    if days <= 1:
        return "어제"
    if days < 7:
        return f"{days}일 전"
    if dt.year == now.year:
        return f"{dt.month}.{dt.day}"
    return f"{dt.year}.{dt.month}.{dt.day}"


def comma(n):
    if n is None:
        return "0"
    return f"{int(n):,}"


def register_template_helpers(app):
    app.jinja_env.filters["time_ago"] = time_ago
    app.jinja_env.filters["comma"] = comma
    app.jinja_env.globals["avatar_url"] = avatar_url
    app.jinja_env.globals["avatar_bg"] = avatar_bg
    app.jinja_env.globals["cat_meta_attr"] = cat_meta_attr
