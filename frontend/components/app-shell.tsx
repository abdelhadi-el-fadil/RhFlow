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
            className={`group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200 ${
              active
                ? "bg-white/12 text-white ring-1 ring-sky-400/40 shadow-lg shadow-sky-900/20"
                : "text-slate-300 hover:bg-white/8 hover:text-white hover:ring-1 hover:ring-white/10"
            }`}
          >
            <Icon
              className={`size-4 shrink-0 transition-colors ${
                active
                  ? "text-sky-300"
                  : "text-slate-400 group-hover:text-sky-300"
              }`}
              strokeWidth={2.5}
            />
            <span className="whitespace-nowrap">{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );

  return (
    <div className="min-h-svh bg-transparent">
 <header className="sticky top-0 z-20 flex items-center justify-between border-b border-slate-300/70 bg-gradient-to-r from-slate-100 via-sky-100 to-blue-200 px-4 py-3 shadow-md backdrop-blur-sm">
  <div className="flex items-center gap-3">
    <Button
      type="button"
      variant="outline"
      size="icon"
      aria-label={navOpen ? "Fermer le menu" : "Ouvrir le menu"}
      onClick={() => setNavOpen((value) => !value)}
      className="border-slate-300 bg-white/70 text-slate-700 shadow-sm hover:border-sky-400 hover:bg-sky-100"
    >
      <Menu className="text-sky-700" />
    </Button>

    <div>
      <p className="text-sm font-semibold text-slate-900">
        Bonjour <span className="text-sky-700">{greetingName}</span>
      </p>
      <p className="text-xs text-slate-600">{emailLabel}</p>
    </div>
  </div>

  <div className="flex items-center gap-2">
    <Badge className="border-sky-300 bg-sky-100 text-sky-800">
      {roleLabel}
    </Badge>

    <Button
      variant="outline"
      onClick={logout}
      className="hidden border-slate-300 bg-white/70 text-slate-700 shadow-sm hover:border-red-400 hover:bg-red-50 hover:text-red-700 sm:inline-flex"
    >
      <LogOut className="mr-2 h-4 w-4 text-red-500" />
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
        className={`fixed inset-y-0 left-0 z-40 flex w-72 max-w-[85vw] flex-col border-r border-slate-600/40 bg-gradient-to-br from-slate-950 via-indigo-950 to-emerald-950 p-4 shadow-2xl transition-transform duration-300 ease-out motion-reduce:transition-none ${
          navOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="mb-2 flex items-center justify-between gap-2">
          <div className="min-w-0">
            <p className="truncate text-xl font-bold tracking-wide text-white">
              RhFlow
            </p>
            <p className="truncate text-sm text-slate-300">
              Interface RH connectée
            </p>
          </div>
          <Button
            type="button"
            size="icon-sm"
            variant="ghost"
            aria-label="Fermer le menu"
            onClick={closeNav}
            className="text-slate-300 hover:bg-white/10 hover:text-white"
          >
            <X className="text-teal-950" strokeWidth={2.75} />
          </Button>
        </div>

        <div className="mb-2 flex items-center gap-2">
          <Badge className="bg-sky-500/20 text-sky-200 border border-sky-400/30">
            {roleLabel}
          </Badge>
          <span className="truncate text-sm text-slate-300">{userLabel}</span>
        </div>

        <Separator className="my-4 bg-white/10" />
        {nav(navigation.primary)}

        <div className="mt-auto pt-4">
          {nav(navigation.footer)}
          <Separator className="my-4 bg-white/10" />
          <Button
            variant="destructive"
            className="w-full justify-start rounded-xl bg-red-600/90 text-white shadow-lg hover:bg-red-500"
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
