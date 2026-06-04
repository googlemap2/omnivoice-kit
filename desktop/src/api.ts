import type { BackendHealth, ConnectionResult } from "./types";
import { normalizeBackendUrl } from "./config";

function apiHeaders(initHeaders?: HeadersInit): Headers {
  const headers = new Headers(initHeaders);
  headers.set("ngrok-skip-browser-warning", "true");
  return headers;
}

async function errorMessage(response: Response): Promise<string> {
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    const body = await response.json().catch(() => null);
    const detail = body?.detail || body?.message;
    if (typeof detail === "string") return detail;
    if (detail) return JSON.stringify(detail);
  }
  const text = await response.text().catch(() => "");
  return text || `${response.status} ${response.statusText}`;
}

export async function testBackendConnection(backendUrl: string): Promise<ConnectionResult> {
  const baseUrl = normalizeBackendUrl(backendUrl);
  if (!baseUrl) {
    return { ok: false, status: 0, message: "Backend URL is required." };
  }

  try {
    const response = await fetch(`${baseUrl}/health`, {
      method: "GET",
      headers: apiHeaders(),
    });
    if (!response.ok) {
      return { ok: false, status: response.status, message: await errorMessage(response) };
    }
    const data = (await response.json().catch(() => ({}))) as BackendHealth;
    return {
      ok: true,
      status: response.status,
      message: data.status ? `Backend status: ${data.status}` : "Backend connection OK.",
      data,
    };
  } catch (error) {
    return {
      ok: false,
      status: 0,
      message: error instanceof Error ? error.message : "Could not connect to backend.",
    };
  }
}
