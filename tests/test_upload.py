"""Step 3: 이미지 업로드 — 리사이즈/webp/확장자·용량 거부/파일명 랜덤화."""
import io

import pytest
from PIL import Image

from app.services.upload import UploadError, save_image


def _png_bytes(w=2000, h=1500, color=(200, 60, 60)):
    buf = io.BytesIO()
    Image.new("RGB", (w, h), color).save(buf, "PNG")
    buf.seek(0)
    return buf


def _file(buf, name):
    from werkzeug.datastructures import FileStorage
    return FileStorage(stream=buf, filename=name)


@pytest.fixture()
def upload_ctx(app, tmp_path):
    app.config["UPLOAD_DIR"] = tmp_path
    with app.test_request_context():
        yield tmp_path


def test_resize_and_webp(upload_ctx):
    body, thumb = save_image(_file(_png_bytes(2000, 1500), "photo.png"))
    assert body.endswith(".webp") and thumb.endswith(".webp")
    assert "photo" not in body  # 파일명 랜덤화

    root = upload_ctx
    body_file = next(root.rglob(body.rsplit("/", 1)[-1]))
    thumb_file = next(root.rglob(thumb.rsplit("/", 1)[-1]))
    with Image.open(body_file) as im:
        assert im.format == "WEBP"
        assert max(im.size) <= 1200
    with Image.open(thumb_file) as im:
        assert max(im.size) <= 400


def test_reject_bad_extension(upload_ctx):
    with pytest.raises(UploadError, match="bad_extension"):
        save_image(_file(_png_bytes(10, 10), "malware.exe"))


def test_reject_oversize(app, upload_ctx):
    app.config["MAX_IMAGE_SIZE"] = 1000  # 1KB로 낮춰서 검증
    with pytest.raises(UploadError, match="too_large"):
        save_image(_file(_png_bytes(500, 500), "big.png"))


def test_reject_fake_image(upload_ctx):
    fake = io.BytesIO(b"not an image at all")
    with pytest.raises(UploadError, match="not_image"):
        save_image(_file(fake, "fake.png"))


def test_write_with_image_sets_thumbnail(app, client, login, user, db, tmp_path):
    import sqlalchemy as sa
    from app.db import schema
    app.config["UPLOAD_DIR"] = tmp_path
    login(user)
    res = client.post("/write", data={
        "category": "free", "post_type": "normal",
        "title": "사진 글", "content": "본문",
        "images": (_png_bytes(800, 600), "pic.png"),
    }, content_type="multipart/form-data")
    assert res.status_code == 302
    post_id = int(res.headers["Location"].rsplit("/", 1)[-1])
    row = db.execute(sa.select(schema.posts.c.thumbnail)
                     .where(schema.posts.c.id == post_id)).mappings().one()
    assert row["thumbnail"] and row["thumbnail"].endswith(".webp")
    imgs = db.execute(sa.select(schema.post_images).where(
        schema.post_images.c.post_id == post_id)).mappings().all()
    assert len(imgs) == 1
