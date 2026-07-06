"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"

import type { UserRole } from "@/lib/auth-types"
import { useAuth } from "@/components/auth-provider"

export function RoleGate({
  roles,
  children,
}: {
  roles: UserRole[]
  children: React.ReactNode
}) {
  const router = useRouter()
  const { user, isLoading } = useAuth()

  useEffect(() => {
    if (!isLoading && user && !roles.includes(user.role)) {
      router.replace("/403")
    }
  }, [isLoading, router, roles, user])

  if (isLoading || !user || !roles.includes(user.role)) {
    return null
  }

  return <>{children}</>
}
