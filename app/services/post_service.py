"""게시글 CRUD, 커서 페이지네이션, 검색."""
import base64
from datetime import datetime

import sqlalchemy as sa

from app.db import schema
from app.db.engine import get_conn

PAGE_SIZE = 20

_p, _u, _c = schema.posts, schema.users, schema.categories

_POST_COLS = [
    _p.c.id, _p.c.user_id, _p.c.title, _p.c.content, _p.c.post_type,
    _p.c.is_column, _p.c.column_tag, _p.c.thumbnail, _p.c.profit_amount,
    _p.c.view_count, _p.c.like_count, _p.c.comment_count, _p.c.created_at,
    _u.c.nickname, _u.c.avatar_no, _u.c.profile_img, _u.c.is_verified,
    _c.c.slug.label("cat_slug"), _c.c.name.label("cat_name"),
]


def _base_query():
    j = _p.join(_u, _p.c.user_id == _u.c.id).join(_c, _p.c.category_id == _c.c.id)
    return sa.select(*_POST_COLS).select_from(j).where(_p.c.deleted_at.is_(None))


def encode_cursor(created_at, post_id):
    raw = f"{created_at.isoformat()}|{post_id}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def decode_cursor(cursor):
    try:
        raw = base64.urlsafe_b64decode(cursor.encode()).decode()
        ts, pid = raw.rsplit("|", 1)
        return datetime.fromisoformat(ts), int(pid)
    except Exception:
        return None


def get_category(slug, conn=None):
    conn = conn or get_conn()
    return conn.execute(sa.select(_c).where(_c.c.slug == slug)).mappings().first()


def list_categories(conn=None):
    conn = conn or get_conn()
    return [dict(r) for r in conn.execute(
        sa.select(_c).order_by(_c.c.sort_order)).mappings().all()]


def list_posts(cat=None, sort="latest", cursor=None, limit=PAGE_SIZE):
    """커서 페이지네이션 목록. 반환: (posts, next_cursor)."""
    conn = get_conn()
    q = _base_query()
    if cat:
        q = q.where(_c.c.slug == cat)
    if sort == "expert":
        q = q.where(_u.c.is_verified == 1)
    elif sort == "profit":
        q = q.where(_p.c.post_type == "profit")
    elif sort == "trade":
        q = q.where(_p.c.post_type == "trade")
    elif sort == "hot":
        # 인기순: 최근 글 대상 가중치 정렬 (상위 N 고정 페이지, 커서 미사용)
        q = q.order_by((_p.c.view_count + _p.c.comment_count * 5 + _p.c.like_count * 3).desc(),
                       _p.c.id.desc()).limit(limit)
        rows = [dict(r) for r in conn.execute(q).mappings().all()]
        return rows, None

    q = q.order_by(_p.c.created_at.desc(), _p.c.id.desc())
    if cursor:
        decoded = decode_cursor(cursor)
        if decoded:
            ts, pid = decoded
            q = q.where(sa.or_(_p.c.created_at < ts,
                               sa.and_(_p.c.created_at == ts, _p.c.id < pid)))
    rows = [dict(r) for r in conn.execute(q.limit(limit + 1)).mappings().all()]
    next_cursor = None
    if len(rows) > limit:
        rows = rows[:limit]
        last = rows[-1]
        next_cursor = encode_cursor(last["created_at"], last["id"])
    return rows, next_cursor


def get_post(post_id, include_deleted=False):
    conn = get_conn()
    q = _base_query() if not include_deleted else sa.select(*_POST_COLS).select_from(
        _p.join(_u, _p.c.user_id == _u.c.id).join(_c, _p.c.category_id == _c.c.id))
    row = conn.execute(q.where(_p.c.id == post_id)).mappings().first()
    return dict(row) if row else None


def create_post(user_id, category_slug, title, content, post_type="normal",
                is_column=0, column_tag=None, profit_amount=None, thumbnail=None):
    from app.services.badwords import contains_banned_word
    conn = get_conn()
    cat = get_category(category_slug, conn)
    if not cat:
        return None, "bad_category"
    flagged = 1 if contains_banned_word(title) or contains_banned_word(content) else 0
    res = conn.execute(schema.posts.insert().values(
        user_id=user_id, category_id=cat["id"], post_type=post_type,
        is_column=is_column, column_tag=column_tag if is_column else None,
        title=title, content=content, thumbnail=thumbnail,
        profit_amount=profit_amount if post_type == "profit" else None,
        view_count=0, like_count=0, comment_count=0, is_flagged=flagged,
    ))
    conn.commit()
    return res.inserted_primary_key[0], "flagged" if flagged else "ok"


def update_post(post_id, user_id, *, title, content, category_slug=None,
                post_type=None, is_column=None, column_tag=None, profit_amount=None):
    from app.services.badwords import contains_banned_word
    conn = get_conn()
    row = conn.execute(sa.select(_p).where(_p.c.id == post_id, _p.c.deleted_at.is_(None))).mappings().first()
    if not row:
        return "not_found"
    if row["user_id"] != user_id:
        return "forbidden"
    values = dict(title=title, content=content, updated_at=datetime.now())
    if category_slug:
        cat = get_category(category_slug, conn)
        if cat:
            values["category_id"] = cat["id"]
    if post_type:
        values["post_type"] = post_type
        values["profit_amount"] = profit_amount if post_type == "profit" else None
    if is_column is not None:
        values["is_column"] = is_column
        values["column_tag"] = column_tag if is_column else None
    if contains_banned_word(title) or contains_banned_word(content):
        values["is_flagged"] = 1
    conn.execute(sa.update(_p).where(_p.c.id == post_id).values(**values))
    conn.commit()
    return "ok"


def delete_post(post_id, user_id, is_admin=False):
    conn = get_conn()
    row = conn.execute(sa.select(_p.c.user_id).where(
        _p.c.id == post_id, _p.c.deleted_at.is_(None))).mappings().first()
    if not row:
        return "not_found"
    if row["user_id"] != user_id and not is_admin:
        return "forbidden"
    conn.execute(sa.update(_p).where(_p.c.id == post_id).values(deleted_at=datetime.now()))
    conn.commit()
    return "ok"


def list_columns(tag=None, limit=30):
    conn = get_conn()
    ep = schema.expert_profiles
    j = _p.join(_u, _p.c.user_id == _u.c.id).join(_c, _p.c.category_id == _c.c.id) \
        .outerjoin(ep, ep.c.user_id == _u.c.id)
    q = sa.select(*_POST_COLS, ep.c.job_title).select_from(j).where(
        _p.c.deleted_at.is_(None), _p.c.is_column == 1)
    if tag:
        q = q.where(_p.c.column_tag == tag)
    q = q.order_by(_p.c.created_at.desc(), _p.c.id.desc()).limit(limit)
    rows = []
    for r in conn.execute(q).mappings().all():
        d = dict(r)
        d["job_title"] = d.get("job_title") or "전문가"
        rows.append(d)
    return rows


def search_posts(q, limit=30):
    conn = get_conn()
    escaped = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    like = f"%{escaped}%"
    query = _base_query().where(
        sa.or_(_p.c.title.like(like, escape="\\"), _p.c.content.like(like, escape="\\"))
    ).order_by(_p.c.created_at.desc(), _p.c.id.desc()).limit(limit)
    return [dict(r) for r in conn.execute(query).mappings().all()]
