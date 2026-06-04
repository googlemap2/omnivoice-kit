import { FormEvent, useMemo, useState } from "react";
import { testBackendConnection } from "./api";
import { loadDesktopConfig, normalizeBackendUrl, saveDesktopConfig } from "./config";
import type { ConnectionResult } from "./types";

const phases = [
  "Backend connection",
  "Media import",
  "Timeline core",
  "Subtitle and ASR",
  "Translation",
  "Voice and dubbing",
  "FFmpeg export",
];

function App() {
  const initialConfig = useMemo(() => loadDesktopConfig(), []);
  const [backendUrl, setBackendUrl] = useState(initialConfig.backendUrl);
  const [savedBackendUrl, setSavedBackendUrl] = useState(initialConfig.backendUrl);
  const [testing, setTesting] = useState(false);
  const [connection, setConnection] = useState<ConnectionResult | null>(null);

  async function handleTestConnection(event?: FormEvent) {
    event?.preventDefault();
    const normalized = normalizeBackendUrl(backendUrl);
    setBackendUrl(normalized);
    setTesting(true);
    setConnection(null);
    const result = await testBackendConnection(normalized);
    setTesting(false);
    setConnection(result);
    if (result.ok) {
      saveDesktopConfig({ backendUrl: normalized, theme: "system" });
      setSavedBackendUrl(normalized);
    }
  }

  const connected = connection?.ok;

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">OV</span>
          <div>
            <h1>OmniVoice Desktop</h1>
            <p>Video editor client</p>
          </div>
        </div>

        <nav className="phase-list" aria-label="Desktop build phases">
          {phases.map((phase, index) => (
            <div className={index === 0 ? "phase active" : "phase"} key={phase}>
              <span>{index + 1}</span>
              {phase}
            </div>
          ))}
        </nav>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">Phase 1</p>
            <h2>Connect desktop app to backend server</h2>
          </div>
          <div className={connected ? "status connected" : "status"}>
            <span />
            {connected ? "Connected" : "Disconnected"}
          </div>
        </header>

        <section className="panel connection-panel">
          <div>
            <h3>Backend URL</h3>
            <p>
              Desktop stores this URL locally and calls the FastAPI server directly. Use your local server,
              VPS, or ngrok URL.
            </p>
          </div>

          <form className="connection-form" onSubmit={handleTestConnection}>
            <label htmlFor="backend-url">Server URL</label>
            <div className="input-row">
              <input
                id="backend-url"
                value={backendUrl}
                onChange={(event) => setBackendUrl(event.target.value)}
                placeholder="https://your-backend.ngrok-free.dev"
                spellCheck={false}
              />
              <button type="submit" disabled={testing}>
                {testing ? "Testing..." : "Test & Save"}
              </button>
            </div>
          </form>

          {connection && (
            <div className={connection.ok ? "notice success" : "notice error"}>
              <strong>{connection.ok ? "Connection OK" : "Connection failed"}</strong>
              <span>{connection.message}</span>
              {connection.status > 0 && <code>HTTP {connection.status}</code>}
            </div>
          )}
        </section>

        <section className="grid">
          <article className="panel editor-preview">
            <div className="video-placeholder">
              <div className="play-button">▶</div>
              <p>Video preview will be added in Phase 2.</p>
            </div>
          </article>

          <article className="panel project-panel">
            <h3>Runtime config</h3>
            <dl>
              <div>
                <dt>Saved backend</dt>
                <dd>{savedBackendUrl}</dd>
              </div>
              <div>
                <dt>Health endpoint</dt>
                <dd>{savedBackendUrl}/health</dd>
              </div>
              <div>
                <dt>Mode</dt>
                <dd>Server-backed desktop client</dd>
              </div>
            </dl>
          </article>
        </section>
      </section>
    </main>
  );
}

export default App;
