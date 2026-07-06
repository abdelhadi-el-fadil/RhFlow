"use client"

import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import {
  BookUser,
  Building2,
  ClipboardList,
  FileText,
  Gauge,
  HandCoins,
  LogOut,
  Menu,
  Settings,
  Users,
} from "lucide-react"
import { useMemo, useState } from "react"
import type { LucideIcon } from "lucide-react"

import { useAuth } from "@/components/auth-provider"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { getNavigationForRole } from "@/lib/navigation"

const ICON_BY_KEY: Record<string, LucideIcon> = {
  dashboard: Gauge,
  users: Users,
  directions: Building2,
  fiches: FileText,
  besoins: ClipboardList,
  projets: BookUser,
  offres: HandCoins,
  settings: Settings,
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const router = useRouter()
  const { user, signOut } = useAuth()
  const [mobileOpen, setMobileOpen] = useState(false)
  const roleLabel = user?.role ?? "-"
  const userLabel = user?.full_name ?? user?.email ?? "Utilisateur"
  const greetingName = user?.full_name?.split(" ")[0] ?? user?.email?.split("@")[0] ?? "utilisateur"
  const emailLabel = user?.email ?? ""

  const navigation = useMemo(() => getNavigationForRole(user?.role), [user?.role])

  const logout = () => {
    signOut()
    router.push("/login")
  }

  const nav = (
    <nav className="space-y-1">
      {navigation.primary.map((item) => {
        const active = pathname === item.href || pathname.startsWith(`${item.href}/`)
        const Icon = ICON_BY_KEY[item.icon]
        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={() => setMobileOpen(false)}
            className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${active ? "bg-primary text-primary-foreground" : "hover:bg-muted"}`}
          >
            <Icon className="size-4 text-sky-300" />
            {item.label}
          </Link>
        )
      })}
    </nav>
  )

  const footerNav = (
    <nav className="space-y-1">
      {navigation.footer.map((item) => {
        const active = pathname === item.href || pathname.startsWith(`${item.href}/`)
        const Icon = ICON_BY_KEY[item.icon]
        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={() => setMobileOpen(false)}
            className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${active ? "bg-primary text-primary-foreground" : "hover:bg-muted"}`}
          >
            <Icon className="size-4 text-sky-300" />
            {item.label}
          </Link>
        )
      })}
    </nav>
  )

  return (
    <div className="min-h-svh bg-muted/20 lg:grid lg:grid-cols-[280px_1fr]">
      <aside className="hidden border-r bg-background p-4 lg:flex lg:flex-col">
        <div className="space-y-4">
          <div>
            <p className="text-lg font-semibold">RhFlow</p>
            <p className="text-sm text-muted-foreground">Interface RH connectée</p>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="secondary">{roleLabel}</Badge>
            <span className="text-sm text-muted-foreground">{userLabel}</span>
          </div>
        </div>
        <Separator className="my-4" />
        {nav}
        <div className="mt-auto pt-4">
          {footerNav}
          <Separator className="my-4" />
          <Button variant="destructive" className="w-full justify-start" onClick={logout}>
            <LogOut className="text-sky-300" />
            Déconnexion
          </Button>
        </div>
      </aside>

      <div className="flex min-h-svh flex-col">
        <header className="flex items-center justify-between border-b bg-background px-4 py-3 lg:px-6">
          <div className="flex items-center gap-3">
            <Button variant="outline" size="icon" className="lg:hidden" onClick={() => setMobileOpen((value) => !value)}>
              <Menu className="text-sky-300" />
            </Button>
            <div>
              <p className="text-sm font-medium">Bonjour {greetingName}</p>
              <p className="text-xs text-muted-foreground">{emailLabel}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline">{roleLabel}</Badge>
            <Button variant="outline" onClick={logout} className="hidden sm:inline-flex">
              <LogOut className="text-sky-300" />
              Sortir
            </Button>
          </div>
        </header>

        {mobileOpen && (
          <div className="border-b bg-background p-4 lg:hidden">
            <Card className="p-4">
              {nav}
              <Separator className="my-4" />
              {footerNav}
              <Separator className="my-4" />
              <Button variant="destructive" className="w-full justify-start" onClick={logout}>
                <LogOut className="text-sky-300" />
                Déconnexion
              </Button>
            </Card>
          </div>
        )}

        <main className="flex-1 p-4 lg:p-6">{children}</main>
      </div>
    </div>
  )
}
