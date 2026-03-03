export type ApprovalItem = {
  id: string;
  action: string;
  risk: "low" | "medium" | "high";
  cost?: string;
  diff?: string;
  payload: string;
  createdAt: string;
};
