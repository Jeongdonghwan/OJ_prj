"""알림 유형별 on/off 설정. 행이 없으면 전부 켜짐(기본값)."""
import sqlalchemy as sa

from app.db import schema
from app.db.engine import get_conn

_ns = schema.notification_settings

DEFAULTS = dict(on_comment=1, on_reply=1, on_column=1)

# notify() type_ → 설정 컬럼 매핑
TYPE_COLUMN = {"comment": "on_comment", "reply": "on_reply", "column": "on_column"}


def get_settings(user_id, conn=None):
    conn = conn or get_conn()
    row = conn.execute(sa.select(_ns).where(_ns.c.user_id == user_id)).mappings().first()
    if not row:
        return dict(DEFAULTS)
    return {k: row[k] for k in DEFAULTS}


def save_settings(user_id, on_comment, on_reply, on_column):
    conn = get_conn()
    values = dict(on_comment=int(bool(on_comment)), on_reply=int(bool(on_reply)),
                  on_column=int(bool(on_column)))
    existing = conn.execute(sa.select(_ns.c.user_id).where(_ns.c.user_id == user_id)).first()
    if existing:
        conn.execute(sa.update(_ns).where(_ns.c.user_id == user_id).values(**values))
    else:
        conn.execute(_ns.insert().values(user_id=user_id, **values))
    conn.commit()


def is_enabled(user_id, type_, conn=None):
    col = TYPE_COLUMN.get(type_)
    if col is None:
        return True  # 매핑 없는 유형(관리자 공지 등)은 항상 발송
    return bool(get_settings(user_id, conn)[col])
