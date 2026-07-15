"use client"

import { useEffect, useMemo, useState } from "react"
import { ClipboardList, MapPin, UserRound, Users } from "lucide-react"

import { RoleGate } from "@/components/role-gate"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"
import type {
  BesoinPriority,
  BesoinRecrutementResponse,
  DirectionResponse,
  PaginatedResponse,
} from "@/lib/backend-types"
import { ApiHttpError, apiClient } from "@/lib/http"
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

export default function ArchiveBesoinsPage() {
  return (
    <RoleGate roles={["ADMIN", "DRH", "DIRECTEUR", "DG"]}>
      <ArchiveBesoinsContent />
    </RoleGate>
  )
}

function ArchiveBesoinsContent() {
  const [items, setItems] = useState<BesoinRecrutementResponse[]>([])
  const [directions, setDirections] = useState<DirectionResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState("")
  const [directionFilter, setDirectionFilter] = useState("")
  const [priorityFilter, setPriorityFilter] = useState<"" | "ALL" | BesoinPriority>("")

  useEffect(() => {
    let cancelled = false

    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const params: Record<string, string | number | boolean> = {
          page: 1,
          page_size: 100,
          archived: true,
        }
        if (directionFilter !== "" && directionFilter !== "ALL") {
          params.direction_id = Number(directionFilter)
        }
        if (priorityFilter !== "" && priorityFilter !== "ALL") {
          params.priority = priorityFilter
        }

        const [besoinsRes, directionsRes] = await Promise.all([
          apiClient.get<PaginatedResponse<BesoinRecrutementResponse>>("/besoins/", {
            params,
          }),
          apiClient.get<PaginatedResponse<DirectionResponse>>("/directions/", {
            params: { page: 1, page_size: 100 },
          }),
        ])

        if (!cancelled) {
          setItems(besoinsRes.data.data)
          setDirections(directionsRes.data.data)
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof ApiHttpError
              ? err.message
              : "Impossible de charger les besoins archivés.",
          )
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
  }, [directionFilter, priorityFilter])

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

  return (
    <div className="stagger-enter space-y-6">
      <Card className="premium-panel premium-lift border-amber-200/65 bg-linear-to-br from-stone-50 via-amber-50 to-teal-50">
        <CardHeader>
          <CardTitle className="premium-title flex items-center gap-2"><ClipboardList className="size-5 text-teal-700" />Archives besoins de recrutement</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-3">
          <Field label="Recherche"><Input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Poste, direction, demandeur, lieu" /></Field>
          <Field label="Direction"><Select value={directionFilter} onChange={(event) => setDirectionFilter(event.target.value)} placeholder="Choisir une direction"><option value="ALL">Toutes</option>{directions.map((direction) => <option key={direction.id} value={direction.id}>{direction.name}</option>)}</Select></Field>
          <Field label="Priorité"><Select value={priorityFilter} onChange={(event) => setPriorityFilter(event.target.value as "" | "ALL" | BesoinPriority)} placeholder="Choisir une priorité"><option value="ALL">Toutes</option>{PRIORITY_OPTIONS.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</Select></Field>
        </CardContent>
      </Card>

      {loading && <Card className="premium-panel"><CardContent className="premium-copy">Chargement…</CardContent></Card>}
      {error && <Card className="premium-panel"><CardContent className="premium-copy">{error}</CardContent></Card>}

      {!loading && !error && visibleItems.length === 0 && (
        <Card className="premium-panel">
          <CardContent className="premium-subtle">Aucun besoin archivé ne correspond aux filtres.</CardContent>
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
