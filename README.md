# 오재 (오늘의 재테크)

재테크 커뮤니티 하이브리드 웹앱 — Flask + Jinja2 SSR (MPA), MariaDB.
기획·디자인 스펙은 [CLAUDE.md](CLAUDE.md), 구현 중 내린 판단은 [DECISIONS.md](DECISIONS.md) 참고.
`design/` 폴더의 HTML 8개가 픽셀 기준 디자인 원본이다.

## 로컬 실행 (Windows/맥 공통)

```bash
python -m venv venv
venv\Scripts\activate          # (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt

cp .env.example .env            # 로컬은 기본값(sqlite)으로 충분. DATABASE_URL 주석 참고

python -m scripts.init_db       # 스키마 + 카테고리 6종
python -m scripts.seed          # 더미 데이터 (계정 아래 참고)
python run.py                   # http://localhost:5000
```

### 시드 계정 (비밀번호 모두 `password123`)

| 계정 | 권한 |
|---|---|
| admin@ojae.kr | 관리자 → `/admin` |
| expert@ojae.kr | 인증 전문가 (칼럼 발행 가능) |
| user1~4@ojae.kr | 일반 회원 |

## 테스트

```bash
python -m pytest            # 전체 (SQLite 인메모리, 외부 의존 전부 목)
python -m pytest -q tests/test_quiz.py   # 개별 모듈
```

## 배치 (Flask 앱과 분리 실행 — CLAUDE.md §11)

```bash
python -m batch.runner --once hot_posts       # 인기글/수익 집계 (10분 주기 권장)
python -m batch.runner --once fetch_news      # RSS 뉴스 수집 (매시)
python -m batch.runner --once daily_briefing  # Claude 브리핑 (06:00, ANTHROPIC_API_KEY 필요)
python -m batch.runner --once close_poll      # 투표 마감 (00:00)
python -m batch.runner --daemon               # APScheduler 상주 모드 (프로덕션)
```

## 프로덕션 배포 (Cafe24 Ubuntu)

```bash
pip install -r requirements-prod.txt
# MariaDB: .env 의 DATABASE_URL=mysql+pymysql://ojae:***@localhost:3306/ojae?charset=utf8mb4
gunicorn -w 3 -t 30 -b 127.0.0.1:8000 wsgi:app
```

- nginx 리버스 프록시 + `/static/` `expires 30d`, gzip(css/js/svg).
- 배치는 **gunicorn과 별도로** systemd 서비스 1개:

```ini
# /etc/systemd/system/ojae-batch.service
[Unit]
Description=ojae batch runner
After=network.target mariadb.service

[Service]
User=ojae
WorkingDirectory=/srv/ojae
ExecStart=/srv/ojae/venv/bin/python -m batch.runner --daemon
Restart=always

[Install]
WantedBy=multi-user.target
```

- 백업(권장 cron): 새벽 4시 `mysqldump` + `app/static/uploads/` tar, 로컬 7일 보관.

## 구조 요약

```
app/
  db/schema.py        # 단일 스키마 소스 (MariaDB/SQLite 겸용, SQLAlchemy Core)
  services/           # 도메인 로직 (post/comment/quiz/poll/point/expert/...)
  blueprints/         # 라우트 (main/auth/community/news/columns/my/quiz/api/admin)
  templates/          # base.html + 부분템플릿(_gnb/_topnav/_rail/_quiz/_vote/_post_card...)
  static/css/         # common.css(공통 65규칙) + 페이지별 css — design/ 초안에서 기계 추출
  static/avatars/     # 기본 아바타 12종 SVG
batch/                # 단독 실행 배치 (fetch_news/daily_briefing/hot_posts/close_poll)
scripts/              # init_db.py, seed.py
tests/                # pytest 128개 (인메모리 SQLite, OAuth/LLM/RSS 목)
```
