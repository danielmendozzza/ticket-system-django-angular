const DEFAULT_DEV_API_BASE = 'http://127.0.0.1:8000/api';

export function getApiBase(): string {
  if (typeof window === 'undefined' || !window.location) {
    return DEFAULT_DEV_API_BASE;
  }

  const { hostname, port, origin } = window.location;
  const isAngularDevServer =
    (hostname === 'localhost' || hostname === '127.0.0.1') && port === '4200';

  if (isAngularDevServer) {
    return DEFAULT_DEV_API_BASE;
  }

  return `${origin}/api`;
}
