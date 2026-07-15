"use client"

import { useEffect, useMemo, useState } from "react"
import { BookUser } from "lucide-react"

import { RoleGate } from "@/components/role-gate"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"
import type {
  DirectionResponse,
  PaginatedResponse,
  ProjetRecrutementCardResponse,
} from "@/lib/backend-types"
import { ApiHttpError, apiClient } from "@/lib/http"
import { badgeVariantFromProjetStatus } from "@/lib/status-labels"

export default function ArchiveProjectsPage() {
  return (
    <RoleGate roles={["ADMIN", "DRH", "DIRECTEUR", "DG"]}>
      <ArchiveProjectsContent />
    </RoleGate>
  )
}

function ArchiveProjectsContent() {
  const [items, setItems] = useState<ProjetRecrutementCardResponse[]>([])
  const [directions, setDirections] = useState<DirectionResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState("")
  const [directionFilter, setDirectionFilter] = useState("")

  useEffect(() => {
    let cancelled = false

    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const params: Record<string, number | boolean> = {
          page: 1,
          page_size: 100,
          archived: true,
        }
        if (directionFilter !== "" && directionFilter !== "ALL") {
          params.direction_id = Number(directionFilter)
        }

        const [projectsRes, directionsRes] = await Promise.all([
          apiClient.get<PaginatedResponse<ProjetRecrutementCardResponse>>("/projets/", {
            params,
          }),
          apiClient.get<PaginatedResponse<DirectionResponse>>("/directions/", {
            params: { page: 1, page_size: 100 },
          }),
        ])

        if (!cancelled) {
          setItems(projectsRes.data.data)
          setDirections(directionsRes.data.data)
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof ApiHttpError
              ? err.message
              : "Impossible de charger les projets archivés.",
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
  }, [directionFilter])

  const visibleItems = useMemo(() => {
    const query = search.trim().toLowerCase()
    if (!query) {
      return items
    }
    return items.filter((item) => {
      const text = `${item.title} ${item.direction_name ?? ""} ${item.director_name ?? ""} ${item.manager_name ?? ""} ${item.fiche_title ?? ""} ${item.besoin_title ?? ""}`.toLowerCase()
      return text.includes(query)
    })
  }, [items, search])

  return (
    <div className="stagger-enter space-y-6">
      <Card className="premium-panel premium-lift border-amber-200/65 bg-linear-to-br from-stone-50 via-amber-50 to-teal-50">
        <CardHeader>
          <CardTitle className="premium-title flex items-center gap-2"><BookUser className="size-5 text-teal-700" />Archives projets de recrutement</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          <Field label="Recherche"><Input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Projet, direction, manager" /></Field>
          <Field label="Direction"><Select value={directionFilter} onChange={(event) => setDirectionFilter(event.target.value)} placeholder="Choisir une direction"><option value="ALL">Toutes</option>{directions.map((direction) => <option key={direction.id} value={direction.id}>{direction.name}</option>)}</Select></Field>
        </CardContent>
      </Card>

      {loading && <Card className="premium-panel"><CardContent className="premium-copy">Chargement…</CardContent></Card>}
      {error && <Card className="premium-panel"><CardContent className="premium-copy">{error}</CardContent></Card>}

      {!loading && !error && visibleItems.length === 0 && (
        <Card className="premium-panel">
          <CardContent className="premium-subtle">Aucun projet archivé ne correspond aux filtres.</CardContent>
        </Card>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        {visibleItems.map((project) => (
          <Card key={project.id} className="premium-panel premium-lift border-stone-300/70 bg-white/90">
            <CardHeader>
              <CardTitle className="flex items-center justify-between gap-3">
                <span>{project.title}</span>
                <Badge variant={badgeVariantFromProjetStatus(project.status)}>
                  {project.status}
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-slate-700">
              <p>Direction: {project.direction_name ?? "-"}</p>
              <p>Directeur: {project.director_name ?? "-"}</p>
              <p>Manager: {project.manager_name ?? "-"}</p>
              <p>Fiche de poste: {project.fiche_title ?? "-"}</p>
              <p>Besoin principal: {project.besoin_title ?? "-"}</p>
              <p>Nombre de postes: {project.nombre_postes ?? "-"}</p>
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
