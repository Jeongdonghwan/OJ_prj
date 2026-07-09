from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.services import post_service

bp = Blueprint("columns", __name__)

VALID_TAGS = {"절세", "내집마련", "연금·노후", "초보투자"}


@bp.get("/columns")
def index():
    from app.services.home_service import get_rail_data
    tag = request.args.get("tag") or None
    if tag and tag not in VALID_TAGS:
        tag = None
    columns = post_service.list_columns(tag=tag)
    return render_template("columns.html", active="column", tag=tag,
                           columns=columns, **get_rail_data())


@bp.route("/expert/apply", methods=["GET", "POST"])
@login_required
def expert_apply():
    from app.services.expert_service import apply as apply_expert, get_profile
    error = None
    if request.method == "POST":
        job_title = (request.form.get("job_title") or "").strip()
        org = (request.form.get("org") or "").strip() or None
        external_link = (request.form.get("external_link") or "").strip() or None
        cert = request.files.get("cert_file")
        if not job_title or not cert or not cert.filename:
            error = "직함과 증빙 파일은 필수입니다"
        else:
            status = apply_expert(current_user.id, job_title, org, external_link, cert)
            if status == "ok":
                return redirect(url_for("my.index"))
            error = {"pending": "이미 심사 중인 신청이 있습니다",
                     "approved": "이미 인증된 전문가입니다",
                     "bad_file": "증빙 파일 형식을 확인해주세요"}.get(status, "신청에 실패했습니다")
    profile = get_profile(current_user.id)
    return render_template("expert_apply.html", active=None, error=error, profile=profile)
