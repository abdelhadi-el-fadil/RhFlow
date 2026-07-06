import type { UserRole } from "@/lib/auth-types"

export type JwtClaims = {
  sub?: string
  exp?: number
  role?: UserRole
  email?: string
}

function decodeBase64Url(value: string): string | null {
  const normalized = value.replace(/-/g, "+").replace(/_/g, "/")
  const padding = "=".repeat((4 - (normalized.length % 4)) % 4)
  const base64 = `${normalized}${padding}`

  try {
    if (typeof atob === "function") {
      return atob(base64)
    }

    if (typeof Buffer !== "undefined") {
      return Buffer.from(base64, "base64").toString("utf8")
    }
  } catch {
    return null
  }

  return null
}

export function decodeJwtPayload(token: string): JwtClaims | null {
  const parts = token.split(".")
  if (parts.length < 2) {
    return null
  }

  const payload = decodeBase64Url(parts[1])
  if (!payload) {
    return null
  }

  try {
    return JSON.parse(payload) as JwtClaims
  } catch {
    return null
  }
}

export function isJwtExpired(token: string, now = Date.now()): boolean {
  const payload = decodeJwtPayload(token)
  if (!payload?.exp) {
    return false
  }

  return payload.exp * 1000 <= now
}