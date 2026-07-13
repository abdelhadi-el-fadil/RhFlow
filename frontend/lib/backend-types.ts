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
  signature_key: string | null
  signature_content_type: string | null
  role: UserRole
  enabled: boolean
}

export type UserSignatureResponse = {
  signature_key: string
  signature_content_type: string
  url: string
}

export type DirectionResponse = {
  id: number
  name: string
  code: string
  description: string | null
  director_id: number | null
  director_name: string | null
  fiche_count: number
  created_by_id: number | null
  updated_by_id: number | null
}

export type FicheDePosteResponse = {
  id: number
  title: string
  main_activities: string
  missions: string
  experience_level: string
  formation_domain: string | null
  education_level: string | null
  technical_skills: string | null
  managerial_skills: string | null
  direction_id: number
  direction_name: string | null
  validated_by_id: number | null
  created_by_id: number | null
  updated_by_id: number | null
}

export type BesoinStatus = "DRAFT" | "SUBMITTED" | "APPROVED" | "REJECTED"
export type BesoinPriority = "HAUTE" | "NORMALE" | "BASSE"

export type BesoinRecrutementResponse = {
  id: number
  title: string
  description: string | null
  positions_count: number | null
  desired_date: string | null
  justification: string | null
  location: string | null
  recruitment_reason: string | null
  priority: BesoinPriority
  status: BesoinStatus
  rejection_reason: string | null
  fiche_de_poste_id: number
  fiche_title: string | null
  direction_name: string | null
  director_name: string | null
  requester_name: string | null
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
  manager_id: number
  manager_name: string | null
  status: ProjetStatus
  besoin_recrutement_id: number | null
  besoin_title: string | null
  fiche_de_poste_id: number | null
  fiche_title: string | null
  nombre_postes: number | null
  email_subject: string | null
  direction_name: string | null
  director_name: string | null
  created_by_id: number | null
  updated_by_id: number | null
  besoins: BesoinRecrutementResponse[]
}

export type ProjetRecrutementCardResponse = {
  id: number
  title: string
  start_date: string
  status: ProjetStatus
  nombre_postes: number | null
  direction_name: string | null
  director_name: string | null
  manager_name: string | null
  fiche_title: string | null
  besoin_title: string | null
  email_subject: string | null
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
