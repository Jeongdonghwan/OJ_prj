from flask import Blueprint, render_template, request
from flask_login import login_required

bp = Blueprint("main", __name__)


@bp.get("/health")
def health():
    return {"ok": True}


@bp.get("/")
def home():
    from app.services.home_service import get_home_data
    data = get_home_data()
    return render_template("home.html", active="home", **data)


@bp.get("/policy")
def policy():
    return render_template("policy.html", active=None)


@bp.get("/terms")
def terms():
    return render_template("terms.html", active=None)


@bp.get("/search")
def search():
    from app.services.post_service import search_posts
    q = (request.args.get("q") or "").strip()
    posts = search_posts(q) if q else []
    return render_template("search.html", active=None, q=q, posts=posts)


@bp.get("/notifications")
@login_required
def notifications():
    from app.services.notification_service import list_notifications, mark_all_read
    from flask_login import current_user
    items = list_notifications(current_user.id)
    mark_all_read(current_user.id)
    return render_template("notifications.html", active=None, notifications=items)
