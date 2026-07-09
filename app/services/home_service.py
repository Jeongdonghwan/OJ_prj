"""홈 화면 데이터 — 배치 캐시/최신 목록만 단순 SELECT (매 요청 계산 금지)."""


def get_home_data():
    # 각 섹션은 해당 단계에서 구현되며, 데이터 없으면 섹션 미노출
    from app.services import quiz_service, poll_service
    quiz = quiz_service.get_today_quiz_view()
    poll = poll_service.get_active_poll_view()
    hot_posts = _hot_posts()
    columns_latest = _columns_latest()
    news_latest = _news_latest()
    rail = get_rail_data(quiz=quiz, poll=poll, hot_posts=hot_posts, news_latest=news_latest)
    return dict(quiz=quiz, poll=poll, hot_posts=hot_posts,
                columns_latest=columns_latest, news_latest=news_latest, **rail)


def _hot_posts():
    from app.services.hot_service import get_hot_posts
    return get_hot_posts()


def _columns_latest(limit=3):
    from app.services.post_service import list_columns
    return list_columns(limit=limit)


def _news_latest(limit=3):
    from app.services.news_service import list_articles
    return list_articles(limit=limit)


def get_rail_data(quiz=None, poll=None, hot_posts=None, news_latest=None):
    """우측 레일 위젯 데이터. 홈이 아닌 페이지에서도 재사용."""
    from app.services import quiz_service, poll_service
    from app.services.hot_service import get_hot_posts, get_profit_board
    from app.services.news_service import list_articles
    from app.services.calendar_service import week_events

    if quiz is None:
        quiz = quiz_service.get_today_quiz_view()
    if poll is None:
        poll = poll_service.get_active_poll_view()
    return dict(
        rail_quiz=quiz,
        rail_poll=poll,
        rail_hot=hot_posts if hot_posts is not None else get_hot_posts(),
        rail_profit=get_profit_board(),
        rail_calendar=week_events(),
        rail_news=news_latest if news_latest is not None else list_articles(limit=3),
    )
