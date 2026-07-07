"use client"

import Link from "next/link"
import { useCallback, useEffect, useMemo, useState } from "react"
import { BriefcaseBusiness, Info } from "lucide-react"

import { useAuth } from "@/components/auth-provider"
import { RoleGate } from "@/components/role-gate"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"
import type {
  ApiResponse,
  DirectionResponse,
  PaginatedResponse,
  ProjetRecrutementCardResponse,
  ProjetRecrutementResponse,
} from "@/lib/backend-types"
import { ApiHttpError, apiClient } from "@/lib/http"
import { badgeVariantFromProjetStatus } from "@/lib/status-labels"

export default function ProjetsPage() {
  return (
    <RoleGate roles={["ADMIN", "DRH", "DIRECTEUR"]}>
      <Content />
    </RoleGate>
  )
}

function Content() {
  const { user } = useAuth()
  const [projects, setProjects] = useState<ProjetRecrutementCardResponse[]>([])
  const [directions, setDirections] = useState<DirectionResponse[]>([])
  const [selectedDirectionId, setSelectedDirectionId] = useState("")
  const [detailProject, setDetailProject] = useState<ProjetRecrutementResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isDetailLoading, setIsDetailLoading] = useState(false)
  const [detailError, setDetailError] = useState<string | null>(null)

  const canCloseProject = user?.role === "ADMIN" || user?.role === "DRH"

  const directionParam = useMemo(() => {
    if (!selectedDirectionId) {
      return null
    }
    const parsed = Number(selectedDirectionId)
    return Number.isNaN(parsed) ? null : parsed
  }, [selectedDirectionId])

  const loadDirections = useCallback(async () => {
    const response = await apiClient.get<PaginatedResponse<DirectionResponse>>("/directions/", {
      params: { page: 1, page_size: 100 },
    })
    setDirections(response.data.data)
  }, [])

  const loadProjects = useCallback(async () => {
    const params: Record<string, number> = { page: 1, page_size: 100 }
    if (directionParam !== null) {
      params.direction_id = directionParam
    }

    const response = await apiClient.get<PaginatedResponse<ProjetRecrutementCardResponse>>("/projets/", { params })
    setProjects(response.data.data)
  }, [directionParam])

  useEffect(() => {
    let cancelled = false

    const load = async () => {
      setIsLoading(true)
      setError(null)
      try {
        await Promise.all([loadDirections(), loadProjects()])
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiHttpError ? err.message : "Impossible de charger les projets de recrutement.")
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false)
        }
      }
    }

    void load()

    return () => {
      cancelled = true
    }
  }, [loadDirections, loadProjects])

  const openDetails = async (projectId: number) => {
    setIsDetailLoading(true)
    setDetailError(null)
    setDetailProject(null)
    try {
      const response = await apiClient.get<ApiResponse<ProjetRecrutementResponse>>(`/projets/${projectId}`)
      setDetailProject(response.data.data)
    } catch (err) {
      setDetailError(err instanceof ApiHttpError ? err.message : "Impossible de charger le détail du projet.")
    } finally {
      setIsDetailLoading(false)
    }
  }

  const closeProject = async (projectId: number) => {
    if (!confirm("Clôturer ce projet ? Cette action est irréversible.")) {
      return
    }

    await apiClient.patch(`/projets/${projectId}/cloturer`)
    await loadProjects()
  }

  if (isLoading) {
    return (
      <Card>
        <CardContent className="animate-pulse motion-reduce:animate-none">Chargement des projets de recrutement…</CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardContent>{error}</CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><BriefcaseBusiness className="size-5 text-indigo-700" />Projets de recrutement ouverts</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-3">
          <Field label="Filtrer par direction">
            <Select value={selectedDirectionId} onChange={(event) => setSelectedDirectionId(event.target.value)}>
              <option value="">Toutes les directions</option>
              {directions.map((direction) => (
                <option key={direction.id} value={direction.id}>
                  {direction.name}
                </option>
              ))}
            </Select>
          </Field>
        </CardContent>
      </Card>

      {projects.length === 0 && (
        <Card>
          <CardContent>Aucun projet ouvert ne correspond au filtre sélectionné.</CardContent>
        </Card>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        {projects.map((project) => (
          <Card key={project.id}>
            <CardHeader>
              <CardTitle className="flex items-center justify-between gap-3">
                <span>{project.title}</span>
                <Badge variant={badgeVariantFromProjetStatus(project.status)}>{project.status}</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-sm">
              <div className="grid gap-2 text-muted-foreground">
                <p>Direction: {project.direction_name ?? "-"}</p>
                <p>Directeur: {project.director_name ?? "-"}</p>
                <p>Date d&apos;ouverture: {project.start_date}</p>
                <p>Nombre de postes: {project.positions_count}</p>
              </div>

              <div className="flex flex-wrap gap-2">
                <Button variant="outline" onClick={() => void openDetails(project.id)}>
                  Voir le détail
                </Button>
                <Button asChild variant="outline">
                  <Link href={`/offres?projectId=${project.id}`}>Voir / générer l&apos;offre</Link>
                </Button>
                <Button asChild variant="outline">
                  <Link href={`/projets/${project.id}/candidatures`}>Voir les candidatures</Link>
                </Button>
                {canCloseProject && (
                  <Button variant="destructive" onClick={() => void closeProject(project.id)}>
                    Fermer le projet
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {(isDetailLoading || detailError || detailProject) && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 motion-safe:animate-in motion-safe:fade-in-0 motion-safe:duration-200">
          <Card className="w-full max-w-2xl motion-safe:animate-in motion-safe:zoom-in-95 motion-safe:duration-200">
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><Info className="size-5 text-indigo-700" />Détail projet</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-sm">
              {isDetailLoading && <p>Chargement du détail…</p>}
              {detailError && <p>{detailError}</p>}
              {detailProject && (
                <div className="space-y-2 text-muted-foreground">
                  <p>Intitulé: {detailProject.title}</p>
                  <p>Période: {detailProject.start_date} → {detailProject.expected_end_date}</p>
                  <p>Manager ID: {detailProject.manager_id}</p>
                  <p>Description: {detailProject.description ?? "-"}</p>
                  <p>Besoins rattachés: {detailProject.besoins.length}</p>
                </div>
              )}
              <div className="flex justify-end">
                <Button variant="outline" onClick={() => { setDetailProject(null); setDetailError(null) }}>
                  Fermer
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <div className="space-y-2"><Label>{label}</Label>{children}</div>
}
