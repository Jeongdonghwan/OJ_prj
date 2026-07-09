"""배치가 집계해 둔 hot_cache 읽기 전용 조회 (매 요청 계산 금지)."""
import json

import sqlalchemy as sa

from app.db import schema
from app.db.engine import get_conn

HOT_KEY = "hot_posts"
PROFIT_KEY = "profit_board"


def _read_cache(key):
    conn = get_conn()
    row = conn.execute(
        sa.select(schema.hot_cache.c.payload).where(schema.hot_cache.c.cache_key == key)
    ).first()
    if not row:
        return []
    try:
        return json.loads(row[0])
    except (ValueError, TypeError):
        return []


def get_hot_posts():
    return _read_cache(HOT_KEY)


def get_profit_board():
    return _read_cache(PROFIT_KEY)


def write_cache(conn, key, payload):
    existing = conn.execute(
        sa.select(schema.hot_cache.c.cache_key).where(schema.hot_cache.c.cache_key == key)
    ).first()
    data = json.dumps(payload, ensure_ascii=False, default=str)
    if existing:
        conn.execute(sa.update(schema.hot_cache)
                     .where(schema.hot_cache.c.cache_key == key)
                     .values(payload=data))
    else:
        conn.execute(schema.hot_cache.insert().values(cache_key=key, payload=data))
