const configuredApiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.trim()

function normalizeUrl(url: string): string {
  return url.endsWith("/") ? url.slice(0, -1) : url
}

function isLocalHost(hostname:  string): boolean {
  return hostname === "localhost" || hostname === "127.0.0.1"
}

function resolveApiBaseUrl(): string {
  if (typeof window === "undefined") {
    return normalizeUrl(configuredApiBaseUrl ?? "http://localhost:8000")
  }

  const browserProtocol = window.location.protocol === "https:" ? "https:" : "http:"
  const browserHost = window.location.hostname
  const browserDefault = `${browserProtocol}//${browserHost}:8000`

  if (!configuredApiBaseUrl) {
    return browserDefault
  }

  try {
    const parsed = new URL(configuredApiBaseUrl)
    if (isLocalHost(parsed.hostname) && !isLocalHost(browserHost)) {
      parsed.hostname = browserHost
      parsed.protocol = browserProtocol
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
