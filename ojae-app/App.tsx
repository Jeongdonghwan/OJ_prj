import React, { useCallback, useRef, useState } from "react";
import { SafeAreaView, StyleSheet } from "react-native";
import { StatusBar } from "expo-status-bar";
import NetInfo, { useNetInfo } from "@react-native-community/netinfo";
import * as Notifications from "expo-notifications";

import OfflineScreen from "./src/OfflineScreen";
import OjaeWebView from "./src/OjaeWebView";
import { usePushNavigation } from "./src/usePushNavigation";
import { usePushToken } from "./src/usePushToken";
import type { WebViewHandle } from "./src/webview";

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowBanner: true,
    shouldShowList: true,
    shouldPlaySound: false,
    shouldSetBadge: false,
  }),
});

export default function App() {
  const webviewRef = useRef<WebViewHandle | null>(null);
  const netInfo = useNetInfo();
  const [retryKey, setRetryKey] = useState(0);
  const pushToken = usePushToken();
  usePushNavigation(webviewRef);

  const retry = useCallback(() => {
    NetInfo.refresh().finally(() => setRetryKey((k) => k + 1));
  }, []);

  const offline = netInfo.isConnected === false;

  return (
    <SafeAreaView style={styles.root}>
      <StatusBar style="dark" backgroundColor="#FFFFFF" />
      {offline ? (
        <OfflineScreen onRetry={retry} />
      ) : (
        <OjaeWebView key={retryKey} ref={webviewRef} pushToken={pushToken} />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: "#FFFFFF" },
});
