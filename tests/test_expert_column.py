"""Step 7: 전문가 인증 플로우 + 칼럼 탭."""
import io

import sqlalchemy as sa

from app.db import schema


def _cert_file():
    return (io.BytesIO(b"%PDF-1.4 fake cert"), "cert.pdf")


def _apply(client, **overrides):
    data = {"job_title": "세무사", "org": "오재세무회계",
            "external_link": "https://blog.example.com", "cert_file": _cert_file()}
    data.update(overrides)
    return client.post("/expert/apply", data=data, content_type="multipart/form-data")


def test_apply_creates_pending(app, client, login, user, db, tmp_path):
    app.config["UPLOAD_DIR"] = tmp_path
    login(user)
    res = _apply(client)
    assert res.status_code == 302
    row = db.execute(sa.select(schema.expert_profiles).where(
        schema.expert_profiles.c.user_id == user["id"])).mappings().one()
    assert row["status"] == "pending"
    assert row["job_title"] == "세무사"
    assert row["cert_file"].startswith("/static/uploads/certs/")
    assert "cert" not in row["cert_file"].rsplit("/", 1)[-1].replace(".pdf", "")  # 랜덤 파일명


def test_apply_requires_login(client):
    assert client.get("/expert/apply").status_code == 302


def test_duplicate_pending_apply_rejected(app, client, login, user, tmp_path):
    app.config["UPLOAD_DIR"] = tmp_path
    login(user)
    _apply(client)
    res = _apply(client, cert_file=_cert_file())
    assert res.status_code == 200
    assert "이미 심사 중" in res.get_data(as_text=True)


def test_admin_approve_sets_verified(app, client, login, user, admin_user, db, tmp_path):
    app.config["UPLOAD_DIR"] = tmp_path
    login(user)
    _apply(client)
    login(admin_user)
    res = client.post("/admin/experts", data={"user_id": user["id"], "action": "approve"})
    assert res.status_code == 302
    assert db.execute(sa.select(schema.users.c.is_verified).where(
        schema.users.c.id == user["id"])).scalar_one() == 1
    assert db.execute(sa.select(schema.expert_profiles.c.status).where(
        schema.expert_profiles.c.user_id == user["id"])).scalar_one() == "approved"


def test_admin_reject_and_reapply(app, client, login, user, admin_user, db, tmp_path):
    app.config["UPLOAD_DIR"] = tmp_path
    login(user)
    _apply(client)
    login(admin_user)
    client.post("/admin/experts", data={"user_id": user["id"], "action": "reject"})
    assert db.execute(sa.select(schema.users.c.is_verified).where(
        schema.users.c.id == user["id"])).scalar_one() == 0

    login(user)  # 반려 후 재신청 가능
    res = _apply(client, cert_file=_cert_file())
    assert res.status_code == 302
    assert db.execute(sa.select(schema.expert_profiles.c.status).where(
        schema.expert_profiles.c.user_id == user["id"])).scalar_one() == "pending"


def test_columns_page_lists_only_columns(client, login, expert_user, user, post_factory):
    post_factory(user, title="일반 글")
    post_factory(expert_user, title="절세 칼럼", is_column=1, column_tag="절세")
    post_factory(expert_user, title="연금 칼럼", is_column=1, column_tag="연금·노후")

    html = client.get("/columns").get_data(as_text=True)
    assert "절세 칼럼" in html and "연금 칼럼" in html
    assert "일반 글" not in html

    # 태그 칩 필터
    html = client.get("/columns?tag=절세").get_data(as_text=True)
    assert "절세 칼럼" in html
    assert "연금 칼럼" not in html


def test_write_page_column_toggle_visibility(client, login, user, expert_user):
    login(user)
    assert "칼럼으로 발행" not in client.get("/write").get_data(as_text=True)
    login(expert_user)
    assert "칼럼으로 발행" in client.get("/write").get_data(as_text=True)


def test_home_shows_latest_columns(client, expert_user, post_factory):
    post_factory(expert_user, title="홈 노출 칼럼", is_column=1, column_tag="초보투자")
    html = client.get("/").get_data(as_text=True)
    assert "전문가 칼럼" in html
    assert "홈 노출 칼럼" in html
