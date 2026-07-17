// Single source of truth for the backend origin. Override at build/run time with
// VITE_API_URL (e.g. a deployed backend); falls back to the local dev server.
export const API_BASE =
  import.meta.env.VITE_API_URL?.replace(/\/$/, '') || 'http://localhost:8000';

export const api = (path: string) => `${API_BASE}${path.startsWith('/') ? path : `/${path}`}`;
