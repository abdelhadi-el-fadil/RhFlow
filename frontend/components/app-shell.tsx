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
  PanelLeftClose,
  PanelLeftOpen,
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
  const [sidebarExpanded, setSidebarExpanded] = useState(false)
  const roleLabel = user?.role ?? "-"
  const userLabel = user?.full_name ?? user?.email ?? "Utilisateur"
  const greetingName = user?.full_name?.split(" ")[0] ?? user?.email?.split("@")[0] ?? "utilisateur"
  const emailLabel = user?.email ?? ""

  const navigation = useMemo(() => getNavigationForRole(user?.role), [user?.role])

  const logout = () => {
    signOut()
    router.push("/login")
  }

  const nav = (expanded: boolean, onNavigate: () => void = () => undefined) => (
    <nav className="space-y-1">
      {navigation.primary.map((item) => {
        const active = pathname === item.href || pathname.startsWith(`${item.href}/`)
        const Icon = ICON_BY_KEY[item.icon]
        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={onNavigate}
            className={`group flex items-center rounded-lg px-3 py-2 text-sm transition-all duration-200 motion-reduce:transition-none ${expanded ? "justify-start gap-3" : "justify-center"} ${active ? "bg-black/15 text-black ring-1 ring-black/20 shadow-sm" : "text-black hover:bg-black/10 hover:ring-1 hover:ring-black/10"}`}
            title={!expanded ? item.label : undefined}
          >
            <Icon
              className="size-4 shrink-0 text-teal-600"
              strokeWidth={2.75}
            />
            <span
              className={`overflow-hidden whitespace-nowrap transition-all duration-200 motion-reduce:transition-none ${expanded ? "max-w-48 opacity-100" : "max-w-0 opacity-0"}`}
            >
              {item.label}
            </span>
          </Link>
        )
      })}
    </nav>
  )

  const footerNav = (expanded: boolean, onNavigate: () => void = () => undefined) => (
    <nav className="space-y-1">
      {navigation.footer.map((item) => {
        const active = pathname === item.href || pathname.startsWith(`${item.href}/`)
        const Icon = ICON_BY_KEY[item.icon]
        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={onNavigate}
            className={`group flex items-center rounded-lg px-3 py-2 text-sm transition-all duration-200 motion-reduce:transition-none ${expanded ? "justify-start gap-3" : "justify-center"} ${active ? "bg-black/15 text-black ring-1 ring-black/20 shadow-sm" : "text-black hover:bg-black/10 hover:ring-1 hover:ring-black/10"}`}
            title={!expanded ? item.label : undefined}
          >
            <Icon
              className="size-4 shrink-0 text-teal-600"
              strokeWidth={2.75}
            />
            <span
              className={`overflow-hidden whitespace-nowrap transition-all duration-200 motion-reduce:transition-none ${expanded ? "max-w-48 opacity-100" : "max-w-0 opacity-0"}`}
            >
              {item.label}
            </span>
          </Link>
        )
      })}
    </nav>
  )

  return (
    <div className="min-h-svh bg-transparent lg:flex">
      <aside
        className={`sticky top-0 hidden h-svh shrink-0 border-r border-sky-300/70 bg-gradient-to-br from-sky-200 via-blue-200 to-cyan-100 p-4 shadow-sm lg:flex lg:flex-col lg:rounded-none lg:transition-[width] lg:duration-300 lg:ease-out lg:motion-reduce:transition-none ${sidebarExpanded ? "lg:w-72" : "lg:w-20"}`}
      >
        <div className="mb-2 flex items-center justify-between gap-2">
          <div className={`min-w-0 transition-opacity duration-200 ${sidebarExpanded ? "opacity-100" : "opacity-0"}`}>
            <p className="truncate text-lg font-semibold text-black">RhFlow</p>
            <p className="truncate text-sm text-black/70">Interface RH connectee</p>
          </div>
          <Button
            type="button"
            size="icon-sm"
            variant="ghost"
            aria-label={sidebarExpanded ? "Reduire la barre laterale" : "Etendre la barre laterale"}
            onClick={() => setSidebarExpanded((value) => !value)}
            className="text-black hover:bg-black/10"
          >
            {sidebarExpanded ? (
              <PanelLeftClose className="text-teal-950" strokeWidth={2.75} />
            ) : (
              <PanelLeftOpen className="text-teal-950" strokeWidth={2.75} />
            )}
          </Button>
        </div>

        <div className={`mb-2 flex items-center gap-2 overflow-hidden transition-all duration-200 ${sidebarExpanded ? "max-h-16 opacity-100" : "max-h-0 opacity-0"}`}>
          <Badge variant="secondary">{roleLabel}</Badge>
          <span className="truncate text-sm text-black/70">{userLabel}</span>
        </div>

        <Separator className="my-4 bg-black/15" />
        {nav(sidebarExpanded)}
        <div className="mt-auto pt-4">
          {footerNav(sidebarExpanded)}
          <Separator className="my-4 bg-black/15" />
          <Button
            variant="destructive"
            className={`w-full bg-red-400 text-white hover:bg-red-500 ${sidebarExpanded ? "justify-start" : "justify-center"}`}
            onClick={logout}
            title={!sidebarExpanded ? "Deconnexion" : undefined}
          >
            <LogOut className="text-white" strokeWidth={2.75} />
            <span className={`overflow-hidden whitespace-nowrap transition-all duration-200 ${sidebarExpanded ? "max-w-28 opacity-100" : "max-w-0 opacity-0"}`}>
              Deconnexion
            </span>
          </Button>
        </div>
      </aside>

      <div className="flex min-h-svh min-w-0 flex-1 flex-col bg-sky-200/50">
        <header className="z-10 flex items-center justify-between border-b border-sky-300/70 bg-gradient-to-br from-sky-200 via-blue-200 to-cyan-100 px-4 py-3 backdrop-blur-sm lg:rounded-none lg:px-6">
          <div className="flex items-center gap-3">
            <Button variant="outline" size="icon" className="lg:hidden" onClick={() => setMobileOpen((value) => !value)}>
              <Menu className="text-teal-600" />
            </Button>
            <div>
              <p className="text-sm font-semibold text-slate-900">Bonjour {greetingName}</p>
              <p className="text-xs text-slate-700">{emailLabel}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline">{roleLabel}</Badge>
            <Button variant="outline" onClick={logout} className="hidden sm:inline-flex">
              <LogOut className="text-teal-600" />
              Sortir
            </Button>
          </div>
        </header>

        {mobileOpen && (
          <div className="border-b border-sky-300/40 bg-gradient-to-br from-sky-100/90 via-blue-100/90 to-cyan-100/90 p-4 lg:hidden">
            <Card className="p-4">
              {nav(true, () => setMobileOpen(false))}
              <Separator className="my-4" />
              {footerNav(true, () => setMobileOpen(false))}
              <Separator className="my-4" />
              <Button variant="destructive" className="w-full justify-start bg-red-400 text-white hover:bg-red-500" onClick={logout}>
                <LogOut className="text-white" strokeWidth={2.75} />
                Deconnexion
              </Button>
            </Card>
          </div>
        )}

        <main className="page-enter flex-1 p-4 lg:p-6">{children}</main>
      </div>
    </div>
  )
}