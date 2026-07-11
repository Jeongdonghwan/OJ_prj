import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import Svg, { Path } from "react-native-svg";

/** 네트워크 끊김 시 네이티브 렌더 화면 — 로고(그레이 변형) + 재시도 (§12 심사 대비 요소). */
export default function OfflineScreen({ onRetry }: { onRetry: () => void }) {
  return (
    <View style={styles.wrap}>
      <Svg width={72} height={66} viewBox="0 0 36 34">
        <Path
          d="M4,4 a4,4 0 0 0 -4,4 v14 a4,4 0 0 0 4,4 h5 l3,6 l5,-6 h15 a4,4 0 0 0 4,-4 v-14 a4,4 0 0 0 -4,-4 z"
          fill="#B0B8C1"
        />
        <Path
          d="M8,20 L14,13 L18,16 L26,7"
          fill="none"
          stroke="#FFFFFF"
          strokeWidth={3}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <Path
          d="M22.5,6.5 L26.5,6.5 L26.5,10.5"
          fill="none"
          stroke="#FFFFFF"
          strokeWidth={3}
          strokeLinecap="round"
        />
      </Svg>
      <Text style={styles.title}>인터넷 연결이 없어요</Text>
      <Text style={styles.desc}>연결 상태를 확인한 뒤 다시 시도해주세요.</Text>
      <Pressable style={styles.btn} onPress={onRetry}>
        <Text style={styles.btnText}>다시 시도</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#FFFFFF",
    padding: 28,
  },
  title: {
    marginTop: 18,
    fontSize: 17,
    fontWeight: "700",
    color: "#191F28",
  },
  desc: {
    marginTop: 6,
    fontSize: 13.5,
    color: "#8B95A1",
  },
  btn: {
    marginTop: 22,
    backgroundColor: "#E0403C",
    borderRadius: 14,
    paddingVertical: 13,
    paddingHorizontal: 36,
  },
  btnText: {
    color: "#FFFFFF",
    fontSize: 15,
    fontWeight: "700",
  },
});
