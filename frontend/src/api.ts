import type { CreateSessionResponse, MessageResponse } from "./types";

async function postJson<T>(url: string, body: unknown): Promise<T> {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`요청 실패 (${res.status}): ${url}`);
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
