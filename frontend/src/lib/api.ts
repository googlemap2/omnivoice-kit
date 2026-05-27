export type {
  AppSettings,
  HistoryEntry,
  Meta,
  ModelStatus,
  Option,
  TranslationProvider,
  Voice,
} from "../types/api";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "");

function apiHeaders(initHeaders?: HeadersInit, json = false): Headers {
  const headers = new Headers(initHeaders);
  headers.set("ngrok-skip-browser-warning", "true");
  if (json && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  return headers;
}

export async function apiJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: apiHeaders(init?.headers, true),
  });
  if (!response.ok) {
    throw new Error(await errorMessage(response));
  }
  return response.json() as Promise<T>;
}

export async function apiForm<T>(path: string, form: FormData, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    method: init?.method || "POST",
    body: form,
    headers: apiHeaders(init?.headers),
  });
  if (!response.ok) {
    throw new Error(await errorMessage(response));
  }
  return response.json() as Promise<T>;
}

export async function apiAudio(path: string, init?: RequestInit): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: apiHeaders(init?.headers),
  });
  if (!response.ok) {
    throw new Error(await errorMessage(response));
  }
  return response.blob();
}

export function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

async function errorMessage(response: Response) {
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    const body = await response.json().catch(() => null);
    return body?.detail || body?.message || `${response.status} ${response.statusText}`;
  }
  const text = await response.text().catch(() => "");
  return text || `${response.status} ${response.statusText}`;
}
