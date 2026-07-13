"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
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
  X,
} from "lucide-react";
import { useMemo, useState } from "react";
import type { LucideIcon } from "lucide-react";

import { useAuth } from "@/components/auth-provider";
import { Toaster } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { getNavigationForRole } from "@/lib/navigation";

const ICON_BY_KEY: Record<string, LucideIcon> = {
  dashboard: Gauge,
  users: Users,
  directions: Building2,
  fiches: FileText,
  besoins: ClipboardList,
  projets: BookUser,
  offres: HandCoins,
  settings: Settings,
};

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, signOut } = useAuth();
  const [navOpen, setNavOpen] = useState(false);
  const roleLabel = user?.role ?? "-";
  const userLabel = user?.full_name ?? user?.email ?? "Utilisateur";
  const greetingName =
    user?.full_name?.split(" ")[0] ??
    user?.email?.split("@")[0] ??
    "utilisateur";
  const emailLabel = user?.email ?? "";

  const navigation = useMemo(
    () => getNavigationForRole(user?.role),
    [user?.role],
  );

  const closeNav = () => setNavOpen(false);

  const logout = () => {
    signOut();
    router.push("/login");
  };

  const nav = (items: typeof navigation.primary) => (
    <nav className="space-y-1">
      {items.map((item) => {
        const active =
          pathname === item.href || pathname.startsWith(`${item.href}/`);
        const Icon = ICON_BY_KEY[item.icon];
        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={closeNav}
            className={`group flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-all duration-200 motion-reduce:transition-none ${active ? "bg-black/15 text-black ring-1 ring-black/20 shadow-sm" : "text-black hover:bg-black/10 hover:ring-1 hover:ring-black/10"}`}
          >
            <Icon
              className="size-4 shrink-0 text-sky-800"
              strokeWidth={2.75}
            />
            <span className="whitespace-nowrap">{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );

  return (
    <div className="min-h-svh bg-transparent">
      <header className="sticky top-0 z-20 flex items-center justify-between border-b border-green-300/70 bg-[#41719d] px-4 py-3 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <Button
            type="button"
            variant="outline"
            size="icon"
            aria-label={navOpen ? "Fermer le menu" : "Ouvrir le menu"}
            onClick={() => setNavOpen((value) => !value)}
          >
            <Menu className="text-green-800" />
          </Button>
          <div>
            <p className="text-sm font-semibold text-slate-900">
              Bonjour {greetingName}
            </p>
            <p className="text-xs text-white/90">{emailLabel}</p>{" "}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline">{roleLabel}</Badge>
          <Button
            variant="outline"
            onClick={logout}
            className="hidden sm:inline-flex"
          >
            <LogOut className="text-green-800" />
            Sortir
          </Button>
        </div>
      </header>

      {/* Backdrop */}
      <div
        aria-hidden="true"
        onClick={closeNav}
        className={`fixed inset-0 z-30 bg-black/30 transition-opacity duration-300 motion-reduce:transition-none ${navOpen ? "pointer-events-auto opacity-100" : "pointer-events-none opacity-0"}`}
      />

      {/* Sliding drawer */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-72 max-w-[85vw] flex-col border-r border-sky-300/70 bg-[#f3f2f4] p-4 shadow-xl transition-transform duration-300 ease-out motion-reduce:transition-none ${navOpen ? "translate-x-0" : "-translate-x-full"}`}
      >
        <div className="mb-2 flex items-center justify-between gap-2">
          <div className="min-w-0">
            <p className="truncate text-lg font-semibold text-black">RhFlow</p>
            <p className="truncate text-sm text-black/70">
              Interface RH connectee
            </p>
          </div>
          <Button
            type="button"
            size="icon-sm"
            variant="ghost"
            aria-label="Fermer le menu"
            onClick={closeNav}
            className="text-black hover:bg-black/10"
          >
            <X className="text-teal-950" strokeWidth={2.75} />
          </Button>
        </div>

        <div className="mb-2 flex items-center gap-2">
          <Badge variant="secondary">{roleLabel}</Badge>
          <span className="truncate text-sm text-black/70">{userLabel}</span>
        </div>

        <Separator className="my-4 bg-black/15" />
        {nav(navigation.primary)}

        <div className="mt-auto pt-4">
          {nav(navigation.footer)}
          <Separator className="my-4 bg-black/15" />
          <Button
            variant="destructive"
            className="w-full justify-start bg-red-400 text-white hover:bg-red-700"
            onClick={logout}
          >
            <LogOut className="text-white" strokeWidth={2.75} />
            <span className="whitespace-nowrap">Deconnexion</span>
          </Button>
        </div>
      </aside>

      <main className="page-enter flex-1 bg-[#0f455409] p-4 lg:p-6">
        <Toaster richColors position="top-right" />
        {children}
      </main>
    </div>
  );
}
