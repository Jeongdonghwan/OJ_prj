import sqlalchemy as sa
from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import current_user, login_required, logout_user

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


@bp.route("/my/profile", methods=["GET", "POST"])
@login_required
def profile():
    from app.services import user_service
    from app.services.upload import UploadError, save_image
    error = message = None
    if request.method == "POST":
        photo = request.files.get("photo")
        if photo and photo.filename:
            try:
                _body, thumb = save_image(photo)
                user_service.update_profile_img(current_user.id, thumb)
                message = "프로필 사진이 변경되었습니다"
            except UploadError:
                error = "사진 파일을 확인해주세요 (jpg/png/webp, 5MB 이하)"
        new_nickname = (request.form.get("nickname") or "").strip()
        if not error and new_nickname and new_nickname != current_user.nickname:
            if not (2 <= len(new_nickname) <= 12):
                error = "닉네임은 2~12자로 입력해주세요"
            else:
                status = user_service.change_nickname(current_user.id, new_nickname)
                if status == "too_soon":
                    error = "닉네임은 30일에 1번만 변경할 수 있어요"
                elif status == "nickname_taken":
                    error = "이미 사용 중인 닉네임입니다"
                else:
                    message = "닉네임이 변경되었습니다"
        if not error and not message:
            message = "변경 사항이 없습니다"
    return render_template("my_profile.html", active=None, error=error, message=message)


@bp.route("/my/settings", methods=["GET", "POST"])
@login_required
def settings():
    from app.services.settings_service import get_settings, save_settings
    message = None
    if request.method == "POST":
        save_settings(current_user.id,
                      on_comment=request.form.get("on_comment"),
                      on_reply=request.form.get("on_reply"),
                      on_column=request.form.get("on_column"))
        message = "알림 설정이 저장되었습니다"
    return render_template("my_settings.html", active=None,
                           settings=get_settings(current_user.id), message=message)


@bp.route("/my/withdraw", methods=["GET", "POST"])
@login_required
def withdraw():
    from app.services import user_service
    if request.method == "POST":
        user_service.withdraw(current_user.id)
        logout_user()
        return redirect(url_for("main.home"))
    return render_template("my_withdraw.html", active=None)
