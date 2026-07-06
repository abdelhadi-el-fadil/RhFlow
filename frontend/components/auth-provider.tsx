"use client"

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react"

import type { AuthUser } from "@/lib/auth-types"
import {
  clearAuthToken,
  fetchCurrentUser,
  getAuthToken,
  getStoredUser,
  loginWithCredentials,
  setAuthToken,
  setStoredUser,
} from "@/lib/http"

type AuthContextValue = {
  user: AuthUser | null
  isLoading: boolean
  signIn: (email: string, password: string) => Promise<AuthUser>
  signOut: () => void
  refreshUser: () => Promise<AuthUser | null>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const syncUser = useCallback(async () => {
    const token = getAuthToken()
    if (!token) {
      setUser(null)
      setIsLoading(false)
      return null
    }

    try {
      const currentUser = await fetchCurrentUser()
      setUser(currentUser)
      setStoredUser(currentUser)
      return currentUser
    } catch {
      clearAuthToken()
      setUser(null)
      return null
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    const cachedUser = getStoredUser()
    if (cachedUser) {
      setUser(cachedUser)
    }

    // The provider hydrates session state from the backend on first mount.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void syncUser()
  }, [syncUser])

  const signIn = useCallback(async (email: string, password: string) => {
    const token = await loginWithCredentials(email, password)
    setAuthToken(token)

    const currentUser = await fetchCurrentUser()
    setStoredUser(currentUser)
    setUser(currentUser)

    return currentUser
  }, [])

  const signOut = useCallback(() => {
    clearAuthToken()
    setUser(null)
  }, [])

  const refreshUser = useCallback(async () => {
    const currentUser = await syncUser()
    return currentUser
  }, [syncUser])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isLoading,
      signIn,
      signOut,
      refreshUser,
    }),
    [isLoading, refreshUser, signIn, signOut, user],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider")
  }

  return context
}