import type { AskResponse, MetricsResponse } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function askQuestion(question: string): Promise<AskResponse> {
  const response = await fetch(`${API_BASE_URL}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question })
  });

  if (!response.ok) {
    throw new Error(`Ask request failed with status ${response.status}`);
  }

  return response.json() as Promise<AskResponse>;
}

export async function fetchMetrics(): Promise<MetricsResponse> {
  const response = await fetch(`${API_BASE_URL}/metrics`);
  if (!response.ok) {
    throw new Error(`Metrics request failed with status ${response.status}`);
  }

  return response.json() as Promise<MetricsResponse>;
}
