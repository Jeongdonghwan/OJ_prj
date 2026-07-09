from flask import Blueprint, abort, render_template, request

from app.services import news_service

bp = Blueprint("news", __name__)

VALID_CATS = {"realestate", "stock", "coin", "policy"}


@bp.get("/news")
def index():
    from app.services.home_service import get_rail_data
    category = request.args.get("category") or None
    if category and category not in VALID_CATS:
        category = None
    articles = news_service.list_articles(category=category)
    briefing = news_service.get_today_briefing()
    return render_template("news.html", active="news", category=category,
                           articles=articles, briefing=briefing, **get_rail_data())


@bp.get("/news/<int:news_id>")
def detail(news_id):
    from app.services.home_service import get_rail_data
    from app.services.news_comment_service import list_news_comments
    article = news_service.get_article(news_id)
    if not article:
        abort(404)
    comments = list_news_comments(news_id)
    return render_template("news_detail.html", active="news",
                           article=article, comments=comments, **get_rail_data())
