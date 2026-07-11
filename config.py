import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///ojae_dev.db")
    UPLOAD_DIR = BASE_DIR / "app" / "static" / "uploads"
    MAX_CONTENT_LENGTH = 60 * 1024 * 1024  # 10장 x 5MB + 여유
    MAX_IMAGE_SIZE = 5 * 1024 * 1024
    MAX_IMAGES_PER_POST = 10
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URI = "memory://"
    KAKAO_CLIENT_ID = os.environ.get("KAKAO_CLIENT_ID", "")
    KAKAO_CLIENT_SECRET = os.environ.get("KAKAO_CLIENT_SECRET", "")
    KAKAO_REDIRECT_URI = os.environ.get("KAKAO_REDIRECT_URI", "")
    NAVER_CLIENT_ID = os.environ.get("NAVER_CLIENT_ID", "")
    NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET", "")
    NAVER_REDIRECT_URI = os.environ.get("NAVER_REDIRECT_URI", "")
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")


class DevConfig(Config):
    DEBUG = True


class ProdConfig(Config):
    SESSION_COOKIE_SECURE = True
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 24 * 30  # 30일 (앱 WebView 재로그인 최소화)


class TestConfig(Config):
    TESTING = True
    DATABASE_URL = "sqlite://"
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False
    SECRET_KEY = "test-secret"
