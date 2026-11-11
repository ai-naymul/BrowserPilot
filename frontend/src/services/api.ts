// Single place that knows where the API lives and how to authenticate to it.
// Every request goes through here so the token can't be forgotten on a new call.

const TOKEN_KEY = 'browserpilot_token';

/** Vite dev server serves the UI on :5173 while the API is on :8000. In prod the
 *  API serves the built SPA, so same-origin is correct (and keeps the Origin
 *  header on the allowlist). */
export function apiBase(): string {
  return window.location.port === '5173' ? 'http://localhost:8000' : window.location.origin;
}

export function apiToken(): string {
  return localStorage.getItem(TOKEN_KEY) || (import.meta.env.VITE_API_TOKEN as string) || '';
}

export function wsUrl(path: string): string {
  const isDev = window.location.port === '5173';
  const host = isDev ? 'localhost:8000' : window.location.host;
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
  const token = apiToken();
  // Browsers cannot set headers on a WebSocket handshake, so the token rides in
  // the query string for /ws and /stream only.
  return `${proto}://${host}${path}${token ? `?token=${encodeURIComponent(token)}` : ''}`;
}

/** fetch() with the API token attached; prompts once for the token on 401. */
export async function apiFetch(path: string, init: RequestInit = {}, retried = false): Promise<Response> {
  const token = apiToken();
  const headers = new Headers(init.headers);
  if (token) headers.set('X-API-Token', token);

  const res = await fetch(`${apiBase()}${path}`, { ...init, headers });

  if (res.status === 401 && !retried) {
    const entered = window.prompt('BrowserPilot API token (BROWSERPILOT_TOKEN):');
    if (entered?.trim()) {
      localStorage.setItem(TOKEN_KEY, entered.trim());
      return apiFetch(path, init, true);
    }
  }
  return res;
}
