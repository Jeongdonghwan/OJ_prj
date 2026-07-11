import React, { forwardRef, useCallback, useEffect, useRef, useState } from "react";
import {
  BackHandler,
  Linking,
  Platform,
  StyleSheet,
  ToastAndroid,
} from "react-native";
import type { WebViewNavigation } from "react-native-webview";
import type { ShouldStartLoadRequest } from "react-native-webview/lib/WebViewTypes";

import { SITE_URL, isAllowedUrl } from "./config";
import type { PushToken } from "./usePushToken";
import { RNWebView, WebViewHandle } from "./webview";

interface Props {
  pushToken: PushToken | null;
}

/** 오재 본체 WebView (CLAUDE.md §12).
 *  - sharedCookiesEnabled: 웹 세션(30일) 그대로 사용, 재로그인 최소화
 *  - 외부 도메인은 기본 브라우저로, OAuth 도메인은 허용 목록으로 내부 처리
 *  - Android 하드웨어 뒤로가기: canGoBack이면 goBack, 루트면 2초 내 더블탭 종료
 *  - 로그인 상태의 웹에 푸시 토큰 주입 (window.__ojaePushToken + ojae:pushtoken 이벤트)
 */
const OjaeWebView = forwardRef<WebViewHandle, Props>(function OjaeWebView(
  { pushToken },
  ref,
) {
  const innerRef = useRef<WebViewHandle | null>(null);
  const canGoBackRef = useRef(false);
  const lastBackPress = useRef(0);
  const [webviewKey, setWebviewKey] = useState(0);

  const setRefs = useCallback(
    (node: WebViewHandle | null) => {
      innerRef.current = node;
      if (typeof ref === "function") ref(node);
      else if (ref) ref.current = node;
    },
    [ref],
  );

  useEffect(() => {
    if (Platform.OS !== "android") return;
    const sub = BackHandler.addEventListener("hardwareBackPress", () => {
      if (canGoBackRef.current && innerRef.current) {
        innerRef.current.goBack();
        return true;
      }
      const now = Date.now();
      if (now - lastBackPress.current < 2000) {
        return false; // 앱 종료
      }
      lastBackPress.current = now;
      ToastAndroid.show("한 번 더 누르면 종료됩니다", ToastAndroid.SHORT);
      return true;
    });
    return () => sub.remove();
  }, []);

  const onNavigationStateChange = useCallback((nav: WebViewNavigation) => {
    canGoBackRef.current = nav.canGoBack;
  }, []);

  const onShouldStartLoadWithRequest = useCallback(
    (request: ShouldStartLoadRequest): boolean => {
      if (isAllowedUrl(request.url)) return true;
      Linking.openURL(request.url).catch(() => undefined);
      return false; // 뉴스 아웃링크 등은 외부 브라우저로 (§12)
    },
    [],
  );

  const injectPushToken = useCallback(() => {
    if (!pushToken || !innerRef.current) return;
    innerRef.current.injectJavaScript(
      `window.__ojaePushToken=${JSON.stringify(pushToken)};` +
        `window.dispatchEvent(new Event('ojae:pushtoken'));true;`,
    );
  }, [pushToken]);

  return (
    <RNWebView
      key={webviewKey}
      ref={setRefs}
      source={{ uri: SITE_URL }}
      style={styles.webview}
      sharedCookiesEnabled
      allowsBackForwardNavigationGestures
      pullToRefreshEnabled
      decelerationRate="normal"
      setSupportMultipleWindows={false}
      injectedJavaScriptBeforeContentLoaded={"window.isOjaeApp=true;true;"}
      onLoadEnd={injectPushToken}
      onNavigationStateChange={onNavigationStateChange}
      onShouldStartLoadWithRequest={onShouldStartLoadWithRequest}
      onRenderProcessGone={() => setWebviewKey((k) => k + 1)}
      onContentProcessDidTerminate={() => setWebviewKey((k) => k + 1)}
    />
  );
});

const styles = StyleSheet.create({
  webview: { flex: 1, backgroundColor: "#FFFFFF" },
});

export default OjaeWebView;
