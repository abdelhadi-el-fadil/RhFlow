"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import { ClipboardList, MapPin, UserRound, Users } from "lucide-react"

import { useAuth } from "@/components/auth-provider"
import { RoleGate } from "@/components/role-gate"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"
import { apiClient, ApiHttpError } from "@/lib/http"
import type { BesoinPriority, BesoinRecrutementResponse, DirectionResponse, PaginatedResponse } from "@/lib/backend-types"
import { badgeVariantFromBesoinStatus } from "@/lib/status-labels"

const PRIORITY_OPTIONS: Array<{ value: BesoinPriority; label: string }> = [
  { value: "HAUTE", label: "Haute" },
  { value: "NORMALE", label: "Normale" },
  { value: "BASSE", label: "Basse" },
]

const PRIORITY_LABELS: Record<BesoinPriority, string> = {
  HAUTE: "Haute",
  NORMALE: "Normale",
  BASSE: "Basse",
}

export default function BesoinsPage() {
  return (
    <RoleGate roles={["ADMIN", "DRH", "DIRECTEUR", "DG"]}>
      <BesoinsContent />
    </RoleGate>
  )
}

function BesoinsContent() {
  const { user } = useAuth()
  const [items, setItems] = useState<BesoinRecrutementResponse[]>([])
  const [directions, setDirections] = useState<DirectionResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [search, setSearch] = useState("")
  const [directionFilter, setDirectionFilter] = useState("")
  const [priorityFilter, setPriorityFilter] = useState<"" | "ALL" | BesoinPriority>("")
  const [showArchives, setShowArchives] = useState(false)

  const canCreateNeed = user?.role === "DIRECTEUR" || user?.role === "DRH" || user?.role === "ADMIN"
  const canDecide = user?.role === "DRH" || user?.role === "ADMIN"

  const load = async () => {
    const params: Record<string, string | number | boolean> = { page: 1, page_size: 100, archived: showArchives }
    if (directionFilter !== "" && directionFilter !== "ALL") {
      params.direction_id = Number(directionFilter)
    }
    if (priorityFilter !== "" && priorityFilter !== "ALL") {
      params.priority = priorityFilter
    }

    const [besoinsRes, directionsRes] = await Promise.all([
      apiClient.get<PaginatedResponse<BesoinRecrutementResponse>>("/besoins/", { params }),
      apiClient.get<PaginatedResponse<DirectionResponse>>("/directions/", { params: { page: 1, page_size: 100 } }),
    ])

    setItems(besoinsRes.data.data)
    setDirections(directionsRes.data.data)
  }

  useEffect(() => {
    const run = async () => {
      setLoading(true)
      setError(null)
      try {
        await load()
      } catch (err) {
        setError(err instanceof ApiHttpError ? err.message : "Impossible de charger les besoins.")
      } finally {
        setLoading(false)
      }
    }

    void run()
  }, [directionFilter, priorityFilter, showArchives])

  const visibleItems = useMemo(() => {
    const query = search.trim().toLowerCase()
    if (!query) {
      return items
    }
    return items.filter((item) => {
      const text = `${item.fiche_title ?? ""} ${item.direction_name ?? ""} ${item.director_name ?? ""} ${item.requester_name ?? ""} ${item.lieu_affectation ?? ""} ${item.justification ?? ""}`.toLowerCase()
      return text.includes(query)
    })
  }, [items, search])

  const approveNeed = async (id: number) => {
    setActionError(null)
    try {
      await apiClient.post(`/besoins/${id}/approuver`)
      await load()
    } catch (err) {
      setActionError(err instanceof ApiHttpError ? err.message : "Impossible d'accepter ce besoin.")
    }
  }

  const rejectNeed = async (id: number) => {
    const reason = prompt("Motif du refus ?") ?? ""
    if (!reason.trim()) {
      return
    }

    setActionError(null)
    try {
      await apiClient.post(`/besoins/${id}/rejeter`, { reason })
      await load()
    } catch (err) {
      setActionError(err instanceof ApiHttpError ? err.message : "Impossible de refuser ce besoin.")
    }
  }

  return (
    <div className="stagger-enter space-y-6">
      <Card className="premium-panel premium-lift border-amber-200/65 bg-gradient-to-br from-stone-50 via-amber-50 to-teal-50">
        <CardHeader>
          <CardTitle className="premium-title flex items-center gap-2"><ClipboardList className="size-5 text-teal-700" />Besoins de recrutement</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {actionError && <p className="text-sm text-destructive">{actionError}</p>}
          <div className="flex flex-wrap gap-2">
            {canCreateNeed && <Button asChild><Link href="/besoins/nouveau">Créer un besoin</Link></Button>}
            <Button variant="outline" onClick={() => setShowArchives((v) => !v)}>{showArchives ? "Voir actifs" : "Voir archives"}</Button>
          </div>
          <div className="grid gap-4 md:grid-cols-3">
            <Field label="Recherche"><Input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Poste, direction, demandeur, lieu" /></Field>
            <Field label="Direction"><Select value={directionFilter} onChange={(event) => setDirectionFilter(event.target.value)} placeholder="Choisir une direction"><option value="ALL">Toutes</option>{directions.map((direction) => <option key={direction.id} value={direction.id}>{direction.name}</option>)}</Select></Field>
            <Field label="Priorité"><Select value={priorityFilter} onChange={(event) => setPriorityFilter(event.target.value as "" | "ALL" | BesoinPriority)} placeholder="Choisir une priorité"><option value="ALL">Toutes</option>{PRIORITY_OPTIONS.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</Select></Field>
          </div>
        </CardContent>
      </Card>

      {loading && <Card className="premium-panel"><CardContent className="premium-copy">Chargement…</CardContent></Card>}
      {error && <Card className="premium-panel"><CardContent className="premium-copy">{error}</CardContent></Card>}

      {!loading && !error && visibleItems.length === 0 && (
        <Card className="premium-panel">
          <CardContent className="premium-subtle">Aucun besoin ne correspond aux filtres.</CardContent>
        </Card>
      )}

      <div className="grid gap-4 xl:grid-cols-2">
        {visibleItems.map((item) => (
          <Card key={item.id} className="premium-panel premium-lift border-stone-300/70 bg-white/90">
            <CardHeader>
              <CardTitle className="flex items-center justify-between gap-3">
                <span>{item.fiche_title ?? `Fiche #${item.fiche_de_poste_id}`}</span>
                <Badge variant={badgeVariantFromBesoinStatus(item.status)}>{item.status}</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-sm text-slate-700">
              <p className="flex items-center gap-2"><Users className="size-4" />Direction: {item.direction_name ?? "-"}</p>
              <p className="flex items-center gap-2"><UserRound className="size-4" />Directeur: {item.director_name ?? "-"}</p>
              <p className="flex items-center gap-2"><UserRound className="size-4" />Demandeur: {item.requester_name ?? "-"}</p>
              <p className="flex items-center gap-2"><MapPin className="size-4" />Lieu: {item.lieu_affectation ?? "-"}</p>
              <p>Motif: {item.justification ?? "-"}</p>
              <p>Nombre de postes: {item.positions_count ?? "-"}</p>
              <p>Date souhaitée: {item.desired_date ?? "-"}</p>
              <p>Priorité: <Badge variant="outline">{PRIORITY_LABELS[item.priority]}</Badge></p>

              <div className="flex flex-wrap gap-2">
                <Button asChild variant="outline" size="sm"><Link href={`/besoins/${item.id}`}>Ouvrir</Link></Button>
                {canDecide && item.status === "SUBMITTED" && !showArchives && (
                  <>
                    <Button size="sm" onClick={() => void approveNeed(item.id)}>Accepter</Button>
                    <Button size="sm" variant="destructive" onClick={() => void rejectNeed(item.id)}>Refuser</Button>
                  </>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <div className="space-y-2"><Label>{label}</Label>{children}</div>
}
