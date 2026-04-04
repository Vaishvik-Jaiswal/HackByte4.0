import type { AskResponse, ThreadDetail } from "./types";

export function getApiBaseUrl(): string {
  const raw = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (raw) return raw.replace(/\/$/, "");
  return "http://127.0.0.1:8000";
}

export async function postAsk(question: string): Promise<AskResponse> {
  const base = getApiBaseUrl();
  const res = await fetch(`${base}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  const text = await res.text();
  if (!res.ok) {
    let detail = text;
    try {
      const j = JSON.parse(text) as { detail?: unknown };
      if (typeof j.detail === "string") detail = j.detail;
    } catch {
      /* keep raw */
    }
    throw new Error(detail || `HTTP ${res.status}`);
  }
  return JSON.parse(text) as AskResponse;
}

export async function getThread(threadId: string): Promise<ThreadDetail> {
  const base = getApiBaseUrl();
  const url = `${base}/threads/${encodeURIComponent(threadId)}`;
  const res = await fetch(url);
  const text = await res.text();
  if (!res.ok) {
    let detail = text;
    try {
      const j = JSON.parse(text) as { detail?: unknown };
      if (typeof j.detail === "string") detail = j.detail;
    } catch {
      /* keep raw */
    }
    throw new Error(detail || `HTTP ${res.status}`);
  }
  return JSON.parse(text) as ThreadDetail;
}
