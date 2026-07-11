# ojae-app — 오재 Expo WebView 셸

웹(https://ojae.kr)을 감싸는 하이브리드 앱 셸. 기능 업데이트는 **웹 배포만으로 완결**되고,
이 셸은 푸시 알림·뒤로가기·오프라인 화면 등 네이티브 브릿지만 담당한다 (CLAUDE.md §12).

## 구성

| 파일 | 역할 |
|---|---|
| `App.tsx` | 상태바(white/dark) + 오프라인 감지 분기 + 푸시 훅 연결 |
| `src/OjaeWebView.tsx` | 본체 WebView — 쿠키 세션 공유, iOS 스와이프 뒤로가기, pull-to-refresh, 외부링크 → 기본 브라우저, Android 뒤로가기(더블탭 종료), 푸시 토큰 주입 |
| `src/config.ts` | `SITE_URL`(env), OAuth 도메인 허용 목록 |
| `src/usePushToken.ts` | 알림 권한 요청 → Expo push token 발급 |
| `src/usePushNavigation.ts` | 푸시 탭 → `data.url` 딥링크 (콜드 스타트 포함) |
| `src/OfflineScreen.tsx` | 네트워크 끊김 화면 (그레이 로고 + 재시도) — 심사 대비 네이티브 요소 |

**웹 ↔ 앱 푸시 토큰 핸드셰이크**: 앱이 `window.isOjaeApp=true`를 주입하고, 토큰 발급 후
`window.__ojaePushToken={token,platform}` 설정 + `ojae:pushtoken` 이벤트를 발생시킨다.
웹(base.html의 브릿지 스니펫)은 로그인 상태에서 이를 받아 `POST /api/push-token`으로 서버에 등록한다.

## 개발 실행

```bash
cd ojae-app
npm install
npm run typecheck                       # tsc --noEmit
EXPO_PUBLIC_SITE_URL=http://<로컬IP>:5000 npx expo start
# Expo Go 앱으로 QR 스캔 (같은 네트워크)
```

## EAS 빌드 (스토어 배포)

사전 준비: Apple 개발자 계정($99/년), Google Play 등록($25), 도메인 HTTPS.

```bash
npm i -g eas-cli
eas login
eas build:configure
eas build -p android --profile preview   # APK 테스트
eas build -p android                     # AAB (Play Store)
eas build -p ios                         # App Store
eas submit -p android / -p ios
```

`eas.json`의 프로덕션 프로필에 `EXPO_PUBLIC_SITE_URL=https://ojae.kr` env 지정.

## 스토어 심사 체크리스트 (§12)

- [x] 네이티브 요소 3종: 푸시 알림 / pull-to-refresh / 오프라인 감지 화면
- [x] 계정 삭제: 웹 `/my/withdraw` (마이페이지 → 회원 탈퇴)
- [x] 개인정보처리방침 `/policy` · 이용약관 `/terms`
- [ ] 심사용 테스트 계정 준비 (시드: `python -m scripts.seed`)
- [ ] 앱 아이콘/스플래시 PNG 제작: `assets/icon.png`(1024²), `assets/adaptive-icon.png`,
      `assets/splash.png` — 웹 레포 `app/static/img/favicon.svg`(레드 말풍선 심볼)를 원본으로 내보내기.
      레드 배경(#E0403C)+화이트 심볼 / 화이트 배경 두 벌 중 택1
- [ ] iOS 리젝 시 Sign in with Apple 추가 (이메일 로그인 있어 1차 대응 가능)
