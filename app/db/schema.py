"""단일 스키마 소스 — CLAUDE.md §5 DDL + DECISIONS.md D2 추가 컬럼.

MariaDB(프로덕션)와 SQLite(테스트)를 동일 정의로 지원한다 (SQLAlchemy Core).
"""
from datetime import datetime

import sqlalchemy as sa

metadata = sa.MetaData()

MYSQL_KW = dict(mysql_charset="utf8mb4", mysql_collate="utf8mb4_unicode_ci")


def _dt():
    return sa.Column("created_at", sa.DateTime, nullable=False, default=datetime.now)


users = sa.Table(
    "users", metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("email", sa.String(120), unique=True, nullable=True),
    sa.Column("oauth_provider", sa.Enum("kakao", "naver", "email", name="oauth_provider_enum"), nullable=False),
    sa.Column("oauth_id", sa.String(100), nullable=True),
    sa.Column("nickname", sa.String(20), unique=True, nullable=False),
    sa.Column("avatar_no", sa.SmallInteger, nullable=False, default=1),
    sa.Column("profile_img", sa.String(255), nullable=True),
    sa.Column("password_hash", sa.String(255), nullable=True),
    sa.Column("is_verified", sa.SmallInteger, nullable=False, default=0),
    sa.Column("is_admin", sa.SmallInteger, nullable=False, default=0),
    sa.Column("points", sa.Integer, nullable=False, default=0),
    sa.Column("nickname_changed_at", sa.DateTime, nullable=True),
    _dt(),
    sa.Column("last_login_at", sa.DateTime, nullable=True),
    sa.Column("status", sa.Enum("active", "banned", "deleted", name="user_status_enum"),
              nullable=False, default="active"),
    **MYSQL_KW,
)

expert_profiles = sa.Table(
    "expert_profiles", metadata,
    sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), primary_key=True),
    sa.Column("job_title", sa.String(30), nullable=False),
    sa.Column("org", sa.String(50), nullable=True),
    sa.Column("cert_file", sa.String(255), nullable=False),
    sa.Column("external_link", sa.String(255), nullable=True),
    sa.Column("status", sa.Enum("pending", "approved", "rejected", name="expert_status_enum"),
              nullable=False, default="pending"),
    _dt(),
    sa.Column("reviewed_at", sa.DateTime, nullable=True),
    **MYSQL_KW,
)

categories = sa.Table(
    "categories", metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("slug", sa.String(20), unique=True, nullable=False),
    sa.Column("name", sa.String(20), nullable=False),
    sa.Column("sort_order", sa.Integer, nullable=False, default=0),
    **MYSQL_KW,
)

posts = sa.Table(
    "posts", metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
    sa.Column("category_id", sa.Integer, sa.ForeignKey("categories.id"), nullable=False),
    sa.Column("post_type", sa.Enum("normal", "profit", "trade", "question", name="post_type_enum"),
              nullable=False, default="normal"),
    sa.Column("is_column", sa.SmallInteger, nullable=False, default=0),
    sa.Column("column_tag", sa.String(20), nullable=True),
    sa.Column("title", sa.String(100), nullable=False),
    sa.Column("content", sa.Text, nullable=False),
    sa.Column("thumbnail", sa.String(255), nullable=True),
    sa.Column("profit_amount", sa.BigInteger, nullable=True),
    sa.Column("view_count", sa.Integer, nullable=False, default=0),
    sa.Column("like_count", sa.Integer, nullable=False, default=0),
    sa.Column("comment_count", sa.Integer, nullable=False, default=0),
    sa.Column("is_flagged", sa.SmallInteger, nullable=False, default=0),
    _dt(),
    sa.Column("updated_at", sa.DateTime, nullable=True),
    sa.Column("deleted_at", sa.DateTime, nullable=True),
    sa.Index("ix_posts_cat_created", "category_id", "created_at"),
    sa.Index("ix_posts_column_created", "is_column", "created_at"),
    **MYSQL_KW,
)

post_images = sa.Table(
    "post_images", metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("post_id", sa.Integer, sa.ForeignKey("posts.id"), nullable=False),
    sa.Column("path", sa.String(255), nullable=False),
    sa.Column("sort_order", sa.Integer, nullable=False, default=0),
    **MYSQL_KW,
)

comments = sa.Table(
    "comments", metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("post_id", sa.Integer, sa.ForeignKey("posts.id"), nullable=False),
    sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
    sa.Column("parent_id", sa.Integer, sa.ForeignKey("comments.id"), nullable=True),
    sa.Column("content", sa.Text, nullable=False),
    _dt(),
    sa.Column("deleted_at", sa.DateTime, nullable=True),
    **MYSQL_KW,
)

reactions = sa.Table(
    "reactions", metadata,
    sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), primary_key=True),
    sa.Column("target_type", sa.Enum("post", "comment", "news", name="reaction_target_enum"),
              primary_key=True),
    sa.Column("target_id", sa.Integer, primary_key=True),
    **MYSQL_KW,
)

scraps = sa.Table(
    "scraps", metadata,
    sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), primary_key=True),
    sa.Column("post_id", sa.Integer, sa.ForeignKey("posts.id"), primary_key=True),
    **MYSQL_KW,
)

follows = sa.Table(
    "follows", metadata,
    sa.Column("follower_id", sa.Integer, sa.ForeignKey("users.id"), primary_key=True),
    sa.Column("followee_id", sa.Integer, sa.ForeignKey("users.id"), primary_key=True),
    **MYSQL_KW,
)

notifications = sa.Table(
    "notifications", metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
    sa.Column("type", sa.String(20), nullable=False),
    sa.Column("ref_id", sa.Integer, nullable=True),
    sa.Column("message", sa.String(200), nullable=False),
    sa.Column("is_read", sa.SmallInteger, nullable=False, default=0),
    _dt(),
    **MYSQL_KW,
)

reports = sa.Table(
    "reports", metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("reporter_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
    sa.Column("target_type", sa.Enum("post", "comment", "news", name="report_target_enum"),
              nullable=False),
    sa.Column("target_id", sa.Integer, nullable=False),
    sa.Column("reason", sa.String(200), nullable=False),
    sa.Column("status", sa.Enum("pending", "resolved", "dismissed", name="report_status_enum"),
              nullable=False, default="pending"),
    _dt(),
    **MYSQL_KW,
)

quizzes = sa.Table(
    "quizzes", metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("quiz_date", sa.Date, unique=True, nullable=False),
    sa.Column("question", sa.Text, nullable=False),
    sa.Column("choice1", sa.String(100), nullable=False),
    sa.Column("choice2", sa.String(100), nullable=False),
    sa.Column("choice3", sa.String(100), nullable=True),
    sa.Column("choice4", sa.String(100), nullable=True),
    sa.Column("answer_no", sa.SmallInteger, nullable=False),
    sa.Column("explanation", sa.Text, nullable=False),
    sa.Column("created_by", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
    **MYSQL_KW,
)

quiz_attempts = sa.Table(
    "quiz_attempts", metadata,
    sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), primary_key=True),
    sa.Column("quiz_id", sa.Integer, sa.ForeignKey("quizzes.id"), primary_key=True),
    sa.Column("choice_no", sa.SmallInteger, nullable=False),
    sa.Column("is_correct", sa.SmallInteger, nullable=False),
    _dt(),
    **MYSQL_KW,
)

point_logs = sa.Table(
    "point_logs", metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
    sa.Column("amount", sa.Integer, nullable=False),
    sa.Column("reason", sa.Enum("quiz", "attendance", "vote", "post", "admin", name="point_reason_enum"),
              nullable=False),
    _dt(),
    **MYSQL_KW,
)

polls = sa.Table(
    "polls", metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("question", sa.String(100), nullable=False),
    sa.Column("option_up", sa.String(20), nullable=False),
    sa.Column("option_down", sa.String(20), nullable=False),
    sa.Column("starts_at", sa.DateTime, nullable=False),
    sa.Column("ends_at", sa.DateTime, nullable=False),
    sa.Column("is_active", sa.SmallInteger, nullable=False, default=1),
    **MYSQL_KW,
)

poll_votes = sa.Table(
    "poll_votes", metadata,
    sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), primary_key=True),
    sa.Column("poll_id", sa.Integer, sa.ForeignKey("polls.id"), primary_key=True),
    sa.Column("side", sa.Enum("up", "down", name="poll_side_enum"), nullable=False),
    _dt(),
    **MYSQL_KW,
)

news_articles = sa.Table(
    "news_articles", metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("source", sa.String(30), nullable=False),
    sa.Column("title", sa.String(200), nullable=False),
    sa.Column("summary", sa.String(300), nullable=True),
    sa.Column("url", sa.String(500), unique=True, nullable=False),
    sa.Column("thumbnail", sa.String(500), nullable=True),
    sa.Column("category", sa.Enum("realestate", "stock", "coin", "policy", name="news_category_enum"),
              nullable=False),
    sa.Column("published_at", sa.DateTime, nullable=False),
    sa.Column("comment_count", sa.Integer, nullable=False, default=0),
    sa.Index("ix_news_cat_pub", "category", "published_at"),
    **MYSQL_KW,
)

news_comments = sa.Table(
    "news_comments", metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("news_id", sa.Integer, sa.ForeignKey("news_articles.id"), nullable=False),
    sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
    sa.Column("parent_id", sa.Integer, sa.ForeignKey("news_comments.id"), nullable=True),
    sa.Column("content", sa.Text, nullable=False),
    _dt(),
    sa.Column("deleted_at", sa.DateTime, nullable=True),
    **MYSQL_KW,
)

daily_briefings = sa.Table(
    "daily_briefings", metadata,
    sa.Column("brief_date", sa.Date, primary_key=True),
    sa.Column("content", sa.String(500), nullable=False),
    **MYSQL_KW,
)

calendar_events = sa.Table(
    "calendar_events", metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("event_date", sa.Date, nullable=False),
    sa.Column("title", sa.String(60), nullable=False),
    sa.Column("is_hot", sa.SmallInteger, nullable=False, default=0),
    sa.Index("ix_calendar_date", "event_date"),
    **MYSQL_KW,
)

ad_slots = sa.Table(
    "ad_slots", metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("position", sa.Enum("wing_l", "wing_r", "rail", "native_feed", name="ad_position_enum"),
              nullable=False),
    sa.Column("image_path", sa.String(255), nullable=False),
    sa.Column("link_url", sa.String(500), nullable=False),
    sa.Column("starts_at", sa.DateTime, nullable=False),
    sa.Column("ends_at", sa.DateTime, nullable=False),
    sa.Column("is_active", sa.SmallInteger, nullable=False, default=1),
    **MYSQL_KW,
)

notification_settings = sa.Table(
    "notification_settings", metadata,
    sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), primary_key=True),
    sa.Column("on_comment", sa.SmallInteger, nullable=False, default=1),
    sa.Column("on_reply", sa.SmallInteger, nullable=False, default=1),
    sa.Column("on_column", sa.SmallInteger, nullable=False, default=1),
    **MYSQL_KW,
)

push_tokens = sa.Table(
    "push_tokens", metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
    sa.Column("token", sa.String(200), unique=True, nullable=False),
    sa.Column("platform", sa.Enum("ios", "android", name="push_platform_enum"), nullable=False),
    sa.Column("updated_at", sa.DateTime, nullable=False, default=datetime.now),
    **MYSQL_KW,
)

hot_cache = sa.Table(
    "hot_cache", metadata,
    sa.Column("cache_key", sa.String(40), primary_key=True),
    sa.Column("payload", sa.Text, nullable=False),
    sa.Column("updated_at", sa.DateTime, nullable=False, default=datetime.now),
    **MYSQL_KW,
)
