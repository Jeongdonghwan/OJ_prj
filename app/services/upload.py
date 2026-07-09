"""이미지 업로드: 확장자/MIME 화이트리스트, 리사이즈(1200/400), webp 변환, 파일명 랜덤화."""
import secrets
from datetime import date
from io import BytesIO
from pathlib import Path

import sqlalchemy as sa
from flask import current_app
from PIL import Image

from app.db import schema
from app.db.engine import get_conn

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp"}
BODY_MAX = 1200
THUMB_MAX = 400
WEBP_QUALITY = 82


class UploadError(Exception):
    pass


def _validate(file_storage):
    name = (file_storage.filename or "").lower()
    ext = Path(name).suffix
    if ext not in ALLOWED_EXT:
        raise UploadError("bad_extension")
    data = file_storage.read()
    file_storage.seek(0)
    if len(data) > current_app.config["MAX_IMAGE_SIZE"]:
        raise UploadError("too_large")
    try:
        img = Image.open(BytesIO(data))
        img.verify()
    except Exception:
        raise UploadError("not_image")
    return data


def save_image(file_storage):
    """검증 → 본문 1200px webp + 썸네일 400px webp 저장. 반환 (body_path, thumb_path)."""
    data = _validate(file_storage)
    img = Image.open(BytesIO(data))
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")

    today = date.today()
    rel_dir = Path(str(today.year)) / f"{today.month:02d}" / f"{today.day:02d}"
    abs_dir = Path(current_app.config["UPLOAD_DIR"]) / rel_dir
    abs_dir.mkdir(parents=True, exist_ok=True)
    token = secrets.token_hex(12)

    def _resize_save(max_px, suffix):
        im = img.copy()
        im.thumbnail((max_px, max_px))
        fname = f"{token}{suffix}.webp"
        im.save(abs_dir / fname, "WEBP", quality=WEBP_QUALITY)
        return f"/static/uploads/{rel_dir.as_posix()}/{fname}"

    body = _resize_save(BODY_MAX, "")
    thumb = _resize_save(THUMB_MAX, "_t")
    return body, thumb


def save_post_images(post_id, files):
    """글에 첨부된 이미지들 저장 + post_images 기록 + 첫 썸네일을 posts.thumbnail로."""
    files = [f for f in files if f and f.filename]
    if not files:
        return []
    max_n = current_app.config["MAX_IMAGES_PER_POST"]
    files = files[:max_n]
    conn = get_conn()
    saved = []
    for i, f in enumerate(files):
        body, thumb = save_image(f)  # UploadError는 호출자(라우트)에서 400 처리
        conn.execute(schema.post_images.insert().values(
            post_id=post_id, path=body, sort_order=i))
        saved.append((body, thumb))
    if saved:
        existing = conn.execute(sa.select(schema.posts.c.thumbnail)
                                .where(schema.posts.c.id == post_id)).scalar()
        if not existing:
            conn.execute(sa.update(schema.posts).where(schema.posts.c.id == post_id)
                         .values(thumbnail=saved[0][1]))
    conn.commit()
    return [s[0] for s in saved]
