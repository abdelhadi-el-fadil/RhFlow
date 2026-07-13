import type {
  BesoinStatus,
  OffreStatus,
  ProjetStatus,
} from "@/lib/backend-types"

export function badgeVariantFromBesoinStatus(status: BesoinStatus) {
  switch (status) {
    case "DRAFT":
      return "secondary" as const
    case "SUBMITTED":
      return "outline" as const
    case "APPROVED":
      return "default" as const
    case "REJECTED":
      return "destructive" as const
  }
}

export function badgeVariantFromProjetStatus(status: ProjetStatus) {
  switch (status) {
    case "DRAFT":
      return "secondary" as const
    case "ACTIVE":
      return "default" as const
    case "CLOSED":
      return "outline" as const
  }
}

export function badgeVariantFromOffreStatus(status: OffreStatus) {
  switch (status) {
    case "DRAFT":
      return "secondary" as const
    case "PUBLISHED":
      return "default" as const
    case "CLOSED":
      return "outline" as const
  }
}
