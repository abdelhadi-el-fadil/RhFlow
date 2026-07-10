import axios from "axios"

import { API_BASE_URL } from "@/lib/api"
import type { AuthUser } from "@/lib/auth-types"
import { isJwtExpired } from "@/lib/jwt"

export const AUTH_TOKEN_KEY = "auth_token"
export const AUTH_USER_KEY = "auth_user"

export class ApiHttpError extends Error {
  status: number
  code: string | null
  payload: unknown

  constructor(
    status: number,
    message: string,
    payload: unknown,
    code: string | null = null,
  ) {
    super(message)
    this.name = "ApiHttpError"
    this.status = status
    this.code = code
    this.payload = payload
  }
}

type ApiResponse<T> = {
  data: T
  message?: string | null
}

type TokenResponse = {
  access_token: string
  token_type: string
}

function readCookie(name: string): string | null {
  if (typeof document === "undefined") {
    return null
  }

  const prefix = `${name}=`
  const cookie = document.cookie
    .split(";")
    .map((entry) => entry.trim())
    .find((entry) => entry.startsWith(prefix))

  if (!cookie) {
    return null
  }

  return decodeURIComponent(cookie.slice(prefix.length))
}

function extractErrorMessage(payload: unknown, fallback: string): string {
  if (
    typeof payload === "object" &&
    payload !== null &&
    "detail" in payload &&
    typeof (payload as { detail?: unknown }).detail === "string"
  ) {
    return (payload as { detail: string }).detail
  }

  if (
    typeof payload === "object" &&
    payload !== null &&
    "message" in payload &&
    typeof (payload as { message?: unknown }).message === "string"
  ) {
    return (payload as { message: string }).message
  }

  return fallback
}

function normalizeError(error: unknown): ApiHttpError {
  if (axios.isAxiosError(error)) {
    const payload = error.response?.data
    const status = error.response?.status ?? 0
    const code =
      typeof payload === "object" &&
      payload !== null &&
      "code" in payload &&
      typeof (payload as { code?: unknown }).code === "string"
        ? (payload as { code: string }).code
        : null

    return new ApiHttpError(
      status,
      extractErrorMessage(payload, error.message),
      payload,
      code,
    )
  }

  return new ApiHttpError(
    0,
    error instanceof Error ? error.message : "Unexpected error",
    error,
  )
}

export function setAuthToken(token: string): void {
  if (typeof window === "undefined") {
    return
  }

  localStorage.setItem(AUTH_TOKEN_KEY, token)
  document.cookie = `${AUTH_TOKEN_KEY}=${encodeURIComponent(token)}; path=/; max-age=${4 * 60 * 60}; samesite=lax`
}

export function clearAuthToken(): void {
  if (typeof window === "undefined") {
    return
  }

  localStorage.removeItem(AUTH_TOKEN_KEY)
  localStorage.removeItem(AUTH_USER_KEY)
  document.cookie = `${AUTH_TOKEN_KEY}=; path=/; max-age=0; samesite=lax`
  document.cookie = `${AUTH_USER_KEY}=; path=/; max-age=0; samesite=lax`
}

export function getAuthToken(): string | null {
  if (typeof window === "undefined") {
    return null
  }

  const fromStorage = localStorage.getItem(AUTH_TOKEN_KEY)
  if (fromStorage) {
    return fromStorage
  }

  const fromCookie = readCookie(AUTH_TOKEN_KEY)
  if (fromCookie) {
    localStorage.setItem(AUTH_TOKEN_KEY, fromCookie)
  }

  return fromCookie
}

export function getStoredUser(): AuthUser | null {
  if (typeof window === "undefined") {
    return null
  }

  const rawUser = localStorage.getItem(AUTH_USER_KEY)
  if (!rawUser) {
    return null
  }

  try {
    return JSON.parse(rawUser) as AuthUser
  } catch {
    return null
  }
}

export function setStoredUser(user: AuthUser | null): void {
  if (typeof window === "undefined") {
    return
  }

  if (!user) {
    localStorage.removeItem(AUTH_USER_KEY)
    return
  }

  localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user))
}

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
})

apiClient.interceptors.request.use((config) => {
  const token = getAuthToken()
  if (token) {
    config.headers = config.headers ?? {}
    ;(config.headers as Record<string, string>).Authorization = `Bearer ${token}`
  }

  if (typeof FormData !== "undefined" && config.data instanceof FormData && config.headers) {
    delete (config.headers as Record<string, string | undefined>)["Content-Type"]
  }

  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const normalizedError = normalizeError(error)

    if (normalizedError.status === 401 && typeof window !== "undefined") {
      clearAuthToken()
      if (window.location.pathname !== "/login") {
        window.location.assign("/login")
      }
    }

    return Promise.reject(normalizedError)
  },
)

export async function loginWithCredentials(email: string, password: string) {
  const formData = new URLSearchParams()
  formData.set("username", email)
  formData.set("password", password)

  const response = await apiClient.post<ApiResponse<TokenResponse>>(
    "/auth/login",
    formData,
    {
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
    },
  )

  const accessToken = response.data.data?.access_token
  if (!accessToken) {
    throw new ApiHttpError(500, "Missing access token in response", response.data)
  }

  return accessToken
}

export async function fetchCurrentUser() {
  const response = await apiClient.get<ApiResponse<AuthUser>>("/auth/me")
  return response.data.data
}

export function isAuthTokenValid(token: string | null): boolean {
  if (!token) {
    return false
  }

  return !isJwtExpired(token)
}

type ApiFetchOptions = RequestInit & {
  auth?: boolean
}

export async function apiFetch<T>(
  path: string,
  options: ApiFetchOptions = {},
): Promise<T> {
  const { auth = true, headers, ...rest } = options
  const requestHeaders = new Headers(headers)

  if (auth) {
    const token = getAuthToken()
    if (token && !requestHeaders.has("Authorization")) {
      requestHeaders.set("Authorization", `Bearer ${token}`)
    }
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...rest,
    headers: requestHeaders,
  })

  const contentType = response.headers.get("content-type") ?? ""
  const isJson = contentType.includes("application/json")
  const payload = isJson ? await response.json() : await response.text()

  if (response.status === 401) {
    clearAuthToken()
  }

  if (!response.ok) {
    const defaultMessage = `Request failed with status ${response.status}`
    const message =
      typeof payload === "object" &&
      payload !== null &&
      "detail" in payload &&
      typeof (payload as { detail?: unknown }).detail === "string"
        ? (payload as { detail: string }).detail
        : defaultMessage
    throw new ApiHttpError(response.status, message, payload)
  }

  return payload as T
}
