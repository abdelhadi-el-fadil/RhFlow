export type UserRole = "ADMIN" | "DRH" | "DIRECTEUR" | "DG"

export type AuthUser = {
  id: number
  email: string
  full_name: string | null
  gsm: string | null
  role: UserRole
  enabled: boolean
}