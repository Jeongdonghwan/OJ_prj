"""관리자: 퀴즈/투표/캘린더 등록, 전문가 심사, 신고 처리, 플래그 글 검토."""
from datetime import datetime

import sqlalchemy as sa
from flask import Blueprint, abort, redirect, render_template, request, url_for
from flask_login import current_user

from app.db import schema
from app.db.engine import get_conn

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.before_request
def require_admin():
    if not current_user.is_authenticated:
        abort(403)
    if not current_user.is_admin:
        abort(403)


@bp.get("/")
def dashboard():
    conn = get_conn()
    counts = dict(
        pending_experts=conn.execute(sa.select(sa.func.count()).where(
            schema.expert_profiles.c.status == "pending")).scalar_one(),
        pending_reports=conn.execute(sa.select(sa.func.count()).where(
            schema.reports.c.status == "pending")).scalar_one(),
        flagged_posts=conn.execute(sa.select(sa.func.count()).where(
            schema.posts.c.is_flagged == 1, schema.posts.c.deleted_at.is_(None))).scalar_one(),
    )
    return render_template("admin/dashboard.html", counts=counts)


@bp.route("/quiz", methods=["GET", "POST"])
def quiz():
    conn = get_conn()
    error = None
    if request.method == "POST":
        f = request.form
        try:
            conn.execute(schema.quizzes.insert().values(
                quiz_date=datetime.strptime(f["quiz_date"], "%Y-%m-%d").date(),
                question=f["question"].strip(),
                choice1=f["choice1"].strip(), choice2=f["choice2"].strip(),
                choice3=(f.get("choice3") or "").strip() or None,
                choice4=(f.get("choice4") or "").strip() or None,
                answer_no=int(f["answer_no"]),
                explanation=f["explanation"].strip(),
                created_by=current_user.id,
            ))
            conn.commit()
            return redirect(url_for("admin.quiz"))
        except sa.exc.IntegrityError:
            conn.rollback()
            error = "해당 날짜에 이미 퀴즈가 있습니다"
        except (KeyError, ValueError):
            error = "입력값을 확인해주세요"
    quizzes = conn.execute(sa.select(schema.quizzes)
                           .order_by(schema.quizzes.c.quiz_date.desc()).limit(30)).mappings().all()
    return render_template("admin/quiz.html", quizzes=quizzes, error=error)


@bp.route("/poll", methods=["GET", "POST"])
def poll():
    conn = get_conn()
    error = None
    if request.method == "POST":
        f = request.form
        try:
            conn.execute(schema.polls.insert().values(
                question=f["question"].strip(),
                option_up=f["option_up"].strip(), option_down=f["option_down"].strip(),
                starts_at=datetime.fromisoformat(f["starts_at"]),
                ends_at=datetime.fromisoformat(f["ends_at"]),
                is_active=1,
            ))
            conn.commit()
            return redirect(url_for("admin.poll"))
        except (KeyError, ValueError):
            error = "입력값을 확인해주세요"
    polls = conn.execute(sa.select(schema.polls)
                         .order_by(schema.polls.c.id.desc()).limit(30)).mappings().all()
    return render_template("admin/poll.html", polls=polls, error=error)


@bp.route("/calendar", methods=["GET", "POST"])
def calendar():
    conn = get_conn()
    error = None
    if request.method == "POST":
        f = request.form
        try:
            conn.execute(schema.calendar_events.insert().values(
                event_date=datetime.strptime(f["event_date"], "%Y-%m-%d").date(),
                title=f["title"].strip(),
                is_hot=1 if f.get("is_hot") else 0,
            ))
            conn.commit()
            return redirect(url_for("admin.calendar"))
        except (KeyError, ValueError):
            error = "입력값을 확인해주세요"
    events = conn.execute(sa.select(schema.calendar_events)
                          .order_by(schema.calendar_events.c.event_date.desc()).limit(30)).mappings().all()
    return render_template("admin/calendar.html", events=events, error=error)


@bp.route("/experts", methods=["GET", "POST"])
def experts():
    from app.services.expert_service import list_pending, review
    if request.method == "POST":
        user_id = request.form.get("user_id", type=int)
        approve = request.form.get("action") == "approve"
        review(user_id, approve)
        return redirect(url_for("admin.experts"))
    return render_template("admin/experts.html", pending=list_pending())


@bp.route("/reports", methods=["GET", "POST"])
def reports():
    conn = get_conn()
    if request.method == "POST":
        report_id = request.form.get("report_id", type=int)
        action = request.form.get("action")
        status = "resolved" if action == "resolve" else "dismissed"
        conn.execute(sa.update(schema.reports).where(schema.reports.c.id == report_id)
                     .values(status=status))
        conn.commit()
        return redirect(url_for("admin.reports"))
    rows = conn.execute(
        sa.select(schema.reports).where(schema.reports.c.status == "pending")
        .order_by(schema.reports.c.id)).mappings().all()
    return render_template("admin/reports.html", reports=rows)


@bp.route("/flagged", methods=["GET", "POST"])
def flagged():
    conn = get_conn()
    if request.method == "POST":
        post_id = request.form.get("post_id", type=int)
        action = request.form.get("action")
        if action == "clear":
            conn.execute(sa.update(schema.posts).where(schema.posts.c.id == post_id)
                         .values(is_flagged=0))
        elif action == "delete":
            conn.execute(sa.update(schema.posts).where(schema.posts.c.id == post_id)
                         .values(deleted_at=datetime.now()))
        conn.commit()
        return redirect(url_for("admin.flagged"))
    rows = conn.execute(
        sa.select(schema.posts).where(
            schema.posts.c.is_flagged == 1, schema.posts.c.deleted_at.is_(None))
        .order_by(schema.posts.c.id.desc())).mappings().all()
    return render_template("admin/flagged.html", posts=rows)
