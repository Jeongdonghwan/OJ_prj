# DECISIONS.md — 자율 판단 기록

CLAUDE.md가 명시하지 않았거나 선택지를 열어둔 부분에 대해 스스로 내린 판단과 근거.

## D1. DB 레이어: SQLAlchemy Core (ORM 아님)
CLAUDE.md §1은 "PyMySQL 직접 쿼리 또는 SQLAlchemy Core 중 택1". **SQLAlchemy Core 선택.**
- 근거: 테스트는 SQLite 인메모리, 프로덕션은 MariaDB — 단일 스키마 정의(`app/db/schema.py`)에서 두 방언 모두 지원. `sa.Enum`이 MySQL에선 native ENUM, SQLite에선 VARCHAR+CHECK로 자동 변환되어 스키마 패리티 유지.
- 패리티 검증: `test_config.py::test_schema_mysql_dialect_parity` 가 mysql 방언 DDL 컴파일 결과의 ENUM/utf8mb4 프래그먼트를 검증.
- §11의 DBUtils PooledDB 대신 SQLAlchemy 엔진 풀(pool_size=10, pool_pre_ping) 사용 — 동일한 목적(요청마다 커넥션 생성 방지)을 SQLAlchemy 내장 기능으로 충족. **의도적 편차.**

## D2. 스키마 추가 (스펙 DDL에 없지만 기능상 필수)
- `users.password_hash VARCHAR(255) NULL` — 이메일 로그인이 스펙에 있으나 DDL에 비밀번호 컬럼 부재.
- `users.nickname_changed_at DATETIME NULL` — §10 "닉네임 변경 30일 1회" 규칙 구현용.
- `posts.profit_amount BIGINT NULL` — §5 하단에 명시된 추가 컬럼.
- `hot_cache(cache_key PK, payload TEXT(JSON), updated_at)` — §7이 이름만 언급, DDL 미정의. 범용 JSON 캐시로 설계해 인기글 TOP5·투표 비율 5분 캐시·수익 레일을 모두 수용.
- `news_comments` 별도 테이블 — §5 `comments`는 `post_id FK`로 게시글 전용. 뉴스 댓글(§4)은 스펙 테이블 형태를 훼손하지 않도록 별도 테이블로 분리.

## D3. 인증: Flask-Login + 주입형 카카오 OAuth 클라이언트
- 카카오 클라이언트를 `app.extensions["kakao_oauth"]`로 주입 — 테스트에서 FakeKakaoClient로 교체, 실제 HTTP 없음.
- 이메일 로그인: werkzeug `generate_password_hash`/`check_password_hash`.
- 아바타 배정: 스펙의 `user_id % 12`를 `(id % 12) + 1`로 해석 (파일명이 av_01~av_12, 0번 파일 없음).

## D4. CSS 추출 전략: 공통 접두 + 페이지 접미, 캐스케이드 순서 보존
- 8개 초안의 `<style>`은 "동일한 공통 블록 + 페이지 고유 블록" 구조. 공통 → `static/css/common.css`(원본 순서 유지), 페이지 고유 → `static/css/<page>.css`(common 뒤에 로드해 오버라이드 유지).
- 속성값은 절대 변경하지 않음 (픽셀 정확성).

## D5. base.html: 5개 chrome 블록 구조
- topnav/adwings/side/rail/gnb 블록 각각 기본 include. write·login은 초안대로 chrome 없음 → 전부 빈 블록으로 오버라이드.
- 레일 중복 제거(§3)는 초안 CSS 규칙 그대로: 홈은 레일 퀴즈 숨김, 커뮤니티는 레일 투표를 컨텍스트 플래그로 미출력.

## D6. 아바타 12종
- 초안 인라인 6종(돼지·고양이·곰·병아리·토끼·황소)을 그대로 추출 + 같은 스타일 문법(64 viewBox, 파스텔 원형 몸통, 2.4r 눈+하이라이트, 볼터치)으로 6종(다람쥐·부엉이·고래·거북이·여우·강아지) 신규 제작.

## D7. Rate limit 테스트 전략
- Flask-Limiter memory storage, 데코레이터 방식(글 2/min, 댓글 5/min, 로그인 10/min/IP).
- TestConfig는 `RATELIMIT_ENABLED=False` — rate limit 전용 테스트 모듈에서만 활성화된 앱을 별도 생성.

## D8. 커서 페이지네이션 응답 형식
- `GET /api/posts?cursor=` 커서는 `created_at|id`의 urlsafe base64. WHERE는 OR 확장형(SQLite row-value 미지원 대응).
- 응답에 `_post_card.html` 서버 렌더링 HTML 조각 포함 — 무한스크롤도 SSR 마크업 그대로 사용해 픽셀 일관성 유지.

## D9. 배치 실행 형태
- `batch/runner.py --once <job>` (개발/Windows·cron) + `--daemon` (APScheduler BlockingScheduler, 프로덕션 systemd 단독 프로세스). Flask 앱 비내장(§11 중복 실행 방지).
- 잡 함수는 의존성 주입형(feedparser/LLM 클라이언트 파라미터) — 테스트에서 목 주입.

## D10. 조회수/토글 API
- 조회수: 세션 `viewed_posts` 리스트, 최근 50개 제한(§11).
- 도움됐어요/스크랩/팔로우: `POST /api/...` 토글, 비로그인 401 JSON(프런트에서 /login 유도).

## D11. 테스트 로그인 방식
- Flask-Login 세션 키(`_user_id`)를 직접 주입하는 `login` fixture — OAuth/폼 로그인을 거치지 않고 임의 권한 상태를 빠르게 구성.

---
아래는 구현 진행 중 추가로 내린 판단.

## D12. CSS 추출 규칙 확정 (기계적 추출 + 위험 검사)
- 8개 초안의 스타일을 규칙 단위로 파싱해 **6개 파일 이상에서 바이트 동일(공백 정규화)** 인 비-미디어 규칙만 `common.css`로 추출(65규칙). **모든 `@media` 블록은 페이지 CSS에 원본 순서 그대로 유지** — 페이지별 미디어 변형(.app/.side/.rail)과 공통 미디어 블록의 캐스케이드 순서가 뒤집히는 위험을 스크립트로 검증한 결과에 따른 결정.
- 페이지 변형이 존재하는 셀렉터(.app, .chip, .hd, .qcard)는 페이지 CSS가 common 뒤에 로드되어 원본과 동일한 우선순위 유지(원본에서도 페이지 변형이 나중 정의).
- CSS 주석은 제거(픽셀 영향 없음). 속성값은 일절 변경 없음.

## D13. 질문 말머리 뱃지 `.tag-q` 신설
- 스펙(§4)은 말머리 3종(수익인증/거래인증/질문)을 요구하나 초안 CSS에는 `.tag-p`(레드틴트)·`.tag-t`(블루틴트)만 존재. `.tag-q`를 그레이 틴트(#F2F3F5/#4E5968)로 동일 규격(패딩·radius·자간)으로 community.css/post.css에 추가.

## D14. 피드 메타 카테고리 컬러 매핑
- 초안에 명시된 것만 사용: 부동산 `.cat-r`, 예적금·절약 `.cat-s`, 펀드·ETF `.cat-f`, 코인 인라인 `#B87A18`. 초안에 없는 주식·자유수다는 기본 그레이(클래스 없음).

## D15. PC 상단바 비로그인 상태
- 스펙 §3 "비로그인 시 로그인 버튼" — 초안에 디자인 없음. 아바타 자리에 `.tl` 스타일 "로그인" 링크로 대체(레드 총량 규제 준수).

## D16. 네이버 로그인 버튼
- 네이버 OAuth는 9번(제외 범위)이지만 로그인 화면 디자인에 버튼이 존재 → 버튼은 그대로 렌더링하되 클릭 시 "준비 중" 알림.

## D17. 이메일 로그인/가입 화면
- 초안 없음("이메일로 시작하기" 버튼만 존재). login.css의 토큰(.sb, .lg, .lgft)을 재사용한 최소 폼 페이지(`email_auth.html`) 신설.

## D18. 뉴스 리스트 클릭 동작
- 스펙: 아이템 클릭 → 원문 아웃링크(새탭), 댓글은 `/news/<id>`. 초안은 아이템 전체가 단일 `<a>` → 아이템은 원문 새탭 링크로 하고, 메타의 "댓글 N" 텍스트 클릭만 JS로 가로채 내부 상세로 이동.

## D19. 뉴스 상세(/news/<id>) 화면
- 초안 없음 → post.css 재사용(헤더+제목+요약+원문 버튼+댓글+입력바). 본문 전재 금지 원칙에 따라 요약+아웃링크 버튼만.

## D20. 수익 인증 레일 집계 기준
- "최근 7일 profit 글 상위/하위"를 **|profit_amount| 큰 순 상위 4건**으로 구현(초안 위젯이 수익·손실 혼합 4행). hot_posts 배치에서 함께 캐시.

## D21. 알림 발생 규칙 상세
- 내 글 댓글/대댓글/팔로우한 전문가 새 칼럼 3종(+관리자 공지는 추후). 자기 글에 자기 댓글은 미발송, 대댓글 시 부모 댓글 작성자와 글 작성자가 같으면 1건만 발송. 알림 페이지 열람 시 일괄 읽음 처리.

## D22. 수익 금액 표기 필터
- `signed_comma` 필터(+1,847,200 / -2,108,500) 신설 — Jinja 기본 format으로 부호+콤마 동시 표현 불가(구현 중 발견한 버그의 회귀 테스트 포함).

## D23. 전문가 증빙 파일
- `/static/uploads/certs/`에 랜덤 파일명으로 저장(jpg/png/webp/pdf 화이트리스트). 반려(rejected) 상태에서만 재신청 허용.

## D24. 글쓰기 화면 확장 (스펙 요구 기능의 UI 배치)
- 수익인증 선택 시 `profit_amount` 숫자 입력 노출, 전문가에게만 "칼럼으로 발행" 칩 그룹 노출 — 초안의 chipbar 문법을 그대로 재사용해 시각적 이질감 없이 추가.

## D25. 관리자 화면
- 스펙 §8 "부트스트랩 수준으로 최소하게" — 외부 CDN 의존 없이 시스템 폰트 + 단일 인라인 스타일의 자체 미니 스타일로 구현(오프라인/보안 이점).
