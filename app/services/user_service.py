"""회원 생성/조회, 닉네임 규칙."""
from datetime import datetime, timedelta

import sqlalchemy as sa
from werkzeug.security import check_password_hash, generate_password_hash

from app.db import schema
from app.db.engine import get_conn

_u = schema.users
NICKNAME_CHANGE_DAYS = 30
AVATAR_COUNT = 12


def _assign_avatar(conn, user_id):
    avatar_no = (user_id % AVATAR_COUNT) + 1
    conn.execute(sa.update(_u).where(_u.c.id == user_id).values(avatar_no=avatar_no))
    return avatar_no


def nickname_exists(nickname, conn=None):
    conn = conn or get_conn()
    return conn.execute(sa.select(_u.c.id).where(_u.c.nickname == nickname)).first() is not None


def email_exists(email, conn=None):
    conn = conn or get_conn()
    return conn.execute(sa.select(_u.c.id).where(_u.c.email == email)).first() is not None


def create_email_user(email, password, nickname):
    conn = get_conn()
    if email_exists(email, conn):
        return None, "email_taken"
    if nickname_exists(nickname, conn):
        return None, "nickname_taken"
    res = conn.execute(_u.insert().values(
        email=email, oauth_provider="email", nickname=nickname,
        password_hash=generate_password_hash(password),
        avatar_no=1, status="active",
    ))
    uid = res.inserted_primary_key[0]
    _assign_avatar(conn, uid)
    conn.commit()
    return uid, "ok"


def verify_email_login(email, password):
    conn = get_conn()
    row = conn.execute(sa.select(_u).where(
        _u.c.email == email, _u.c.oauth_provider == "email")).mappings().first()
    if not row or not row["password_hash"]:
        return None
    if not check_password_hash(row["password_hash"], password):
        return None
    return dict(row)


def get_or_create_social_user(provider, profile):
    """소셜(kakao/naver) 프로필로 기존 사용자 로그인 또는 신규 생성. 반환: (user_row, created)."""
    conn = get_conn()
    row = conn.execute(sa.select(_u).where(
        _u.c.oauth_provider == provider, _u.c.oauth_id == profile["oauth_id"]
    )).mappings().first()
    if row:
        return dict(row), False
    base = profile.get("nickname") or "오재유저"
    nickname = base
    n = 1
    while nickname_exists(nickname, conn):
        n += 1
        nickname = f"{base}{n}"
    email = profile.get("email")
    if email and email_exists(email, conn):
        email = None
    res = conn.execute(_u.insert().values(
        email=email, oauth_provider=provider, oauth_id=profile["oauth_id"],
        nickname=nickname, avatar_no=1, status="active",
    ))
    uid = res.inserted_primary_key[0]
    _assign_avatar(conn, uid)
    conn.commit()
    row = conn.execute(sa.select(_u).where(_u.c.id == uid)).mappings().one()
    return dict(row), True


def get_or_create_kakao_user(profile):
    return get_or_create_social_user("kakao", profile)


def touch_last_login(user_id):
    conn = get_conn()
    conn.execute(sa.update(_u).where(_u.c.id == user_id)
                 .values(last_login_at=datetime.now()))
    conn.commit()


def update_profile_img(user_id, path):
    conn = get_conn()
    conn.execute(sa.update(_u).where(_u.c.id == user_id).values(profile_img=path))
    conn.commit()


def withdraw(user_id):
    """회원 탈퇴: soft delete + PII 스크럽. 글/댓글은 '탈퇴회원N' 표시로 유지."""
    conn = get_conn()
    nickname = f"탈퇴회원{user_id}"
    n = 0
    while nickname_exists(nickname, conn):
        n += 1
        nickname = f"탈퇴회원{user_id}_{n}"
    conn.execute(sa.update(_u).where(_u.c.id == user_id).values(
        status="deleted", nickname=nickname,
        email=None, oauth_id=None, password_hash=None, profile_img=None))
    conn.commit()


def change_nickname(user_id, new_nickname):
    """30일 1회 제한."""
    conn = get_conn()
    row = conn.execute(sa.select(_u.c.nickname_changed_at).where(_u.c.id == user_id)).mappings().first()
    if not row:
        return "not_found"
    last = row["nickname_changed_at"]
    if last and datetime.now() - last < timedelta(days=NICKNAME_CHANGE_DAYS):
        return "too_soon"
    if nickname_exists(new_nickname, conn):
        return "nickname_taken"
    conn.execute(sa.update(_u).where(_u.c.id == user_id).values(
        nickname=new_nickname, nickname_changed_at=datetime.now()))
    conn.commit()
    return "ok"
