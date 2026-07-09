"""User 모델(Flask-Login용) + 사용자 조회/생성."""
import sqlalchemy as sa
from flask_login import UserMixin

from app.db import schema
from app.db.engine import get_conn


class User(UserMixin):
    def __init__(self, row):
        self._row = dict(row)

    def __getattr__(self, name):
        try:
            return self._row[name]
        except KeyError:
            raise AttributeError(name)

    def get_id(self):
        return str(self._row["id"])

    @property
    def is_active(self):
        return self._row.get("status") == "active"


def get_user_by_id(user_id):
    conn = get_conn()
    row = conn.execute(
        sa.select(schema.users).where(schema.users.c.id == int(user_id))
    ).mappings().first()
    return User(row) if row else None


def init_login(login_manager):
    @login_manager.user_loader
    def load_user(user_id):
        user = get_user_by_id(user_id)
        if user and user.is_active:
            return user
        return None
