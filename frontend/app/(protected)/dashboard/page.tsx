"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import { Activity, Building2, ClipboardList, FileText, Gauge, Users } from "lucide-react"

import { useAuth } from "@/components/auth-provider"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { apiClient } from "@/lib/http"
import type {
  BesoinRecrutementResponse,
  DirectionResponse,
  FicheDePosteResponse,
  PaginatedResponse,
  UserResponse,
} from "@/lib/backend-types"

type Counts = {
  users: number
  directions: number
  fiches: number
  besoins: number
}

export default function DashboardPage() {
  const { user } = useAuth()
  const [counts, setCounts] = useState<Counts>({ users: 0, directions: 0, fiches: 0, besoins: 0 })
  const [recentBesoins, setRecentBesoins] = useState<BesoinRecrutementResponse[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false

    const load = async () => {
      try {
        const canSeeAdminData = user?.role === "ADMIN" || user?.role === "DRH"
        const canSeeNeeds = canSeeAdminData || user?.role === "DIRECTEUR"

        let usersRes: PaginatedResponse<UserResponse> | null = null
        let directionsRes: PaginatedResponse<DirectionResponse> | null = null
        let besoinsRes: PaginatedResponse<BesoinRecrutementResponse> | null = null

        if (canSeeAdminData) {
          const [usersResponse, directionsResponse] = await Promise.all([
            apiClient.get<PaginatedResponse<UserResponse>>("/users/", { params: { page: 1, page_size: 1 } }),
            apiClient.get<PaginatedResponse<DirectionResponse>>("/directions/", { params: { page: 1, page_size: 1 } }),
          ])
          usersRes = usersResponse.data
          directionsRes = directionsResponse.data
        }

        if (canSeeNeeds) {
          besoinsRes = (await apiClient.get<PaginatedResponse<BesoinRecrutementResponse>>("/besoins/", { params: { page: 1, page_size: 5 } })).data
        }

        const fichesRes = (await apiClient.get<PaginatedResponse<FicheDePosteResponse>>("/fiches-de-poste/", { params: { page: 1, page_size: 1 } })).data

        if (cancelled) {
          return
        }

        setCounts({
          users: usersRes?.meta.total_items ?? 0,
          directions: directionsRes?.meta.total_items ?? 0,
          fiches: fichesRes.data.length ? fichesRes.meta.total_items : 0,
          besoins: besoinsRes?.meta.total_items ?? 0,
        })
        setRecentBesoins(besoinsRes?.data ?? [])
      } catch {
        if (!cancelled) {
          setCounts({ users: 0, directions: 0, fiches: 0, besoins: 0 })
          setRecentBesoins([])
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    void load()
    return () => {
      cancelled = true
    }
  }, [user?.role])

  const firstName = user?.full_name?.split(" ")[0] ?? user?.email?.split("@")[0] ?? "utilisateur"

  return (
    <div className="space-y-6">
      <Card className="border-sky-200/70 bg-sky-50/90">
        <CardHeader>
          <CardDescription>Bonjour {firstName}</CardDescription>
          <CardTitle className="flex items-center gap-2"><Gauge className="size-5 text-indigo-700" />Tableau de bord RH</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          <Badge variant="secondary">Rôle {user?.role}</Badge>
          <Badge variant={user?.enabled ? "default" : "destructive"}>{user?.enabled ? "Compte actif" : "Compte désactivé"}</Badge>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard title="Utilisateurs" value={counts.users} href="/users" loading={loading} tone="from-blue-500/10 to-indigo-500/10" />
        <StatCard title="Directions" value={counts.directions} href="/directions" loading={loading} tone="from-indigo-500/10 to-violet-500/10" />
        <StatCard title="Fiches de poste" value={counts.fiches} href="/fiches-de-poste" loading={loading} tone="from-sky-500/10 to-blue-500/10" />
        <StatCard title="Besoins" value={counts.besoins} href="/besoins" loading={loading} tone="from-violet-500/10 to-fuchsia-500/10" />
      </div>

      <Card>
        <CardHeader>
          <CardDescription>Raccourcis</CardDescription>
          <CardTitle className="flex items-center gap-2"><Activity className="size-5 text-indigo-700" />Navigation rapide</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-3 text-sm">
          <Link className="rounded-lg border border-indigo-200/70 bg-background/80 px-3 py-2 transition-colors duration-200 hover:bg-muted" href="/fiches-de-poste">Voir les fiches de poste</Link>
          {user?.role !== "DG" && <Link className="rounded-lg border border-indigo-200/70 bg-background/80 px-3 py-2 transition-colors duration-200 hover:bg-muted" href="/besoins">Voir les besoins</Link>}
          {(user?.role === "ADMIN" || user?.role === "DRH" || user?.role === "DIRECTEUR") && <Link className="rounded-lg border border-indigo-200/70 bg-background/80 px-3 py-2 transition-colors duration-200 hover:bg-muted" href="/projets">Voir les projets</Link>}
          {(user?.role === "ADMIN" || user?.role === "DRH") && <Link className="rounded-lg border border-indigo-200/70 bg-background/80 px-3 py-2 transition-colors duration-200 hover:bg-muted" href="/offres">Voir les offres</Link>}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardDescription>Derniers besoins</CardDescription>
          <CardTitle className="flex items-center gap-2"><ClipboardList className="size-5 text-indigo-700" />Éléments récents depuis le backend</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {recentBesoins.map((need) => (
            <Link key={need.id} href={`/besoins/${need.id}`} className="flex items-center justify-between rounded-lg border border-indigo-200/70 px-3 py-2 transition-colors duration-200 hover:bg-muted/50">
              <div>
                <p className="font-medium">{need.title}</p>
                <p className="text-xs text-muted-foreground">Fiche {need.fiche_de_poste_id} · {need.status}</p>
              </div>
              <Badge variant="outline">#{need.id}</Badge>
            </Link>
          ))}
          {!recentBesoins.length && <p className="animate-pulse text-sm text-muted-foreground motion-reduce:animate-none">Aucune donnée chargée.</p>}
        </CardContent>
      </Card>
    </div>
  )
}

function StatCard({ title, value, href, loading, tone }: { title: string; value: number; href: string; loading: boolean; tone: string }) {
  const icon = title === "Utilisateurs" ? <Users className="size-4 text-indigo-700" /> : title === "Directions" ? <Building2 className="size-4 text-indigo-700" /> : title === "Fiches de poste" ? <FileText className="size-4 text-indigo-700" /> : <ClipboardList className="size-4 text-indigo-700" />
  return (
    <Card className={`border-indigo-200/70 bg-linear-to-br ${tone}`}>
      <CardHeader>
        <CardDescription className="flex items-center gap-2">{icon}{title}</CardDescription>
        <CardTitle className="text-indigo-950">{loading ? "…" : value}</CardTitle>
      </CardHeader>
      <CardContent>
        <Link href={href} className="text-sm text-indigo-700 hover:text-indigo-900 hover:underline">Ouvrir</Link>
      </CardContent>
    </Card>
  )
}