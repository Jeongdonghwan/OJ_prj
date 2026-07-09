from flask import Blueprint, render_template

from app.services import quiz_service

bp = Blueprint("quiz", __name__)


@bp.get("/quiz/archive")
def archive():
    from app.services.home_service import get_rail_data
    quizzes = quiz_service.list_archive()
    return render_template("quiz_archive.html", active=None,
                           quizzes=quizzes, **get_rail_data())
