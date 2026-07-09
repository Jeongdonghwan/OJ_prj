# 오재 (오늘의 재테크) — 개발 스펙 문서

재테크 커뮤니티 하이브리드 웹앱. 부동산·주식·코인·펀드·저축 커뮤니티 + 전문가 칼럼 + 재테크 뉴스 + 데일리 퀴즈/투표.
이 문서는 확정된 기획·디자인 스펙이며, `design/` 폴더의 HTML 8개가 픽셀 단위 디자인 정답이다. **디자인 초안의 마크업과 CSS를 최대한 그대로 Jinja2 템플릿으로 이식할 것.**

---

## 1. 기술 스택 & 배포

- **백엔드**: Python Flask + Jinja2 SSR (MPA). SPA 금지 — SEO가 성장 전략의 핵심이므로 모든 페이지 서버 렌더링.
- **DB**: MariaDB (utf8mb4). ORM 없이 PyMySQL + 직접 쿼리 또는 SQLAlchemy Core 중 택1 (기존 마케팅광장 관례 따름).
- **배포**: Cafe24 가상서버 (Ubuntu). gunicorn + nginx. 이미지 업로드는 로컬 디스크 (`/static/uploads/`, 날짜별 폴더).
- **배치**: APScheduler (Flask 앱 내장) — 뉴스 수집, 인기글 집계, 투표 마감.
- **앱 패키징**: 반응형 웹 완성 후 Expo WebView 셸 (푸시 알림 브릿지만 네이티브). 웹 개발 단계에서는 신경 쓸 것 없음. 단, 뒤로가기 시 스크롤 복원과 `viewport-fit=cover` / `env(safe-area-inset-bottom)` 은 반드시 유지.
- **폰트**: Pretendard (jsdelivr CDN, dynamic-subset).

## 2. 디자인 시스템 (절대 규칙)

`design/*.html` 의 `:root` 변수 체계를 공통 CSS로 추출해 사용한다.

```css
--red:#E0403C;      /* 메인 레드: 로고, CTA, 글쓰기 버튼/FAB, 인증뱃지, 랭킹 숫자, 수익 금액 */
--red-deep:#A32D2D; /* 눌림/강조 텍스트 */
--red-tint:#FCEBEB; /* 레드 배경 틴트 */
--ink:#191F28;      /* 제목, 활성 GNB */
--gray:#8B95A1;  --gray-light:#B0B8C1;
--bg:#FFFFFF;  --card:#FFFFFF;  --line:#EEF0F2;  /* 순백 배경 + 0.5px 헤어라인 */
```

- 하락/손실 컬러: `#3572B0` (블루). 상승/수익: 레드. 국내 관례 고정.
- 타이포: 화면제목 20~21/800 · 글제목 15~16/600 · 본문 14~15.5/400 · 메타 11.5~12/gray. 자간 -0.2~-0.6px.
- **레드 사용처 총량 규제**: 로고·글쓰기·인증뱃지·랭킹/수익 숫자·투표(오른다) 외 금지. GNB 활성 색은 잉크.
- **아이콘 규칙**: 내비/헤더 = 잉크 아웃라인 1.8px (디자인 초안의 자체 SVG 세트 사용, 외부 아이콘 라이브러리 금지). 활성 GNB 탭 = filled 전환. 홈 카테고리 = filled 듀오톤 컬러 아이콘 (초안에 포함). 그 외 영역 아이콘 사용 금지.
- **아바타**: 기본 아바타 12종 SVG (`/static/avatars/av_01.svg`~`av_12.svg`). 가입 시 `user_id % 12` 고정 배정, 프로필 사진 업로드 시 덮어씀. 초안에 6종 샘플 있음(돼지·고양이·곰·병아리·토끼·황소) — 같은 스타일로 6종 추가 제작(다람쥐·부엉이·고래·거북이·여우·강아지 등).
- **로고**: C안 확정 — 레드 말풍선+상승차트 심볼 + Pretendard 800 "오재" 워드마크. 심볼 단독 사용처: 앱 아이콘/파비콘/스플래시/빈 화면(그레이 변형).
- 전문가 표시는 닉네임 옆 **레드 체크 인증뱃지 하나만**. 직함은 프로필 페이지에서만.

## 3. 화면 ↔ 템플릿 매핑

| 디자인 초안 | 템플릿 | 라우트 | 비고 |
|---|---|---|---|
| home.html | templates/home.html | GET / | 퀴즈 카드 최상단 |
| community.html | templates/community.html | GET /community | 투표 카드(활성 투표 있을 때만) |
| post.html | templates/post_detail.html | GET /post/<id> | 댓글·대댓글 |
| news.html | templates/news.html | GET /news | 브리핑 + 아웃링크 리스트 |
| column.html | templates/columns.html | GET /columns | 전문가 글만 |
| write.html | templates/write.html | GET,POST /write | 로그인 필수 |
| my.html | templates/my.html | GET /my | 로그인 필수 |
| login.html | templates/login.html | GET /login | 소셜 로그인 |

공통 요소는 base.html + 부분 템플릿으로 분리: `_gnb.html`(모바일 하단탭), `_topnav.html`(PC 상단, 로그인 시 아바타/비로그인 시 로그인 버튼), `_rail.html`(PC 우측 위젯), `_adwings.html`, `_quiz.html`, `_vote.html`, `_post_card.html`.

### 반응형 규칙 (초안에 구현되어 있음 — 그대로 유지)
- 모바일(<1240px): 하단 GNB 5탭(filled/outline 전환) + 커뮤니티 글쓰기 FAB.
- PC(≥1240px): 상단 GNB(로고+메뉴4개 / 우측: 검색·알림·글쓰기·프로필아바타), 중앙 600px, 우측 레일 280px. 하단 GNB·FAB 숨김.
- PC(≥1460px): 좌우 스카이스크래퍼 광고 윙 240×600 노출.
- 레일 중복 제거: 홈은 레일 퀴즈 숨김(중앙에 있음), 커뮤니티는 레일 투표 숨김.

## 4. 화면별 기능 스펙

### 홈 `/`
1. 데일리 퀴즈 카드(§6) 2. 카테고리 그리드 6종 → `/community?cat=<slug>` 3. 지금 뜨는 글 TOP5 (24h 조회+댓글 가중치, 배치 집계) 4. 전문가 칼럼 최신 3 (칩: 칼럼 주제 태그) 5. 재테크 뉴스 3.

### 커뮤니티 `/community`
- 쿼리: `?cat=` (부동산/주식/코인/펀드ETF/예적금절약/자유수다), `?sort=` (latest|hot|expert|profit|trade), 페이지네이션(무한스크롤: `GET /api/posts?page=`).
- 상단: 활성 투표 있으면 투표 카드(§6). PC 전용 글쓰기 유도 박스 → /write.
- 피드 카드: 아바타·닉네임(+인증뱃지)·카테고리·시간·조회 / 제목(볼드)+본문 2줄 클램프 / 첨부 이미지 있으면 우측 66px 정사각 썸네일(object-fit:cover) / 하단 알약: 도움됐어요(토글, AJAX)·댓글 수.
- 말머리 뱃지: 수익인증(레드틴트)·거래인증(블루틴트)·질문.
- 네이티브 광고 슬롯: 피드 5번째 위치마다 (관리자가 광고 없으면 미노출).

### 글 상세 `/post/<id>`
- 헤더: 뒤로가기 + 카테고리명 + 더보기(신고/작성자면 수정·삭제).
- 제목 / 작성자 행(아바타·닉·뱃지·팔로우 버튼·시간·조회) / 본문(개행 유지, 이미지 인라인) / 액션 알약: 도움됐어요·스크랩·공유(URL 복사).
- 댓글: 1뎁스 대댓글, 작성자 뱃지, 하단 고정 입력바. 조회수는 세션당 1회 증가.

### 재테크뉴스 `/news`
- 칩: 전체/부동산/증시/코인/금리·정책. 상단 오늘의 브리핑(뉴트럴 그레이 카드, 3줄 — Claude API로 매일 06:00 생성, `daily_briefings` 저장).
- 리스트: 제목(2줄)+언론사·시간·댓글수+우측 78×54 썸네일. 클릭 → 원문 **아웃링크(새탭)**. 저작권상 본문 전재 금지, 제목+요약 2줄까지만.
- 뉴스 댓글: `/news/<id>` 내부 페이지에서 댓글만 (본문은 요약+원문 링크).

### 전문가칼럼 `/columns`
- posts 중 `is_column=1` 만. 칩: 칼럼 태그(절세/내집마련/연금·노후/초보투자 — column_tags). 리스트: 제목+설명1줄+작성자(뱃지+직함)+조회 / 우측 72px 썸네일. 하단 전문가 인증 신청 배너 → /expert/apply.
- 칼럼 작성은 인증 전문가만 (/write 에서 전문가면 "칼럼로 발행" 토글 노출).

### 글쓰기 `/write`
- 카테고리 칩(자유수다 기본 선택·맨앞) / 말머리 칩(일반·수익인증·거래인증·질문) / 제목(필수) / 본문 / 사진 첨부(최대 10장, 5MB, jpg·png·webp, 서버 리사이즈 1200px).
- 하단 면책 고지 문구 고정 노출(초안 문구 그대로). 플레이스홀더에 커뮤니티 가이드 포함.
- 금지어 필터(리딩방·수익보장 등 키워드 → 저장 시 관리자 검토 플래그).

### 마이 `/my` · 로그인 `/login`
- 마이: 프로필(아바타·닉·가입월), 내 글/댓글/스크랩 카운트+목록, 전문가 인증 배너, 설정 메뉴, 로그아웃.
- 로그인: 카카오 OAuth(필수) + 네이버 OAuth + 이메일. 세션 기반(Flask-Login). 가입 시 닉네임 설정 + 아바타 자동 배정.

## 5. DB 스키마 (MariaDB DDL 요지)

```sql
users(id PK, email UNIQ NULL, oauth_provider ENUM('kakao','naver','email'), oauth_id, nickname UNIQ,
      avatar_no TINYINT, profile_img VARCHAR NULL, is_verified TINYINT(0), is_admin TINYINT(0),
      points INT DEFAULT 0, created_at, last_login_at, status ENUM('active','banned','deleted'))

expert_profiles(user_id PK/FK, job_title VARCHAR(30), org VARCHAR(50), cert_file VARCHAR,
      external_link VARCHAR NULL, status ENUM('pending','approved','rejected'), reviewed_at)

categories(id PK, slug UNIQ, name, sort_order)   -- 6행 시드
posts(id PK, user_id FK, category_id FK, post_type ENUM('normal','profit','trade','question'),
      is_column TINYINT(0), column_tag VARCHAR(20) NULL, title VARCHAR(100), content TEXT,
      thumbnail VARCHAR NULL, view_count INT, like_count INT, comment_count INT,
      is_flagged TINYINT(0), created_at, updated_at, deleted_at NULL,
      INDEX(category_id, created_at), INDEX(is_column, created_at))
post_images(id PK, post_id FK, path, sort_order)
comments(id PK, post_id FK, user_id FK, parent_id FK NULL, content TEXT, created_at, deleted_at NULL)
reactions(user_id, target_type ENUM('post','comment','news'), target_id, PRIMARY KEY(user_id,target_type,target_id))
scraps(user_id, post_id, PK(user_id,post_id))
follows(follower_id, followee_id, PK)
notifications(id PK, user_id FK, type, ref_id, message, is_read, created_at)
reports(id PK, reporter_id, target_type, target_id, reason, status, created_at)

quizzes(id PK, quiz_date DATE UNIQ, question TEXT, choice1, choice2, choice3 NULL, choice4 NULL,
        answer_no TINYINT, explanation TEXT, created_by)
quiz_attempts(user_id, quiz_id, choice_no, is_correct, created_at, PK(user_id,quiz_id))
point_logs(id PK, user_id FK, amount INT, reason ENUM('quiz','attendance','vote','post','admin'), created_at)

polls(id PK, question, option_up VARCHAR(20), option_down VARCHAR(20),
      starts_at, ends_at, is_active TINYINT)          -- 활성 투표 없으면 커뮤니티 카드 미노출
poll_votes(user_id, poll_id, side ENUM('up','down'), created_at, PK(user_id,poll_id))

news_articles(id PK, source VARCHAR(30), title, summary VARCHAR(300), url UNIQ, thumbnail NULL,
      category ENUM('realestate','stock','coin','policy'), published_at, comment_count INT, INDEX(category,published_at))
daily_briefings(brief_date DATE PK, content VARCHAR(500))
calendar_events(id PK, event_date DATE, title VARCHAR(60), is_hot TINYINT, INDEX(event_date))
ad_slots(id PK, position ENUM('wing_l','wing_r','rail','native_feed'), image_path, link_url,
      starts_at, ends_at, is_active)
```

수익 인증 위젯: `post_type='profit'` 글 작성 시 선택 입력 필드 `profit_amount BIGINT NULL` (posts에 컬럼 추가) — 레일 "실시간 수익 인증"은 최근 7일 profit 글 상위/하위 정렬.

## 6. 퀴즈 · 투표 · 포인트 로직

- **퀴즈**: 매일 1문제(quiz_date). 응답 시 정답/오답 관계없이 정답+해설 공개. 정답 +10P, 참여만 +3P. 하루 1회. "지난 퀴즈 보기" = 최근 3개 인라인, `/quiz/archive` 전체 페이지(SEO용, 문제+해설 SSR).
- **투표**: 관리자가 등록, `is_active AND now BETWEEN starts_at,ends_at` 일 때만 커뮤니티 상단 노출. 투표 즉시 실시간 비율 공개. 참여 +3P. 자정 배치로 마감 처리.
- **포인트**: point_logs 합산 → users.points 캐시. 출석(첫 접속) +2P. 소진처는 추후(제휴 리워드) — 적립만 구현.

## 7. 배치 (APScheduler)

1. `fetch_news` (매시 정각): 언론사 RSS 파싱(feedparser) → 카테고리 키워드 분류 → news_articles upsert. 소스: 한국경제·연합뉴스 경제·매일경제 등 RSS 5~8개.
2. `daily_briefing` (06:00): 전일 뉴스 상위 headlines → Claude API 요약 3줄 → daily_briefings.
3. `hot_posts` (10분): 24h (조회×1 + 댓글×5 + 좋아요×3) 상위 5 캐시 테이블/Redis 없이 단순 테이블 `hot_cache`.
4. `close_poll` (00:00): 투표 마감, 익일 퀴즈 활성화 확인(없으면 관리자 알림).

## 8. 관리자 `/admin` (간단히)

세션 is_admin 체크. 기능: 퀴즈 등록/예약, 투표 등록, 캘린더 일정, 전문가 인증 심사(승인/반려), 신고 처리, 광고 슬롯 등록, 플래그 글 검토. 디자인은 부트스트랩 수준으로 최소하게 — 사용자 화면 디자인 시스템 적용 불필요.

## 9. 개발 순서 (커밋 단위 권장)

**1차 MVP**
1. 프로젝트 셋업, base.html + 공통 CSS/컴포넌트 분리, 반응형 골격
2. 회원(카카오 OAuth+이메일, 닉네임/아바타), 세션
3. 커뮤니티 CRUD(글·이미지·댓글·대댓글·도움됐어요·스크랩·조회수), 카테고리/말머리/정렬 필터
4. 홈(인기글 배치 포함), 마이페이지
5. 퀴즈(관리자 등록 + 응답 + 아카이브 + 포인트)

**2차**
6. 투표, 뉴스 수집 배치 + 뉴스 탭 + 브리핑, 캘린더
7. 전문가 인증 플로우 + 칼럼 탭 + 팔로우
8. 알림, 신고, 검색(제목+본문 LIKE → 추후 풀텍스트)

**3차**
9. 광고 슬롯 관리 + 노출, 네이버 OAuth
10. 시트맵·메타태그·OG 이미지 등 SEO 마감 → Expo WebView 패키징(§12 상세 스펙 따름) → 웹·앱 동시 출시

## 10. 주의사항 (기획·법률)

- **유사투자자문 리스크**: 글쓰기 면책 문구·금지어 플래그 필수 구현. 전문가 칼럼 하단에도 "본 콘텐츠는 정보 제공 목적이며 투자 권유가 아닙니다" 자동 삽입.
- **저작권**: 뉴스는 제목+요약 2줄+아웃링크만. 본문 저장/노출 금지.
- **SEO**: 모든 목록·상세 SSR, 시맨틱 태그, 페이지별 title/description, 글 상세 OG 태그. URL은 /post/123 형태 유지.
- 조회수 어뷰징 방지: 세션 기준 중복 차단. 도움됐어요/투표/퀴즈는 로그인 필수, 비로그인 클릭 시 /login 유도 모달.
- 삭제는 soft delete(deleted_at). 닉네임 변경 30일 1회.
- 이미지 업로드: Pillow 리사이즈+webp 변환, 경로 DB 저장. 업로드 확장자 화이트리스트.

## 11. 성능·운영 체크리스트 (처음부터 반영할 것)

**아키텍처**
- **배치 분리 (중요)**: APScheduler를 Flask 앱에 내장하지 말 것. gunicorn 워커가 2개 이상이면 스케줄러가 중복 실행되어 뉴스 중복 수집·포인트 이중 적립이 발생한다. 배치는 별도 스크립트(`batch/runner.py`)로 만들어 systemd 서비스 1개로 단독 실행 (또는 개별 cron 등록).
- **DB 커넥션 풀**: 요청마다 커넥션 생성 금지. DBUtils PooledDB (maxconnections=10, blocking=True) 사용.
- **페이지네이션은 커서 방식**: 무한스크롤 API는 OFFSET 금지. `WHERE (created_at, id) < (:last_created, :last_id) ORDER BY created_at DESC, id DESC LIMIT 20` 커서 방식으로 구현 (글이 수만 건 쌓여도 일정 속도).
- gunicorn: worker 2~3 (sync), timeout 30. nginx 리버스 프록시.

**이미지 (첫 병목 지점)**
- 업로드 시 Pillow로 리사이즈: 본문용 최대 1200px + 썸네일 400px 별도 생성, webp 변환(quality 82). 원본 보관 안 함.
- nginx에서 `/static/` 전체에 `expires 30d` + `gzip on`(css/js/svg) 설정. 아바타 SVG·공통 CSS는 브라우저 캐시로 재방문 트래픽 거의 0.
- CDN(Cloudflare 등)은 현 단계 도입하지 않음. 이미지 트래픽으로 서버 대역폭이 실제 병목이 되는 시점에 옵션으로 검토.

**핫스팟 처리**
- 조회수: 페이지뷰당 UPDATE는 현 규모 OK. 단 세션의 "본 글 ID" 목록은 최근 50개로 제한(세션 비대 방지).
- 인기글/레일 위젯(실시간 인기, 수익 인증, 캘린더, 브리핑)은 매 요청 계산 금지 — 배치 집계 결과 테이블을 단순 SELECT. 홈은 캐시된 데이터만 조합하므로 쿼리 5~6개 이내로 유지.
- 퀴즈/투표 응답은 PK(user_id, quiz_id/poll_id) upsert라 부하 없음. 투표 비율은 poll_votes COUNT를 5분 캐시(간단히 hot_cache 테이블 재활용).

**보안·안정성 (처음부터, 나중에 붙이면 귀찮음)**
- Rate limit: 글쓰기 분당 2회, 댓글 분당 5회, 로그인 시도 IP당 분당 10회 (Flask-Limiter, memory storage).
- XSS: 본문은 이스케이프 후 nl2br. HTML 입력 허용하지 않음. 이미지 태그는 서버가 생성.
- CSRF 토큰 전 폼 적용. 업로드 확장자·MIME 화이트리스트 + 파일명 랜덤화.
- 세션 쿠키: HttpOnly, SameSite=Lax, Secure(HTTPS).
- 백업: cron 새벽 4시 `mysqldump` + `/static/uploads/` tar → 로컬 7일 보관, 주 1회 외부(구글드라이브 rclone 등) 복사.
- 로그: nginx access log + Flask 에러 로그 파일 분리, logrotate. 500 에러 시 관리자 알림(텔레그램 봇 또는 메일) 권장.

**규모 기준점**: 위 구성으로 일 방문 수천~1만, 동접 100 수준까지 Cafe24 단일 서버로 충분. 그 이상은 이미지 CDN → DB 분리 순으로 검토.

## 12. 앱 패키징 스펙 (Expo WebView 셸)

웹 완성 후 3차 단계에서 진행. 별도 레포 `ojae-app/` (Expo SDK 최신, TypeScript).

**구성**
- `react-native-webview` 하나로 전체 화면 구성. `source={{uri: 'https://<도메인>'}}`.
- WebView 설정: `allowsBackForwardNavigationGestures`(iOS 스와이프 뒤로가기), `pullToRefreshEnabled`(Android), iOS는 스크롤 바운스 유지. `decelerationRate="normal"`.
- Android 하드웨어 뒤로가기: `canGoBack`이면 `goBack()`, 루트면 2초 내 더블탭 종료 토스트.
- 외부 링크 처리: 뉴스 아웃링크 등 도메인 밖 URL은 `onShouldStartLoadWithRequest`에서 가로채 `Linking.openURL`(외부 브라우저). 카카오/네이버 OAuth 리다이렉트 도메인은 WebView 내 허용 목록에 포함.
- 쿠키/세션: WebView 기본 쿠키 저장 사용(`sharedCookiesEnabled`). 웹 세션 만료 30일로 설정해 앱에서 재로그인 최소화.
- 상태바: 배경 #FFFFFF, dark-content. 노치 대응은 웹의 safe-area CSS가 처리(이미 초안에 포함).
- 스플래시: 화이트 배경 중앙에 로고 C 심볼(레드 말풍선). 앱 아이콘: 심볼 단독, 배경 #E0403C에 화이트 심볼 버전과 화이트 배경 버전 두 벌 제작 후 택1.

**푸시 알림 (FCM/APNs — expo-notifications)**
- 앱 최초 실행 시 권한 요청 → Expo push token 발급 → WebView가 로그인 상태일 때 `POST /api/push-token {token, platform}` 으로 서버 전달. DB: `push_tokens(user_id, token UNIQ, platform, updated_at)`.
- 서버 발송: notifications 생성 시점에 Expo Push API 호출 (배치 아님, 즉시). 발송 대상: 내 글 댓글, 대댓글, 팔로우한 전문가 새 칼럼, 관리자 공지. 마이페이지 알림 설정과 연동(유형별 on/off 컬럼 `notification_settings`).
- 푸시 탭 → 딥링크: data에 URL 담아 WebView `injectedJavaScript` 또는 uri 변경으로 해당 글 이동.

**스토어 심사 대비 (순수 WebView 리젝 방지)**
- 네이티브 요소 최소 3종 포함: ① 푸시 알림 ② pull-to-refresh ③ 오프라인 감지 화면(네트워크 끊김 시 로고+재시도 버튼 네이티브 렌더).
- iOS: 소셜 로그인 제공 시 Apple 로그인 추가 요구될 수 있음 → 이메일 로그인이 있으므로 1차 대응 가능하나, 리젝 시 Sign in with Apple 추가 (users.oauth_provider에 'apple' 확장 여지 있음).
- 계정 삭제 기능 필수(스토어 정책): 마이페이지 설정에 회원 탈퇴(soft delete) 웹 페이지로 구현 — 웹에 미리 포함할 것.
- 심사용 테스트 계정 준비, 개인정보처리방침·이용약관 URL(웹 /policy, /terms 정적 페이지 — 1차 MVP에 포함).

**빌드/배포**
- EAS Build로 iOS/Android 빌드, 버전은 웹과 독립 관리(셸은 거의 업데이트 없음 — 웹 배포만으로 기능 업데이트 완결되는 것이 이 구조의 핵심 장점).
- 사전 준비물: Apple 개발자 계정($99/년), Google Play 등록($25 1회), 도메인 HTTPS 필수.
