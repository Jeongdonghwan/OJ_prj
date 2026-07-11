"""Expo 푸시: 토큰 등록 + 알림 생성 시 즉시 발송 (§12).

발송 클라이언트는 app.extensions['push_sender']로 주입 — 테스트는 Fake 교체.
발송 실패는 절대 호출 트랜잭션(댓글 작성 등)을 실패시키지 않는다.
"""
from datetime import datetime

import sqlalchemy as sa
from flask import current_app

from app.db import schema
from app.db.engine import get_conn

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"
CHUNK = 100

_pt = schema.push_tokens


def register_token(user_id, token, platform):
    """토큰 기준 upsert — 한 기기는 최근 로그인한 계정으로 재배정."""
    conn = get_conn()
    existing = conn.execute(sa.select(_pt.c.id).where(_pt.c.token == token)).first()
    if existing:
        conn.execute(sa.update(_pt).where(_pt.c.token == token).values(
            user_id=user_id, platform=platform, updated_at=datetime.now()))
    else:
        conn.execute(_pt.insert().values(
            user_id=user_id, token=token, platform=platform, updated_at=datetime.now()))
    conn.commit()


def tokens_for_user(user_id, conn=None):
    conn = conn or get_conn()
    return conn.execute(
        sa.select(_pt.c.token).where(_pt.c.user_id == user_id)).scalars().all()


class ExpoPushSender:
    """실 배포용 — Expo Push API 호출. DeviceNotRegistered 토큰은 정리 대상 반환."""

    def send(self, messages):
        import requests
        dead_tokens = []
        for i in range(0, len(messages), CHUNK):
            chunk = messages[i:i + CHUNK]
            res = requests.post(EXPO_PUSH_URL, json=chunk, timeout=5)
            res.raise_for_status()
            for msg, ticket in zip(chunk, res.json().get("data", [])):
                details = ticket.get("details") or {}
                if details.get("error") == "DeviceNotRegistered":
                    dead_tokens.append(msg["to"])
        return dead_tokens


def get_push_sender(app=None):
    app = app or current_app
    if "push_sender" not in app.extensions:
        app.extensions["push_sender"] = ExpoPushSender()
    return app.extensions["push_sender"]


def push_to_user(user_id, title, body, data=None):
    """토큰 없으면 no-op. 모든 예외는 로깅 후 무시(비차단)."""
    try:
        tokens = tokens_for_user(user_id)
        if not tokens:
            return
        messages = [{"to": t, "title": title, "body": body, "data": data or {}}
                    for t in tokens]
        dead = get_push_sender().send(messages) or []
        if dead:
            conn = get_conn()
            conn.execute(sa.delete(_pt).where(_pt.c.token.in_(dead)))
            conn.commit()
    except Exception as e:  # noqa: BLE001 — 푸시 실패가 본 작업을 막으면 안 됨
        current_app.logger.warning("push failed for user %s: %s", user_id, e)
