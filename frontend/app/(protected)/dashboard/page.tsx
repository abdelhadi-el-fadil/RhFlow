"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  Activity,
  Building2,
  ClipboardList,
  FileText,
  Gauge,
  Users,
} from "lucide-react";

import { useAuth } from "@/components/auth-provider";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { apiClient } from "@/lib/http";
import type {
  BesoinRecrutementResponse,
  DirectionResponse,
  FicheDePosteResponse,
  PaginatedResponse,
  UserResponse,
} from "@/lib/backend-types";

type Counts = {
  users: number;
  directions: number;
  fiches: number;
  besoins: number;
};

export default function DashboardPage() {
  const { user } = useAuth();
  const [counts, setCounts] = useState<Counts>({
    users: 0,
    directions: 0,
    fiches: 0,
    besoins: 0,
  });
  const [recentBesoins, setRecentBesoins] = useState<
    BesoinRecrutementResponse[]
  >([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const canSeeAdminData = user?.role === "ADMIN" || user?.role === "DRH";
        const canSeeNeeds = canSeeAdminData || user?.role === "DIRECTEUR";

        let usersRes: PaginatedResponse<UserResponse> | null = null;
        let directionsRes: PaginatedResponse<DirectionResponse> | null = null;
        let besoinsRes: PaginatedResponse<BesoinRecrutementResponse> | null =
          null;

        if (canSeeAdminData) {
          const [usersResponse, directionsResponse] = await Promise.all([
            apiClient.get<PaginatedResponse<UserResponse>>("/users/", {
              params: { page: 1, page_size: 1 },
            }),
            apiClient.get<PaginatedResponse<DirectionResponse>>(
              "/directions/",
              { params: { page: 1, page_size: 1 } },
            ),
          ]);
          usersRes = usersResponse.data;
          directionsRes = directionsResponse.data;
        }

        if (canSeeNeeds) {
          besoinsRes = (
            await apiClient.get<PaginatedResponse<BesoinRecrutementResponse>>(
              "/besoins/",
              { params: { page: 1, page_size: 5 } },
            )
          ).data;
        }

        const fichesRes = (
          await apiClient.get<PaginatedResponse<FicheDePosteResponse>>(
            "/fiches-de-poste/",
            { params: { page: 1, page_size: 1 } },
          )
        ).data;

        if (cancelled) {
          return;
        }

        setCounts({
          users: usersRes?.meta.total_items ?? 0,
          directions: directionsRes?.meta.total_items ?? 0,
          fiches: fichesRes.data.length ? fichesRes.meta.total_items : 0,
          besoins: besoinsRes?.meta.total_items ?? 0,
        });
        setRecentBesoins(besoinsRes?.data ?? []);
      } catch {
        if (!cancelled) {
          setCounts({ users: 0, directions: 0, fiches: 0, besoins: 0 });
          setRecentBesoins([]);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    void load();
    return () => {
      cancelled = true;
    };
  }, [user?.role]);

  const firstName =
    user?.full_name?.split(" ")[0] ??
    user?.email?.split("@")[0] ??
    "utilisateur";

  return (
    <div className="stagger-enter space-y-6">
      <Card className="premium-panel premium-lift border-amber-200/65 bg-gradient-to-br from-amber-50 via-stone-50 to-teal-50">
        <CardHeader>
          <CardDescription className="premium-copy">
            Bonjour {firstName}
          </CardDescription>
          <CardTitle className="premium-title flex items-center gap-2">
            <Gauge className="size-5 text-teal-700" />
            Tableau de bord RH
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          <Badge className="premium-chip" variant="secondary">
            Rôle {user?.role}
          </Badge>
          <Badge variant={user?.enabled ? "default" : "destructive"}>
            {user?.enabled ? "Compte actif" : "Compte désactivé"}
          </Badge>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title="Utilisateurs"
          value={counts.users}
          href="/users"
          loading={loading}
          tone="from-stone-50 via-amber-50 to-emerald-50"
          border="border-amber-200/70"
          textColor="text-slate-900"
          accentColor="text-emerald-700"
          linkColor="text-teal-800 hover:text-teal-950"
        />
        <StatCard
          title="Directions"
          value={counts.directions}
          href="/directions"
          loading={loading}
          tone="from-teal-50 via-cyan-50 to-stone-50"
          border="border-teal-200/70"
          textColor="text-slate-900"
          accentColor="text-teal-700"
          linkColor="text-teal-800 hover:text-teal-950"
        />
        <StatCard
          title="Fiches de poste"
          value={counts.fiches}
          href="/fiches-de-poste"
          loading={loading}
          tone="from-stone-50 via-teal-50 to-emerald-50"
          border="border-emerald-200/70"
          textColor="text-slate-900"
          accentColor="text-emerald-700"
          linkColor="text-teal-800 hover:text-teal-950"
        />
        <StatCard
          title="Besoins"
          value={counts.besoins}
          href="/besoins"
          loading={loading}
          tone="from-emerald-50 via-stone-50 to-cyan-50"
          border="border-cyan-200/70"
          textColor="text-slate-900"
          accentColor="text-cyan-700"
          linkColor="text-teal-800 hover:text-teal-950"
        />
      </div>

      <Card className="premium-panel premium-lift border-amber-200/65 bg-gradient-to-br from-stone-50 via-amber-50 to-teal-50">
        <CardHeader>
          <CardDescription className="premium-copy">Raccourcis</CardDescription>
          <CardTitle className="premium-title flex items-center gap-2">
            <Activity className="size-5 text-teal-700" />
            Navigation rapide
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-3 text-sm premium-copy">
          <Link
            className="premium-link rounded-lg border border-stone-300/75 bg-white/85 px-3 py-2 transition-colors duration-200 hover:bg-amber-50"
            href="/fiches-de-poste"
          >
            Voir les fiches de poste
          </Link>
          {user?.role !== "DG" && (
            <Link
              className="premium-link rounded-lg border border-stone-300/75 bg-white/85 px-3 py-2 transition-colors duration-200 hover:bg-amber-50"
              href="/besoins"
            >
              Voir les besoins
            </Link>
          )}
          {(user?.role === "ADMIN" ||
            user?.role === "DRH" ||
            user?.role === "DIRECTEUR") && (
            <Link
              className="premium-link rounded-lg border border-stone-300/75 bg-white/85 px-3 py-2 transition-colors duration-200 hover:bg-amber-50"
              href="/projets"
            >
              Voir les projets
            </Link>
          )}
          {(user?.role === "ADMIN" || user?.role === "DRH") && (
            <Link
              className="premium-link rounded-lg border border-stone-300/75 bg-white/85 px-3 py-2 transition-colors duration-200 hover:bg-amber-50"
              href="/offres"
            >
              Voir les offres
            </Link>
          )}
        </CardContent>
      </Card>

      <Card className="premium-panel premium-lift border-teal-200/65 bg-gradient-to-br from-teal-50 via-stone-50 to-cyan-50">
        <CardHeader>
          <CardDescription className="premium-copy">
            Derniers besoins
          </CardDescription>
          <CardTitle className="premium-title flex items-center gap-2">
            <ClipboardList className="size-5 text-teal-700" />
            Éléments récents depuis le backend
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {recentBesoins.map((need) => (
            <Link
              key={need.id}
              href={`/besoins/${need.id}`}
              className="flex items-center justify-between rounded-lg border border-stone-300/75 bg-white/80 px-3 py-2 text-slate-800 transition-colors duration-200 hover:bg-amber-50/80"
            >
              <div>
                <p className="font-medium text-slate-900">{need.fiche_title ?? `Besoin #${need.id}`}</p>
                <p className="text-xs text-slate-600">
                  Fiche {need.fiche_de_poste_id} · {need.status}
                </p>
              </div>
              <Badge variant="outline">#{need.id}</Badge>
            </Link>
          ))}
          {!recentBesoins.length && (
            <p className="premium-subtle animate-pulse text-sm motion-reduce:animate-none">
              Aucune donnée chargée.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function StatCard({
  title,
  value,
  href,
  loading,
  tone,
  border,
  textColor,
  accentColor,
  linkColor,
}: {
  title: string;
  value: number;
  href: string;
  loading: boolean;
  tone: string;
  border: string;
  textColor: string;
  accentColor: string;
  linkColor: string;
}) {
  const icon =
    title === "Utilisateurs" ? (
      <Users className={`size-4 ${accentColor}`} />
    ) : title === "Directions" ? (
      <Building2 className={`size-4 ${accentColor}`} />
    ) : title === "Fiches de poste" ? (
      <FileText className={`size-4 ${accentColor}`} />
    ) : (
      <ClipboardList className={`size-4 ${accentColor}`} />
    );
  return (
    <Card className={`premium-panel premium-lift ${border} bg-gradient-to-br ${tone}`}>
      <CardHeader>
        <CardDescription className={`flex items-center gap-2 ${accentColor}`}>
          {icon}
          {title}
        </CardDescription>
        <CardTitle className={textColor}>{loading ? "…" : value}</CardTitle>
      </CardHeader>
      <CardContent>
        <Link href={href} className={`text-sm ${linkColor} hover:underline`}>
          Ouvrir
        </Link>
      </CardContent>
    </Card>
  );
}
