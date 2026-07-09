"""전문가 인증 신청/심사."""
import secrets
from datetime import datetime
from pathlib import Path

import sqlalchemy as sa
from flask import current_app

from app.db import schema
from app.db.engine import get_conn

_ep, _u = schema.expert_profiles, schema.users

CERT_ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".pdf"}


def get_profile(user_id, conn=None):
    conn = conn or get_conn()
    row = conn.execute(sa.select(_ep).where(_ep.c.user_id == user_id)).mappings().first()
    return dict(row) if row else None


def _save_cert(file_storage):
    ext = Path((file_storage.filename or "").lower()).suffix
    if ext not in CERT_ALLOWED_EXT:
        return None
    rel_dir = Path("certs")
    abs_dir = Path(current_app.config["UPLOAD_DIR"]) / rel_dir
    abs_dir.mkdir(parents=True, exist_ok=True)
    fname = f"{secrets.token_hex(12)}{ext}"
    file_storage.save(abs_dir / fname)
    return f"/static/uploads/certs/{fname}"


def apply(user_id, job_title, org, external_link, cert_file):
    conn = get_conn()
    existing = get_profile(user_id, conn)
    if existing and existing["status"] in ("pending", "approved"):
        return existing["status"]
    path = _save_cert(cert_file)
    if not path:
        return "bad_file"
    if existing:  # rejected → 재신청
        conn.execute(sa.update(_ep).where(_ep.c.user_id == user_id).values(
            job_title=job_title, org=org, cert_file=path,
            external_link=external_link, status="pending", reviewed_at=None))
    else:
        conn.execute(_ep.insert().values(
            user_id=user_id, job_title=job_title, org=org, cert_file=path,
            external_link=external_link, status="pending"))
    conn.commit()
    return "ok"


def review(user_id, approve):
    """관리자 심사. 승인 시 users.is_verified=1."""
    conn = get_conn()
    profile = get_profile(user_id, conn)
    if not profile or profile["status"] != "pending":
        return "not_found"
    status = "approved" if approve else "rejected"
    conn.execute(sa.update(_ep).where(_ep.c.user_id == user_id)
                 .values(status=status, reviewed_at=datetime.now()))
    conn.execute(sa.update(_u).where(_u.c.id == user_id)
                 .values(is_verified=1 if approve else 0))
    conn.commit()
    return "ok"


def list_pending():
    conn = get_conn()
    rows = conn.execute(
        sa.select(_ep, _u.c.nickname).select_from(_ep.join(_u, _ep.c.user_id == _u.c.id))
        .where(_ep.c.status == "pending").order_by(_ep.c.created_at)
    ).mappings().all()
    return [dict(r) for r in rows]
