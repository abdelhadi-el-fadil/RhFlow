const configuredApiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.trim()

function normalizeUrl(url: string): string {
  return url.endsWith("/") ? url.slice(0, -1) : url
}

function isLocalHost(hostname:  string): boolean {
  return hostname === "localhost" || hostname === "127.0.0.1"
}

function isInternalHost(hostname: string): boolean {
  return hostname === "backend" || hostname === "0.0.0.0"
}

function isRelativePath(url: string): boolean {
  return url.startsWith("/")
}

function defaultBrowserApiBaseUrl(browserHost: string): string {
  if (isLocalHost(browserHost)) {
    return `http://${browserHost}:8000`
  }

  // On non-local hosts, default to same-origin reverse proxy (/api).
  // This avoids mixed-content and unreachable localhost/backend hostnames.
  return `${window.location.origin}/api`
}

function resolveApiBaseUrl(): string {
  if (typeof window === "undefined") {
    return normalizeUrl(configuredApiBaseUrl ?? "http://localhost:8000")
  }

  const browserHost = window.location.hostname
  const browserDefault = defaultBrowserApiBaseUrl(browserHost)

  if (!configuredApiBaseUrl) {
    return browserDefault
  }

  if (isRelativePath(configuredApiBaseUrl)) {
    return normalizeUrl(`${window.location.origin}${configuredApiBaseUrl}`)
  }

  try {
    const parsed = new URL(configuredApiBaseUrl)
    if ((isLocalHost(parsed.hostname) || isInternalHost(parsed.hostname)) && !isLocalHost(browserHost)) {
      if (window.location.protocol === "https:") {
        return normalizeUrl(`${window.location.origin}/api`)
      }

      parsed.hostname = browserHost
      parsed.protocol = window.location.protocol
      if (!parsed.port) {
        parsed.port = "8000"
      }

      return normalizeUrl(parsed.toString())
    }

    return normalizeUrl(configuredApiBaseUrl)
  } catch {
    return browserDefault
  }
}

export const API_BASE_URL = resolveApiBaseUrl()
