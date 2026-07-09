"""Step 3: 글 CRUD, 권한, soft delete, 금지어 플래그."""
import sqlalchemy as sa

from app.db import schema


def _post_row(db, post_id):
    return db.execute(sa.select(schema.posts).where(schema.posts.c.id == post_id)).mappings().first()


def test_create_post_via_route(client, login, user, db):
    login(user)
    res = client.post("/write", data={
        "category": "stock", "post_type": "question",
        "title": "삼성전자 지금 사도 될까요", "content": "고민입니다\n\n의견 부탁드려요"})
    assert res.status_code == 302
    post_id = int(res.headers["Location"].rsplit("/", 1)[-1])
    row = _post_row(db, post_id)
    assert row["title"] == "삼성전자 지금 사도 될까요"
    assert row["post_type"] == "question"
    assert row["is_flagged"] == 0

    html = client.get(f"/post/{post_id}").get_data(as_text=True)
    assert "삼성전자 지금 사도 될까요" in html
    assert "질문" in html  # 말머리 뱃지


def test_profit_post_stores_amount(client, login, user, db):
    login(user)
    res = client.post("/write", data={
        "category": "saving", "post_type": "profit", "profit_amount": "1847200",
        "title": "적금 결산", "content": "1년 결산입니다"})
    post_id = int(res.headers["Location"].rsplit("/", 1)[-1])
    assert _post_row(db, post_id)["profit_amount"] == 1847200


def test_banned_word_flags_post(client, login, user, db):
    login(user)
    res = client.post("/write", data={
        "category": "free", "post_type": "normal",
        "title": "좋은 리딩방 소개합니다", "content": "수익보장 100%"})
    assert res.status_code == 302  # 저장은 되고
    post_id = int(res.headers["Location"].rsplit("/", 1)[-1])
    assert _post_row(db, post_id)["is_flagged"] == 1  # 플래그


def test_edit_own_post(client, login, user, db, post_factory):
    post_id = post_factory(user, title="원래 제목")
    login(user)
    res = client.post("/write", data={
        "post_id": post_id, "category": "free", "post_type": "normal",
        "title": "수정된 제목", "content": "수정된 내용"})
    assert res.status_code == 302
    row = _post_row(db, post_id)
    assert row["title"] == "수정된 제목"
    assert row["updated_at"] is not None


def test_cannot_edit_others_post(client, login, user_factory, post_factory):
    author, attacker = user_factory(), user_factory()
    post_id = post_factory(author)
    login(attacker)
    res = client.post("/write", data={
        "post_id": post_id, "category": "free", "post_type": "normal",
        "title": "해킹", "content": "해킹"})
    assert res.status_code == 403
    # 수정 화면 접근도 차단
    assert client.get(f"/write?edit={post_id}").status_code == 403


def test_soft_delete(client, login, user_factory, post_factory, db):
    author, attacker = user_factory(), user_factory()
    post_id = post_factory(author, title="삭제될 글")

    login(attacker)
    assert client.post(f"/post/{post_id}/delete").status_code == 403

    login(author)
    res = client.post(f"/post/{post_id}/delete")
    assert res.status_code == 302
    assert _post_row(db, post_id)["deleted_at"] is not None  # soft delete
    assert client.get(f"/post/{post_id}").status_code == 404  # 상세 404
    assert "삭제될 글" not in client.get("/community").get_data(as_text=True)  # 목록 제외


def test_write_requires_login(client):
    assert client.get("/write").status_code == 302
    assert client.post("/write", data={"title": "t", "content": "c"}).status_code == 302


def test_column_publish_requires_expert(client, login, user, db):
    """비전문가가 column_tag를 보내도 일반 글로 저장."""
    login(user)
    res = client.post("/write", data={
        "category": "free", "post_type": "normal", "column_tag": "절세",
        "title": "가짜 칼럼", "content": "일반인이 쓴 글"})
    post_id = int(res.headers["Location"].rsplit("/", 1)[-1])
    row = _post_row(db, post_id)
    assert row["is_column"] == 0
    assert row["column_tag"] is None


def test_expert_can_publish_column(client, login, expert_user, db):
    login(expert_user)
    res = client.post("/write", data={
        "category": "fund", "post_type": "normal", "column_tag": "절세",
        "title": "진짜 칼럼", "content": "전문가의 칼럼"})
    post_id = int(res.headers["Location"].rsplit("/", 1)[-1])
    row = _post_row(db, post_id)
    assert row["is_column"] == 1
    assert row["column_tag"] == "절세"
    # 칼럼 상세에 면책 문구 자동 삽입
    html = client.get(f"/post/{post_id}").get_data(as_text=True)
    assert "투자 권유가 아닙니다" in html
