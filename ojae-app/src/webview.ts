import type React from "react";
import WebViewDefault, { WebViewProps } from "react-native-webview";

/** 이 앱이 사용하는 WebView 명령 메서드 (useImperativeHandle로 노출됨). */
export interface WebViewHandle {
  goBack(): void;
  goForward(): void;
  reload(): void;
  injectJavaScript(script: string): void;
}

/** react-native-webview 13.x의 범용 .d.ts가 ref 타입을 노출하지 않아
 *  (플랫폼별 d.ts만 ForwardRefExoticComponent) 직접 지정한다. */
export const RNWebView = WebViewDefault as unknown as React.ForwardRefExoticComponent<
  WebViewProps & React.RefAttributes<WebViewHandle>
>;

export type { WebViewProps };
