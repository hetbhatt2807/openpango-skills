import React, { useEffect, useState } from "react";
import {
  ActivityIndicator,
  FlatList,
  Pressable,
  SafeAreaView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { approve, fetchApprovals, reject } from "./src/api";
import { registerForPushNotificationsAsync } from "./src/notifications";
import { ApprovalItem } from "./src/types";

export default function App() {
  const [items, setItems] = useState<ApprovalItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchApprovals();
      setItems(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    registerForPushNotificationsAsync().catch(() => null);
  }, []);

  const onApprove = async (id: string) => {
    await approve(id);
    await load();
  };

  const onReject = async (id: string) => {
    await reject(id);
    await load();
  };

  return (
    <SafeAreaView style={styles.container}>
      <Text style={styles.title}>OpenPango HITL Approvals</Text>
      <Text style={styles.subtitle}>Review sensitive agent actions while away</Text>

      {loading ? <ActivityIndicator color="#fff" style={{ marginTop: 24 }} /> : null}
      {error ? <Text style={styles.error}>{error}</Text> : null}

      <FlatList
        data={items}
        keyExtractor={(item) => item.id}
        contentContainerStyle={{ paddingBottom: 24 }}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <Text style={styles.action}>{item.action}</Text>
            <Text style={styles.meta}>Risk: {item.risk.toUpperCase()}</Text>
            {item.cost ? <Text style={styles.meta}>Cost: {item.cost}</Text> : null}
            <Text style={styles.payload}>{item.payload}</Text>
            {item.diff ? <Text style={styles.diff}>Diff: {item.diff}</Text> : null}

            <View style={styles.row}>
              <Pressable style={[styles.btn, styles.reject]} onPress={() => onReject(item.id)}>
                <Text style={styles.btnText}>Reject</Text>
              </Pressable>
              <Pressable style={[styles.btn, styles.approve]} onPress={() => onApprove(item.id)}>
                <Text style={styles.btnText}>Approve</Text>
              </Pressable>
            </View>
          </View>
        )}
        ListEmptyComponent={!loading ? <Text style={styles.meta}>No pending approvals.</Text> : null}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0b1020",
    paddingHorizontal: 16,
    paddingTop: 12,
  },
  title: { color: "#fff", fontSize: 24, fontWeight: "700" },
  subtitle: { color: "#94a3b8", marginTop: 4, marginBottom: 10 },
  error: { color: "#fca5a5", marginVertical: 10 },
  card: {
    backgroundColor: "#111827",
    borderColor: "#1f2937",
    borderWidth: 1,
    borderRadius: 12,
    padding: 12,
    marginTop: 10,
  },
  action: { color: "#fff", fontSize: 16, fontWeight: "700" },
  meta: { color: "#93c5fd", marginTop: 6, fontSize: 12 },
  payload: { color: "#d1d5db", marginTop: 8, fontSize: 13 },
  diff: { color: "#c4b5fd", marginTop: 6, fontSize: 12 },
  row: { flexDirection: "row", gap: 10, marginTop: 12 },
  btn: {
    flex: 1,
    borderRadius: 10,
    paddingVertical: 10,
    alignItems: "center",
  },
  approve: { backgroundColor: "#16a34a" },
  reject: { backgroundColor: "#dc2626" },
  btnText: { color: "#fff", fontWeight: "700" },
});
