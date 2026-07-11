import { RefObject, useEffect } from "react";
import * as Notifications from "expo-notifications";

import { SITE_URL, isAllowedUrl } from "./config";
import type { WebViewHandle } from "./webview";

function resolveUrl(raw: unknown): string | null {
  if (typeof raw !== "string" || !raw) return null;
  if (raw.startsWith("/")) return SITE_URL + raw;
  if (raw.startsWith("http") && isAllowedUrl(raw)) return raw;
  return null;
}

/** 푸시 탭 → data.url 딥링크로 WebView 이동 (§12). 콜드 스타트 포함. */
export function usePushNavigation(webviewRef: RefObject<WebViewHandle | null>): void {
  useEffect(() => {
    function navigate(response: Notifications.NotificationResponse | null) {
      const url = resolveUrl(
        response?.notification.request.content.data?.url,
      );
      if (url && webviewRef.current) {
        webviewRef.current.injectJavaScript(
          `location.href=${JSON.stringify(url)};true;`,
        );
      }
    }

    // 앱이 꺼진 상태에서 푸시로 실행된 경우
    Notifications.getLastNotificationResponseAsync().then(navigate);

    const sub = Notifications.addNotificationResponseReceivedListener(navigate);
    return () => sub.remove();
  }, [webviewRef]);
}
