import type {
  AskExamplesResponse,
  AskRequestPayload,
  AskResponse,
  AuditRecord,
  HealthResponse,
  MetricsResponse
} from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function askQuestion(payload: AskRequestPayload | string): Promise<AskResponse> {
  const body = typeof payload === "string" ? { question: payload } : payload;

  return apiRequest<AskResponse>("/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
}

export async function fetchAskExamples(): Promise<AskExamplesResponse> {
  return apiRequest<AskExamplesResponse>("/ask/examples");
}

export async function fetchMetrics(): Promise<MetricsResponse> {
  return apiRequest<MetricsResponse>("/metrics");
}

export async function fetchHealth(): Promise<HealthResponse> {
  return apiRequest<HealthResponse>("/health");
}

export async function fetchAuditRecord(queryId: string): Promise<AuditRecord> {
  return apiRequest<AuditRecord>(`/queries/${encodeURIComponent(queryId)}`);
}

async function apiRequest<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, options);

  if (!response.ok) {
    throw new Error(await errorMessage(response));
  }

  return response.json() as Promise<T>;
}

async function errorMessage(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: unknown };
    if (typeof body.detail === "string") {
      return body.detail;
    }
  } catch {
    return `API request failed with status ${response.status}`;
  }

  return `API request failed with status ${response.status}`;
}
