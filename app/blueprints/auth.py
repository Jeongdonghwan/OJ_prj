from flask import Blueprint, current_app, redirect, render_template, request, url_for
from flask_login import login_required, login_user, logout_user

from app.extensions import limiter
from app.services import user_service
from app.services.auth_service import User, get_user_by_id
from app.services.oauth import get_kakao_client

bp = Blueprint("auth", __name__)


@bp.get("/login")
def login():
    return render_template("login.html", active=None)


@bp.get("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.home"))


@bp.route("/auth/email/signup", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def email_signup():
    error = None
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        nickname = (request.form.get("nickname") or "").strip()
        if not email or len(password) < 8 or not (2 <= len(nickname) <= 12):
            error = "입력값을 확인해주세요 (비밀번호 8자 이상, 닉네임 2~12자)"
        else:
            uid, status = user_service.create_email_user(email, password, nickname)
            if status == "email_taken":
                error = "이미 가입된 이메일입니다"
            elif status == "nickname_taken":
                error = "이미 사용 중인 닉네임입니다"
            else:
                login_user(get_user_by_id(uid))
                user_service.touch_last_login(uid)
                return redirect(url_for("main.home"))
    return render_template("email_auth.html", active=None, mode="signup", error=error,
                           form_email=request.form.get("email"),
                           form_nickname=request.form.get("nickname"))


@bp.route("/auth/email/login", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def email_login():
    error = None
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        row = user_service.verify_email_login(email, password)
        if row and row["status"] == "active":
            login_user(User(row))
            user_service.touch_last_login(row["id"])
            nxt = request.args.get("next")
            if nxt and nxt.startswith("/"):
                return redirect(nxt)
            return redirect(url_for("main.home"))
        error = "이메일 또는 비밀번호가 올바르지 않습니다"
    return render_template("email_auth.html", active=None, mode="login", error=error,
                           form_email=request.form.get("email"))


@bp.get("/auth/kakao")
def kakao_start():
    client = get_kakao_client(current_app)
    return redirect(client.get_authorize_url())


@bp.get("/auth/kakao/callback")
def kakao_callback():
    code = request.args.get("code")
    if not code:
        return redirect(url_for("auth.login"))
    client = get_kakao_client(current_app)
    token = client.exchange_token(code)
    profile = client.get_profile(token)
    row, created = user_service.get_or_create_kakao_user(profile)
    login_user(User(row))
    user_service.touch_last_login(row["id"])
    return redirect(url_for("main.home"))
