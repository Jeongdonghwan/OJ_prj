from flask import Flask

from config import Config


def create_app(config_object=None):
    app = Flask(__name__)
    app.config.from_object(config_object or Config)

    from app.db import engine as db_engine
    db_engine.init_app(app)

    from app.extensions import csrf, limiter, login_manager
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    limiter.enabled = app.config.get("RATELIMIT_ENABLED", True)

    from app.services.auth_service import init_login
    init_login(login_manager)

    from app.utils import register_template_helpers
    register_template_helpers(app)

    from app.blueprints import register_blueprints
    register_blueprints(app)

    _register_attendance_hook(app)

    return app


def _register_attendance_hook(app):
    """로그인 사용자의 하루 첫 접속 시 출석 +2P (§6)."""
    from flask import request, session
    from flask_login import current_user

    @app.before_request
    def attendance():
        if request.endpoint in (None, "static") or request.path.startswith("/static"):
            return
        if not current_user.is_authenticated:
            return
        from datetime import date
        today = date.today().isoformat()
        if session.get("att_date") == today:
            return
        from app.services.point_service import award_attendance
        award_attendance(current_user.id)
        session["att_date"] = today
