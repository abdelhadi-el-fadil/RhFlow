import type { UserRole } from "@/lib/auth-types"

export type NavIconKey =
  | "dashboard"
  | "users"
  | "directions"
  | "fiches"
  | "besoins"
  | "projets"
  | "archives"
  | "settings"

export type NavItem = {
  label: string
  href?: string
  roles: UserRole[]
  icon: NavIconKey
  children?: NavItem[]
}

export type NavigationConfig = {
  primary: NavItem[]
  footer: NavItem[]
}

const NAV_PRIMARY: NavItem[] = [
  { label: "Tableau de bord", href: "/dashboard", roles: ["ADMIN", "DRH", "DIRECTEUR", "DG"], icon: "dashboard" },
  { label: "Utilisateurs", href: "/users", roles: ["ADMIN", "DRH"], icon: "users" },
  { label: "Directions", href: "/directions", roles: ["ADMIN", "DRH"], icon: "directions" },
  { label: "Fiches de poste", href: "/fiches-de-poste", roles: ["ADMIN", "DRH", "DIRECTEUR", "DG"], icon: "fiches" },
  { label: "Besoins", href: "/besoins", roles: ["ADMIN", "DRH", "DIRECTEUR"], icon: "besoins" },
  { label: "Projets", href: "/projets", roles: ["ADMIN", "DRH", "DIRECTEUR"], icon: "projets" },
  {
    label: "Archives",
    roles: ["ADMIN", "DRH", "DIRECTEUR", "DG"],
    icon: "archives",
    children: [
      {
        label: "Besoins de recrutement",
        href: "/archives/besoins",
        roles: ["ADMIN", "DRH", "DIRECTEUR", "DG"],
        icon: "archives",
      },
      {
        label: "Projets de recrutement",
        href: "/archives/projets",
        roles: ["ADMIN", "DRH", "DIRECTEUR", "DG"],
        icon: "archives",
      },
    ],
  },
]

const NAV_FOOTER: NavItem[] = [
  { label: "Paramètres", href: "/settings", roles: ["ADMIN", "DRH", "DIRECTEUR", "DG"], icon: "settings" },
]

export function getNavigationForRole(role: UserRole | null | undefined): NavigationConfig {
  if (!role) {
    return { primary: [], footer: [] }
  }

  return {
    primary: NAV_PRIMARY.filter((item) => item.roles.includes(role)).map((item) => ({
      ...item,
      children: item.children?.filter((child) => child.roles.includes(role)),
    })),
    footer: NAV_FOOTER.filter((item) => item.roles.includes(role)),
  }
}
