const CONFIG_KEY = "omnivoice.desktop.config";
const DEFAULT_BACKEND_URL = "http://127.0.0.1:8000";

export type DesktopConfig = {
  backendUrl: string;
  theme: "system" | "dark" | "light";
};

export function normalizeBackendUrl(value: string): string {
  return value.trim().replace(/\/+$/, "");
}

export function loadDesktopConfig(): DesktopConfig {
  if (typeof window === "undefined") {
    return { backendUrl: DEFAULT_BACKEND_URL, theme: "system" };
  }
  const raw = window.localStorage.getItem(CONFIG_KEY);
  if (!raw) {
    return { backendUrl: DEFAULT_BACKEND_URL, theme: "system" };
  }
  try {
    const parsed = JSON.parse(raw) as Partial<DesktopConfig>;
    return {
      backendUrl: normalizeBackendUrl(parsed.backendUrl || DEFAULT_BACKEND_URL),
      theme: parsed.theme || "system",
    };
  } catch {
    return { backendUrl: DEFAULT_BACKEND_URL, theme: "system" };
  }
}

export function saveDesktopConfig(config: DesktopConfig): void {
  window.localStorage.setItem(
    CONFIG_KEY,
    JSON.stringify({ ...config, backendUrl: normalizeBackendUrl(config.backendUrl) }),
  );
}
