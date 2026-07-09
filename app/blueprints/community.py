from flask import Blueprint, abort, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import limiter
from app.services import comment_service, interaction_service, post_service

bp = Blueprint("community", __name__)

VALID_SORTS = {"latest", "hot", "expert", "profit", "trade"}


@bp.get("/community")
def index():
    from app.services.home_service import get_rail_data
    from app.services.poll_service import get_active_poll_view
    cat = request.args.get("cat") or None
    sort = request.args.get("sort") or "latest"
    if sort not in VALID_SORTS:
        sort = "latest"
    posts, next_cursor = post_service.list_posts(cat=cat, sort=sort)
    if current_user.is_authenticated:
        for p in posts:
            p["liked"] = interaction_service.has_liked(current_user.id, "post", p["id"])
    poll = get_active_poll_view()
    rail = get_rail_data(poll=poll)
    return render_template("community.html", active="community",
                           categories=post_service.list_categories(),
                           cat=cat, sort=sort, posts=posts, next_cursor=next_cursor,
                           poll=poll, **rail)


@bp.get("/post/<int:post_id>")
def post_detail(post_id):
    from app.services.home_service import get_rail_data
    post = post_service.get_post(post_id)
    if not post:
        abort(404)
    interaction_service.count_view(post_id)
    post["view_count"] += 1  # 방금 증가분 반영(재조회 절약)
    post["liked"] = post["scrapped"] = post["following"] = False
    if current_user.is_authenticated:
        post["liked"] = interaction_service.has_liked(current_user.id, "post", post_id)
        post["scrapped"] = interaction_service.has_scrapped(current_user.id, post_id)
        post["following"] = interaction_service.is_following(current_user.id, post["user_id"])
    post["images"] = _post_images(post_id)
    comments = comment_service.list_comments(post_id)
    return render_template("post_detail.html", active="community",
                           post=post, comments=comments, **get_rail_data())


def _post_images(post_id):
    import sqlalchemy as sa
    from app.db import schema
    from app.db.engine import get_conn
    rows = get_conn().execute(
        sa.select(schema.post_images).where(schema.post_images.c.post_id == post_id)
        .order_by(schema.post_images.c.sort_order)
    ).mappings().all()
    return [dict(r) for r in rows]


@bp.route("/write", methods=["GET", "POST"])
@limiter.limit("2 per minute", methods=["POST"])
@login_required
def write():
    from app.services.upload import save_post_images

    edit_id = request.args.get("edit", type=int)
    edit_post = None
    if edit_id:
        edit_post = post_service.get_post(edit_id)
        if not edit_post or edit_post["user_id"] != current_user.id:
            abort(403)

    if request.method == "POST":
        return _handle_write(save_post_images)

    return render_template("write.html", active=None, edit_post=edit_post,
                           is_expert=bool(current_user.is_verified))


def _handle_write(save_post_images):
    title = (request.form.get("title") or "").strip()
    content = (request.form.get("content") or "").strip()
    category = request.form.get("category") or "free"
    post_type = request.form.get("post_type") or "normal"
    if post_type not in ("normal", "profit", "trade", "question"):
        post_type = "normal"
    profit_amount = request.form.get("profit_amount", type=int)
    column_tag = (request.form.get("column_tag") or "").strip() or None
    is_column = 1 if (column_tag and current_user.is_verified) else 0
    if not title or not content:
        abort(400)

    post_id = request.form.get("post_id", type=int)
    if post_id:
        status = post_service.update_post(
            post_id, current_user.id, title=title, content=content,
            category_slug=category, post_type=post_type,
            is_column=is_column, column_tag=column_tag, profit_amount=profit_amount)
        if status == "forbidden":
            abort(403)
        if status == "not_found":
            abort(404)
        save_post_images(post_id, request.files.getlist("images"))
        return redirect(url_for("community.post_detail", post_id=post_id))

    new_id, status = post_service.create_post(
        current_user.id, category, title, content, post_type=post_type,
        is_column=is_column, column_tag=column_tag, profit_amount=profit_amount)
    if new_id is None:
        abort(400)
    save_post_images(new_id, request.files.getlist("images"))
    if is_column:
        _notify_followers_new_column(new_id, title)
    return redirect(url_for("community.post_detail", post_id=new_id))


def _notify_followers_new_column(post_id, title):
    import sqlalchemy as sa
    from app.db import schema
    from app.db.engine import get_conn
    from app.services.notification_service import notify
    conn = get_conn()
    followers = conn.execute(
        sa.select(schema.follows.c.follower_id)
        .where(schema.follows.c.followee_id == current_user.id)
    ).scalars().all()
    for fid in followers:
        notify(fid, "column", post_id,
               f"{current_user.nickname}님의 새 칼럼: {title[:30]}", conn=conn, commit=False)
    conn.commit()


@bp.post("/post/<int:post_id>/delete")
@login_required
def delete_post(post_id):
    status = post_service.delete_post(post_id, current_user.id,
                                      is_admin=bool(current_user.is_admin))
    if status == "forbidden":
        abort(403)
    if status == "not_found":
        abort(404)
    return redirect(url_for("community.index"))


@bp.post("/post/<int:post_id>/comment")
@login_required
@limiter.limit("5 per minute")
def add_comment(post_id):
    content = (request.form.get("content") or "").strip()
    parent_id = request.form.get("parent_id", type=int) or None
    if not content:
        abort(400)
    status, _cid = comment_service.add_comment(post_id, current_user.id, content, parent_id)
    if status == "not_found":
        abort(404)
    if status == "bad_parent":
        abort(400)
    return redirect(url_for("community.post_detail", post_id=post_id))


@bp.post("/comment/<int:comment_id>/delete")
@login_required
def delete_comment(comment_id):
    status = comment_service.delete_comment(comment_id, current_user.id,
                                            is_admin=bool(current_user.is_admin))
    if status == "forbidden":
        abort(403)
    if status == "not_found":
        abort(404)
    return redirect(request.referrer or url_for("community.index"))
