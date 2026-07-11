import { useEffect, useState } from "react";
import { Platform } from "react-native";
import * as Device from "expo-device";
import * as Notifications from "expo-notifications";

export interface PushToken {
  token: string;
  platform: "ios" | "android";
}

/** 앱 최초 실행 시 권한 요청 → Expo push token 발급 (§12).
 *  시뮬레이터/권한 거부 시 null. */
export function usePushToken(): PushToken | null {
  const [pushToken, setPushToken] = useState<PushToken | null>(null);

  useEffect(() => {
    let mounted = true;

    async function register() {
      if (!Device.isDevice) return;

      if (Platform.OS === "android") {
        await Notifications.setNotificationChannelAsync("default", {
          name: "오재 알림",
          importance: Notifications.AndroidImportance.DEFAULT,
          lightColor: "#E0403C",
        });
      }

      const { status: existing } = await Notifications.getPermissionsAsync();
      let status = existing;
      if (existing !== "granted") {
        const req = await Notifications.requestPermissionsAsync();
        status = req.status;
      }
      if (status !== "granted") return;

      const { data } = await Notifications.getExpoPushTokenAsync();
      if (mounted && data) {
        setPushToken({
          token: data,
          platform: Platform.OS === "ios" ? "ios" : "android",
        });
      }
    }

    register().catch(() => undefined);
    return () => {
      mounted = false;
    };
  }, []);

  return pushToken;
}
