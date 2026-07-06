import { NextRequest, NextResponse } from "next/server"

import { decodeJwtPayload, isJwtExpired } from "@/lib/jwt"

const AUTH_COOKIE = "auth_token"
const ADMIN_ROLES = new Set(["ADMIN", "DRH"])

function isPublicAsset(pathname: string) {
  return (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/favicon") ||
    pathname.startsWith("/images")
  )
}

function safeClaims(token: string | undefined) {
  if (!token || isJwtExpired(token)) {
    return null
  }

  return decodeJwtPayload(token)
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  if (isPublicAsset(pathname)) {
    return NextResponse.next()
  }

  const token = request.cookies.get(AUTH_COOKIE)?.value
  const claims = safeClaims(token)

  if (pathname === "/login") {
    if (claims) {
      return NextResponse.redirect(new URL("/dashboard", request.url))
    }

    return NextResponse.next()
  }

  if (!claims) {
    return NextResponse.redirect(new URL("/login", request.url))
  }

  if (pathname.startsWith("/admin") && !ADMIN_ROLES.has(claims.role ?? "")) {
    return NextResponse.redirect(new URL("/403", request.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
}