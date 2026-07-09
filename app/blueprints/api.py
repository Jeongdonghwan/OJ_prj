"""AJAX API: 커서 피드, 도움됐어요/스크랩/팔로우 토글, 퀴즈/투표 응답, 신고, 뉴스 댓글."""
from flask import Blueprint, abort, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import limiter
from app.services import interaction_service, post_service

bp = Blueprint("api", __name__, url_prefix="/api")


def _login_required_json():
    if not current_user.is_authenticated:
        abort(jsonify(error="login_required"), 401)


@bp.get("/posts")
def posts():
    cat = request.args.get("cat") or None
    sort = request.args.get("sort") or "latest"
    cursor = request.args.get("cursor") or None
    items, next_cursor = post_service.list_posts(cat=cat, sort=sort, cursor=cursor)
    if current_user.is_authenticated:
        for p in items:
            p["liked"] = interaction_service.has_liked(current_user.id, "post", p["id"])
    html = [render_template("_post_card.html", p=p) for p in items]
    return jsonify(items=html, next_cursor=next_cursor)


@bp.post("/like")
def like():
    if not current_user.is_authenticated:
        return jsonify(error="login_required"), 401
    data = request.get_json(silent=True) or {}
    post_id = data.get("post_id")
    if not post_id or not post_service.get_post(post_id):
        return jsonify(error="not_found"), 404
    on, count = interaction_service.toggle_like(current_user.id, "post", post_id)
    return jsonify(on=on, count=count)


@bp.post("/scrap")
def scrap():
    if not current_user.is_authenticated:
        return jsonify(error="login_required"), 401
    data = request.get_json(silent=True) or {}
    post_id = data.get("post_id")
    if not post_id or not post_service.get_post(post_id):
        return jsonify(error="not_found"), 404
    on = interaction_service.toggle_scrap(current_user.id, post_id)
    return jsonify(on=on)


@bp.post("/follow")
def follow():
    if not current_user.is_authenticated:
        return jsonify(error="login_required"), 401
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    if not user_id:
        return jsonify(error="bad_request"), 400
    status, on = interaction_service.toggle_follow(current_user.id, int(user_id))
    if status == "self":
        return jsonify(error="self_follow"), 400
    return jsonify(on=on)


@bp.post("/quiz/answer")
def quiz_answer():
    from app.services.quiz_service import answer_quiz
    if not current_user.is_authenticated:
        return jsonify(error="login_required"), 401
    data = request.get_json(silent=True) or {}
    quiz_id, choice_no = data.get("quiz_id"), data.get("choice_no")
    if not quiz_id or not choice_no:
        return jsonify(error="bad_request"), 400
    status, result = answer_quiz(current_user.id, int(quiz_id), int(choice_no))
    if status == "duplicate":
        return jsonify(error="already_answered"), 409
    if status == "not_found":
        return jsonify(error="not_found"), 404
    return jsonify(**result)


@bp.post("/poll/vote")
def poll_vote():
    from app.services.poll_service import vote
    if not current_user.is_authenticated:
        return jsonify(error="login_required"), 401
    data = request.get_json(silent=True) or {}
    poll_id, side = data.get("poll_id"), data.get("side")
    if not poll_id or side not in ("up", "down"):
        return jsonify(error="bad_request"), 400
    status, result = vote(current_user.id, int(poll_id), side)
    if status == "duplicate":
        return jsonify(error="already_voted"), 409
    if status == "not_found":
        return jsonify(error="not_found"), 404
    if status == "bad_request":
        return jsonify(error="bad_request"), 400
    return jsonify(**result)


@bp.post("/report")
def report():
    from app.db import schema
    from app.db.engine import get_conn
    if not current_user.is_authenticated:
        return jsonify(error="login_required"), 401
    data = request.get_json(silent=True) or {}
    target_type = data.get("target_type")
    target_id = data.get("target_id")
    reason = (data.get("reason") or "").strip()
    if target_type not in ("post", "comment", "news") or not target_id or not reason:
        return jsonify(error="bad_request"), 400
    conn = get_conn()
    conn.execute(schema.reports.insert().values(
        reporter_id=current_user.id, target_type=target_type,
        target_id=int(target_id), reason=reason[:200], status="pending"))
    conn.commit()
    return jsonify(ok=True)


@bp.post("/news/<int:news_id>/comment")
@limiter.limit("5 per minute")
@login_required
def news_comment(news_id):
    from app.services.news_comment_service import add_news_comment
    content = (request.form.get("content") or "").strip()
    if not content:
        abort(400)
    status, _ = add_news_comment(news_id, current_user.id, content)
    if status == "not_found":
        abort(404)
    return redirect(url_for("news.detail", news_id=news_id))
