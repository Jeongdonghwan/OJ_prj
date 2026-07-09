# -*- coding: utf-8 -*-
"""더미 데이터 시드 — 관리자/전문가/일반 계정 + 글/댓글/퀴즈/투표/뉴스/캘린더.

사용: python -m scripts.seed
(먼저 python -m scripts.init_db 실행)

계정 (비밀번호 모두 password123):
  admin@ojae.kr  관리자
  expert@ojae.kr 인증 전문가 (박PB)
  user1@ojae.kr ~ user4@ojae.kr 일반 회원
"""
import random
from datetime import date, datetime, timedelta

import sqlalchemy as sa
from werkzeug.security import generate_password_hash

from app import create_app
from app.db import schema
from app.db.engine import get_engine
from config import DevConfig

PW = generate_password_hash("password123")


def _user(conn, email, nickname, **kw):
    values = dict(email=email, oauth_provider="email", nickname=nickname,
                  password_hash=PW, avatar_no=1, status="active",
                  created_at=datetime.now() - timedelta(days=60))
    values.update(kw)
    uid = conn.execute(schema.users.insert().values(**values)).inserted_primary_key[0]
    conn.execute(sa.update(schema.users).where(schema.users.c.id == uid)
                 .values(avatar_no=(uid % 12) + 1))
    return uid


def seed():
    app = create_app(DevConfig)
    with app.app_context():
        engine = get_engine(app)
        with engine.begin() as conn:
            existing = conn.execute(sa.select(schema.users.c.id).limit(1)).first()
            if existing:
                print("이미 사용자가 있습니다 — 시드 생략 (프레시 DB에서 실행하세요)")
                return

            admin = _user(conn, "admin@ojae.kr", "오재지기", is_admin=1)
            expert = _user(conn, "expert@ojae.kr", "박PB", is_verified=1)
            users = [_user(conn, f"user{i}@ojae.kr", n) for i, n in
                     enumerate(["몽실이", "티끌모아", "존버왕", "월급루팡"], start=1)]

            conn.execute(schema.expert_profiles.insert().values(
                user_id=expert, job_title="자산관리사", org="오재금융",
                cert_file="/static/uploads/certs/seed.pdf", status="approved",
                reviewed_at=datetime.now()))

            cats = {r["slug"]: r["id"] for r in
                    conn.execute(sa.select(schema.categories)).mappings().all()}

            posts_data = [
                (users[0], "realestate", "normal", "전세 만기, 갱신 vs 매수 고민입니다",
                 "보증금 3억으로 전세 살고 있는데 다음 달이 만기입니다.\n갱신청구권을 쓸지, 대출 껴서 매수할지 고민이에요.", None),
                (users[1], "saving", "profit", "적금 풍차돌리기 1년 결산",
                 "12개 통장 만기 전부 돌았습니다. 총 이자 정리해서 공유해요.", 1847200),
                (users[2], "coin", "question", "비트코인 지금이라도 적립식으로 살까요",
                 "매달 30만원 정도 여유가 생기는데 적립식 진입 어떻게 보시나요.", None),
                (users[3], "stock", "normal", "월급 300 사회초년생 포트폴리오 봐주세요",
                 "적금 50 / 지수 ETF 30 / 개별주 20 비율입니다. 조언 부탁드려요.", None),
                (users[2], "stock", "profit", "단타 손절 인증합니다",
                 "물타다가 결국 손절했습니다. 다들 저처럼 되지 마세요.", -2108500),
                (expert, "fund", "normal", "ISA 계좌 만기, 전환 전략 3가지",
                 "연장·해지·재가입 케이스별 세금 차이 총정리입니다.", None),
            ]
            post_ids = []
            for i, (uid, cat, ptype, title, content, profit) in enumerate(posts_data):
                is_column = 1 if uid == expert else 0
                pid = conn.execute(schema.posts.insert().values(
                    user_id=uid, category_id=cats[cat], post_type=ptype,
                    is_column=is_column, column_tag="절세" if is_column else None,
                    title=title, content=content, profit_amount=profit,
                    view_count=random.randint(50, 1200),
                    like_count=random.randint(3, 90), comment_count=0, is_flagged=0,
                    created_at=datetime.now() - timedelta(hours=3 * i + 1),
                )).inserted_primary_key[0]
                post_ids.append(pid)

            comments = [
                (post_ids[0], users[3], "저도 작년에 똑같은 고민 했는데 갱신청구권 쓰고 2년 벌었어요."),
                (post_ids[0], expert, "맞벌이시면 DSR 기준으로 대출 한도부터 확인해보세요."),
                (post_ids[1], users[0], "대단하세요! 저도 풍차 시작해봐야겠어요."),
                (post_ids[2], users[1], "적립식이면 타이밍 걱정은 덜해도 될 것 같아요."),
            ]
            for pid, uid, content in comments:
                conn.execute(schema.comments.insert().values(
                    post_id=pid, user_id=uid, content=content))
                conn.execute(sa.update(schema.posts).where(schema.posts.c.id == pid)
                             .values(comment_count=schema.posts.c.comment_count + 1))

            today = date.today()
            quiz_rows = [
                (today, "예금자보호 한도는 1인당 금융회사별 얼마까지일까요?",
                 "5,000만원", "1억원", 2,
                 "2025년 9월부터 예금자보호 한도가 1억원으로 상향됐어요."),
                (today - timedelta(days=1), "국내 상장 ETF의 매매차익에는 세금이 붙지 않는다?",
                 "O", "X", 2, "국내주식형만 비과세, 그 외엔 배당소득세 15.4%가 부과됩니다."),
                (today - timedelta(days=2), "청약통장 월 납입 인정액은 최대 25만원이다?",
                 "O", "X", 1, "2024년 11월부터 10만원에서 25만원으로 상향됐습니다."),
                (today - timedelta(days=3), "연금저축 세액공제 한도는 연 600만원이다?",
                 "O", "X", 1, "IRP 합산 시 최대 900만원까지 공제됩니다."),
            ]
            for qd, q, c1, c2, ans, exp in quiz_rows:
                conn.execute(schema.quizzes.insert().values(
                    quiz_date=qd, question=q, choice1=c1, choice2=c2,
                    answer_no=ans, explanation=exp, created_by=admin))

            conn.execute(schema.polls.insert().values(
                question="이번 주 코스피, 어떻게 될까요?",
                option_up="오른다", option_down="떨어진다",
                starts_at=datetime.now() - timedelta(hours=1),
                ends_at=datetime.combine(today, datetime.max.time()),
                is_active=1))

            news_rows = [
                ("한국경제", "서울 아파트값 3주 연속 상승… 강남권 신고가 잇따라", "realestate", 2),
                ("연합뉴스", "연준, 7월 금리 동결 시사… 시장은 9월 인하에 무게", "policy", 4),
                ("블로터", "이더리움 현물 ETF 승인 임박설에 코인 시장 들썩", "coin", 6),
                ("머니투데이", "청년도약계좌 가입 요건 완화… 소득 기준 상향", "policy", 8),
                ("서울경제", "2분기 어닝시즌 개막, 반도체 실적 전망은", "stock", 10),
            ]
            for src, title, cat, hrs in news_rows:
                conn.execute(schema.news_articles.insert().values(
                    source=src, title=title, url=f"https://example.com/news/{hrs}",
                    summary=title, category=cat,
                    published_at=datetime.now() - timedelta(hours=hrs), comment_count=0))

            conn.execute(schema.daily_briefings.insert().values(
                brief_date=today,
                content="서울 아파트 3주 연속 상승 · 연준 금리 동결 시사 · 이더리움 ETF 승인 임박설"))

            cal_rows = [
                (today + timedelta(days=1), "힐스테이트 ○○ 청약 접수 시작", 0),
                (today + timedelta(days=5), "삼성전자 2분기 잠정실적 발표", 0),
                (today + timedelta(days=6), "청년도약계좌 7월 신청 마감", 1),
                (today + timedelta(days=20), "미 FOMC 금리 결정", 1),
            ]
            for d, title, hot in cal_rows:
                conn.execute(schema.calendar_events.insert().values(
                    event_date=d, title=title, is_hot=hot))

        # 인기글/수익 캐시 집계
        from batch.jobs import hot_posts
        hot_posts.run(engine)

    print("시드 완료:")
    print("  관리자  admin@ojae.kr / password123  → /admin")
    print("  전문가  expert@ojae.kr / password123")
    print("  일반    user1~4@ojae.kr / password123")


if __name__ == "__main__":
    seed()
