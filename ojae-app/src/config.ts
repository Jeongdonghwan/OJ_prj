/** 오재 웹 도메인 — EAS 빌드 시 EXPO_PUBLIC_SITE_URL로 주입 */
export const SITE_URL: string =
  process.env.EXPO_PUBLIC_SITE_URL ?? "https://ojae.kr";

export const SITE_HOST: string = new URL(SITE_URL).host;

/** WebView 안에서 열리도록 허용하는 호스트 (그 외는 외부 브라우저).
 *  카카오/네이버 OAuth 리다이렉트 도메인 포함 (CLAUDE.md §12). */
export const ALLOWED_HOSTS: string[] = [
  SITE_HOST,
  "kauth.kakao.com",
  "accounts.kakao.com",
  "kapi.kakao.com",
  "nid.naver.com",
  "openapi.naver.com",
];

export function isAllowedUrl(url: string): boolean {
  try {
    const host = new URL(url).host;
    return ALLOWED_HOSTS.some((h) => host === h || host.endsWith("." + h));
  } catch {
    return true; // about:blank 등 비정상 URL은 WebView에 맡김
  }
}
