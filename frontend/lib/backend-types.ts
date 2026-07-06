import type { UserRole } from "@/lib/auth-types"

export type ApiResponse<T> = {
  data: T
  message?: string | null
}

export type PaginationMeta = {
  page: number
  page_size: number
  total_items: number
  total_pages: number
}

export type PaginatedResponse<T> = {
  data: T[]
  meta: PaginationMeta
}

export type UserResponse = {
  id: number
  email: string
  full_name: string | null
  gsm: string | null
  role: UserRole
  enabled: boolean
}

export type DirectionResponse = {
  id: number
  name: string
  code: string
  description: string | null
  director_id: number | null
  created_by_id: number | null
  updated_by_id: number | null
}

export type FicheStatus = "DRAFT" | "VALIDATED" | "ARCHIVED"

export type FicheDePosteResponse = {
  id: number
  title: string
  description: string
  missions: string
  required_skills: string
  experience_level: string
  status: FicheStatus
  direction_id: number
  validated_by_id: number | null
  created_by_id: number | null
  updated_by_id: number | null
}

export type BesoinStatus = "DRAFT" | "SUBMITTED" | "APPROVED" | "REJECTED"

export type BesoinRecrutementResponse = {
  id: number
  title: string
  description: string | null
  positions_count: number | null
  desired_date: string | null
  justification: string | null
  status: BesoinStatus
  rejection_reason: string | null
  fiche_de_poste_id: number
  submitted_by_id: number | null
  processed_by_id: number | null
  projet_id: number | null
  created_by_id: number | null
  updated_by_id: number | null
}

export type ProjetStatus = "DRAFT" | "ACTIVE" | "CLOSED"

export type ProjetRecrutementResponse = {
  id: number
  title: string
  description: string | null
  start_date: string
  expected_end_date: string
  email_subject: string
  status: ProjetStatus
  manager_id: number
  created_by_id: number | null
  updated_by_id: number | null
  besoins: BesoinRecrutementResponse[]
}

export type ProjetRecrutementCardResponse = {
  id: number
  title: string
  start_date: string
  status: ProjetStatus
  positions_count: number
  direction_name: string | null
  director_name: string | null
  email_subject: string
}

export type OffreStatus = "DRAFT" | "PUBLISHED" | "CLOSED"

export type OffreResponse = {
  id: number
  title: string
  description: string | null
  requirements: string | null
  published_at: string | null
  deadline: string | null
  status: OffreStatus
  besoin_id: number
  published_by_id: number | null
  created_by_id: number | null
  updated_by_id: number | null
}

export type OffrePublicResponse = {
  title: string
  description: string | null
  requirements: string | null
  published_at: string | null
  deadline: string | null
}
