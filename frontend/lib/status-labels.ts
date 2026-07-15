import type {
  BesoinStatus,
  OffreStatus,
  ProjetStatus,
} from "@/lib/backend-types"

export function badgeVariantFromBesoinStatus(status: BesoinStatus) {
  switch (status) {
    case "SUBMITTED":
      return "outline" as const
    case "APPROVED":
      return "default" as const
    case "REJECTED":
      return "destructive" as const
  }
}

export function labelFromBesoinStatus(status: BesoinStatus) {
  switch (status) {
    case "SUBMITTED":
      return "En cours"
    case "APPROVED":
      return "Approuvé"
    case "REJECTED":
      return "Rejeté"
  }
}

export function badgeVariantFromProjetStatus(status: ProjetStatus) {
  switch (status) {
    case "ACTIVE":
      return "default" as const
    case "CLOSED":
      return "outline" as const
  }
}

export function labelFromProjetStatus(status: ProjetStatus) {
  switch (status) {
    case "ACTIVE":
      return "Ouvert"
    case "CLOSED":
      return "Fermé"
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

export function labelFromOffreStatus(status: OffreStatus) {
  switch (status) {
    case "DRAFT":
      return "Brouillon"
    case "PUBLISHED":
      return "Publié"
    case "CLOSED":
      return "Fermé"
  }
}
