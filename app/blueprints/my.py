import sqlalchemy as sa
from flask import Blueprint, render_template
from flask_login import current_user, login_required

from app.db import schema
from app.db.engine import get_conn

bp = Blueprint("my", __name__)


@bp.get("/my")
@login_required
def index():
    from app.services.home_service import get_rail_data
    conn = get_conn()
    uid = current_user.id
    p, cm, s = schema.posts, schema.comments, schema.scraps
    stats = dict(
        posts=conn.execute(sa.select(sa.func.count()).where(
            p.c.user_id == uid, p.c.deleted_at.is_(None))).scalar_one(),
        comments=conn.execute(sa.select(sa.func.count()).where(
            cm.c.user_id == uid, cm.c.deleted_at.is_(None))).scalar_one(),
        scraps=conn.execute(sa.select(sa.func.count()).where(
            s.c.user_id == uid)).scalar_one(),
    )
    my_posts = [dict(r) for r in conn.execute(
        sa.select(p.c.id, p.c.title).where(p.c.user_id == uid, p.c.deleted_at.is_(None))
        .order_by(p.c.id.desc()).limit(10)).mappings().all()]
    return render_template("my.html", active="my", stats=stats,
                           my_posts=my_posts, **get_rail_data())
