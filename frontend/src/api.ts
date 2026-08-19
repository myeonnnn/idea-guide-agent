import type { CreateSessionResponse, MessageResponse } from "./types";

const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`요청 실패 (${res.status}): ${path}`);
  }
  return res.json();
}

export function createSession(idea: string): Promise<CreateSessionResponse> {
  return postJson("/session", { idea });
}

export function sendMessage(
  sessionId: string,
  message: string
): Promise<MessageResponse> {
  return postJson(`/session/${sessionId}/message`, { message });
}
