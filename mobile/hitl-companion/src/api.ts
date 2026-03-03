import { ApprovalItem } from "./types";

const baseUrl = process.env.EXPO_PUBLIC_OPENPANGO_NODE_URL || "http://localhost:3030";

export async function fetchApprovals(): Promise<ApprovalItem[]> {
  const res = await fetch(`${baseUrl}/api/hitl/pending`);
  if (!res.ok) throw new Error(`Failed to fetch approvals: ${res.status}`);
  return (await res.json()) as ApprovalItem[];
}

export async function approve(id: string): Promise<void> {
  const res = await fetch(`${baseUrl}/api/hitl/${id}/approve`, { method: "POST" });
  if (!res.ok) throw new Error(`Approve failed: ${res.status}`);
}

export async function reject(id: string): Promise<void> {
  const res = await fetch(`${baseUrl}/api/hitl/${id}/reject`, { method: "POST" });
  if (!res.ok) throw new Error(`Reject failed: ${res.status}`);
}
