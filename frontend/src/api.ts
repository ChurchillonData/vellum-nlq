import type {
  AskExamplesResponse,
  AskRequestPayload,
  AskResponse,
  AuditRecord,
  MetricsResponse
} from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function askQuestion(payload: AskRequestPayload | string): Promise<AskResponse> {
  const body = typeof payload === "string" ? { question: payload } : payload;

  const response = await fetch(`${API_BASE_URL}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });

  if (!response.ok) {
    throw new Error(`Ask request failed with status ${response.status}`);
  }

  return response.json() as Promise<AskResponse>;
}

export async function fetchAskExamples(): Promise<AskExamplesResponse> {
  const response = await fetch(`${API_BASE_URL}/ask/examples`);
  if (!response.ok) {
    throw new Error(`Ask examples request failed with status ${response.status}`);
  }

  return response.json() as Promise<AskExamplesResponse>;
}

export async function fetchMetrics(): Promise<MetricsResponse> {
  const response = await fetch(`${API_BASE_URL}/metrics`);
  if (!response.ok) {
    throw new Error(`Metrics request failed with status ${response.status}`);
  }

  return response.json() as Promise<MetricsResponse>;
}

export async function fetchAuditRecord(queryId: string): Promise<AuditRecord> {
  const response = await fetch(`${API_BASE_URL}/queries/${encodeURIComponent(queryId)}`);
  if (!response.ok) {
    throw new Error(`Audit lookup failed with status ${response.status}`);
  }

  return response.json() as Promise<AuditRecord>;
}
