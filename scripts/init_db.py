"""DB 스키마 생성 + 카테고리 시드. 사용: python -m scripts.init_db"""
import sqlalchemy as sa

from app import create_app
from app.db import schema
from app.db.engine import get_engine
from config import DevConfig

CATEGORY_SEED = [
    ("realestate", "부동산", 1),
    ("stock", "주식", 2),
    ("coin", "코인", 3),
    ("fund", "펀드·ETF", 4),
    ("saving", "예적금·절약", 5),
    ("free", "자유수다", 6),
]


def init_db(app=None):
    app = app or create_app(DevConfig)
    with app.app_context():
        engine = get_engine(app)
        schema.metadata.create_all(engine)
        with engine.begin() as conn:
            for slug, name, order in CATEGORY_SEED:
                exists = conn.execute(sa.select(schema.categories.c.id)
                                      .where(schema.categories.c.slug == slug)).first()
                if not exists:
                    conn.execute(schema.categories.insert().values(
                        slug=slug, name=name, sort_order=order))
    print("DB 초기화 완료 (스키마 + 카테고리 6종)")


if __name__ == "__main__":
    init_db()
