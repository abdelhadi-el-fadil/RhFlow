"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  Building2,
  ClipboardList,
  FileText,
  Gauge,
  FolderKanban,
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
  ProjetRecrutementCardResponse,
  UserResponse,
} from "@/lib/backend-types";

type Counts = {
  users: number;
  directions: number;
  fiches: number;
  besoins: number;
  projets: number;
};

export default function DashboardPage() {
  const { user } = useAuth();
  const isAdminOrDrh = user?.role === "ADMIN" || user?.role === "DRH";
  const canSeeOperationalCards =
    isAdminOrDrh || user?.role === "DIRECTEUR" || user?.role === "DG";
  const [counts, setCounts] = useState<Counts>({
    users: 0,
    directions: 0,
    fiches: 0,
    besoins: 0,
    projets: 0,
  });
  const [recentBesoins, setRecentBesoins] = useState<
    BesoinRecrutementResponse[]
  >([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const canSeeAdminData = isAdminOrDrh;
        const canSeeNeeds = canSeeOperationalCards;
        const canSeeProjects = canSeeOperationalCards;

        let usersRes: PaginatedResponse<UserResponse> | null = null;
        let directionsRes: PaginatedResponse<DirectionResponse> | null = null;
        let besoinsRes: PaginatedResponse<BesoinRecrutementResponse> | null =
          null;
        let projetsRes: PaginatedResponse<ProjetRecrutementCardResponse> | null =
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

        if (canSeeProjects) {
          projetsRes = (
            await apiClient.get<PaginatedResponse<ProjetRecrutementCardResponse>>(
              "/projets/",
              { params: { page: 1, page_size: 1 } },
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
          projets: projetsRes?.meta.total_items ?? 0,
        });
        setRecentBesoins(besoinsRes?.data ?? []);
      } catch {
        if (!cancelled) {
          setCounts({ users: 0, directions: 0, fiches: 0, besoins: 0, projets: 0 });
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
  }, [user?.role, isAdminOrDrh, canSeeOperationalCards]);

  const firstName =
    user?.full_name?.split(" ")[0] ??
    user?.email?.split("@")[0] ??
    "utilisateur";

  return (
    <div className="stagger-enter space-y-6">
      <Card className="premium-panel premium-lift border-amber-200/65 bg-linear-to-br from-amber-50 via-stone-50 to-teal-50">
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

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        {isAdminOrDrh && (
          <StatCard
            title="Utilisateurs"
            value={counts.users}
            href="/users"
            loading={loading}
            tone="from-stone-50 via-amber-50 to-emerald-50"
            border="border-amber-200/70"
            textColor="text-slate-900"
            accentColor="text-emerald-700"
          />
        )}
        {isAdminOrDrh && (
          <StatCard
            title="Directions"
            value={counts.directions}
            href="/directions"
            loading={loading}
            tone="from-teal-50 via-cyan-50 to-stone-50"
            border="border-teal-200/70"
            textColor="text-slate-900"
            accentColor="text-teal-700"
          />
        )}
        {canSeeOperationalCards && (
          <StatCard
            title="Fiches de poste"
            value={counts.fiches}
            href="/fiches-de-poste"
            loading={loading}
            tone="from-stone-50 via-teal-50 to-emerald-50"
            border="border-emerald-200/70"
            textColor="text-slate-900"
            accentColor="text-emerald-700"
          />
        )}
        {canSeeOperationalCards && (
          <StatCard
            title="Besoins"
            value={counts.besoins}
            href="/besoins"
            loading={loading}
            tone="from-emerald-50 via-stone-50 to-cyan-50"
            border="border-cyan-200/70"
            textColor="text-slate-900"
            accentColor="text-cyan-700"
          />
        )}
        {canSeeOperationalCards && (
          <StatCard
            title="Projets"
            value={counts.projets}
            href="/projets"
            loading={loading}
            tone="from-cyan-50 via-stone-50 to-amber-50"
            border="border-cyan-200/70"
            textColor="text-slate-900"
            accentColor="text-cyan-700"
          />
        )}
      </div>

      <Card className="premium-panel premium-lift border-teal-200/65 bg-linear-to-br from-teal-50 via-stone-50 to-cyan-50">
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
}: {
  title: string;
  value: number;
  href: string;
  loading: boolean;
  tone: string;
  border: string;
  textColor: string;
  accentColor: string;
}) {
  const icon =
    title === "Utilisateurs" ? (
      <Users className={`size-4 ${accentColor}`} />
    ) : title === "Directions" ? (
      <Building2 className={`size-4 ${accentColor}`} />
    ) : title === "Projets" ? (
      <FolderKanban className={`size-4 ${accentColor}`} />
    ) : title === "Fiches de poste" ? (
      <FileText className={`size-4 ${accentColor}`} />
    ) : (
      <ClipboardList className={`size-4 ${accentColor}`} />
    );
  return (
    <Link href={href} className="block">
      <Card className={`premium-panel premium-lift w-full ${border} bg-linear-to-br ${tone}`}>
        <CardHeader>
          <CardDescription className={`flex items-center gap-2 ${accentColor}`}>
            {icon}
            {title}
          </CardDescription>
          <CardTitle className={textColor}>{loading ? "…" : value}</CardTitle>
        </CardHeader>
      </Card>
    </Link>
  );
}
