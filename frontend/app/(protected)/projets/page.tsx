"use client"

import Link from "next/link"
import { useCallback, useEffect, useMemo, useState } from "react"
import { BriefcaseBusiness, Copy, Mail, Pencil } from "lucide-react"

import { useAuth } from "@/components/auth-provider"
import { RoleGate } from "@/components/role-gate"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"
import type {
  DirectionResponse,
  PaginatedResponse,
  ProjetRecrutementCardResponse,
} from "@/lib/backend-types"
import { ApiHttpError, apiClient } from "@/lib/http"
import { badgeVariantFromProjetStatus, labelFromProjetStatus } from "@/lib/status-labels"

export default function ProjetsPage() {
  return (
    <RoleGate roles={["ADMIN", "DRH", "DIRECTEUR", "DG"]}>
      <Content />
    </RoleGate>
  )
}

function Content() {
  const { user } = useAuth()
  const [projects, setProjects] = useState<ProjetRecrutementCardResponse[]>([])
  const [directions, setDirections] = useState<DirectionResponse[]>([])
  const [selectedDirectionId, setSelectedDirectionId] = useState("")
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [editingProjectId, setEditingProjectId] = useState<number | null>(null)
  const [emailDraft, setEmailDraft] = useState("")
  const [showArchived, setShowArchived] = useState(false)

  const canManageProjects = user?.role === "ADMIN" || user?.role === "DRH"
  const canEditEmailSubject = user?.role === "DRH" || user?.role === "ADMIN"

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
    const params: Record<string, number | boolean> = { page: 1, page_size: 100, archived: showArchived }
    if (directionParam !== null) {
      params.direction_id = directionParam
    }

    const response = await apiClient.get<PaginatedResponse<ProjetRecrutementCardResponse>>("/projets/", { params })
    setProjects(response.data.data)
  }, [directionParam, showArchived])

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

  const closeProject = async (projectId: number) => {
    if (!confirm("Clôturer ce projet ? Cette action est irréversible.")) {
      return
    }

    setActionError(null)
    try {
      await apiClient.patch(`/projets/${projectId}/cloturer`)
      await loadProjects()
    } catch (err) {
      setActionError(err instanceof ApiHttpError ? err.message : "Impossible de clôturer ce projet.")
    }
  }

  const deleteProject = async (projectId: number) => {
    if (!confirm("Supprimer ce projet ?")) {
      return
    }

    setActionError(null)
    try {
      await apiClient.delete(`/projets/${projectId}`)
      await loadProjects()
    } catch (err) {
      setActionError(err instanceof ApiHttpError ? err.message : "Impossible de supprimer ce projet.")
    }
  }

  const copyEmailSubject = async (value: string) => {
    setActionError(null)
    try {
      await navigator.clipboard.writeText(value)
    } catch {
      setActionError("Impossible de copier l'objet d'email.")
    }
  }

  const saveEmailSubject = async (projectId: number) => {
    setActionError(null)
    try {
      await apiClient.put(`/projets/${projectId}`, { email_subject: emailDraft })
      setEditingProjectId(null)
      setEmailDraft("")
      await loadProjects()
    } catch (err) {
      setActionError(err instanceof ApiHttpError ? err.message : "Impossible de modifier l'objet d'email.")
    }
  }

  if (isLoading) {
    return (
      <Card className="premium-panel">
        <CardContent className="premium-copy animate-pulse motion-reduce:animate-none">Chargement des projets de recrutement…</CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="premium-panel">
        <CardContent className="premium-copy">{error}</CardContent>
      </Card>
    )
  }

  return (
    <div className="stagger-enter space-y-6">
      <Card className="premium-panel premium-lift border-amber-200/65 bg-linear-to-br from-stone-50 via-amber-50 to-teal-50">
        <CardHeader>
          <CardTitle className="premium-title flex items-center gap-2"><BriefcaseBusiness className="size-5 text-teal-700" />Projets de recrutement</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-3">
          {actionError && <p className="md:col-span-3 text-sm text-destructive">{actionError}</p>}
          <Field label="Filtrer par direction">
            <Select value={selectedDirectionId} onChange={(event) => setSelectedDirectionId(event.target.value)}>
              {directions.map((direction) => (
                <option key={direction.id} value={direction.id}>
                  {direction.name}
                </option>
              ))}
            </Select>
          </Field>
          <div className="flex items-end">
            <Button type="button" variant="outline" onClick={() => setShowArchived((value) => !value)}>
              {showArchived ? "Voir actifs" : "Voir archives"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {projects.length === 0 && (
        <Card className="premium-panel">
          <CardContent className="premium-subtle">Aucun projet ne correspond au filtre sélectionné.</CardContent>
        </Card>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        {projects.map((project) => (
          <Card key={project.id} className="premium-panel premium-lift border-stone-300/70 bg-white/90">
            <CardHeader>
              <CardTitle className="flex items-center justify-between gap-3">
                <span>{project.title}</span>
                <Badge variant={badgeVariantFromProjetStatus(project.status)}>{labelFromProjetStatus(project.status)}</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-sm">
              <div className="grid gap-2 text-muted-foreground">
                <p>Direction: {project.direction_name ?? "-"}</p>
                <p>Directeur: {project.director_name ?? "-"}</p>
                <p>Manager: {project.manager_name ?? "-"}</p>
                <p>Fiche de poste: {project.fiche_title ?? "-"}</p>
                <p>Besoin principal: {project.besoin_title ?? "-"}</p>
                <p>Nombre de postes: {project.nombre_postes ?? "-"}</p>
              </div>

              <div className="space-y-2 rounded-lg border border-stone-300/70 bg-stone-50/70 p-3">
                <p className="flex items-center gap-2 text-xs uppercase tracking-wide text-muted-foreground"><Mail className="size-4" />Objet d&apos;email</p>
                {editingProjectId === project.id ? (
                  <div className="space-y-2">
                    <textarea
                      className="w-full rounded-md border p-2 text-sm"
                      value={emailDraft}
                      onChange={(event) => setEmailDraft(event.target.value)}
                    />
                    <div className="flex gap-2">
                      <Button size="sm" onClick={() => void saveEmailSubject(project.id)}>Enregistrer</Button>
                      <Button size="sm" variant="outline" onClick={() => { setEditingProjectId(null); setEmailDraft("") }}>Annuler</Button>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-sm">{project.email_subject ?? "-"}</p>
                    <div className="flex gap-2">
                      <Button size="icon-sm" variant="outline" onClick={() => void copyEmailSubject(project.email_subject ?? "")}> 
                        <Copy className="size-4" />
                      </Button>
                      {canEditEmailSubject && (
                        <Button
                          size="icon-sm"
                          variant="outline"
                          onClick={() => {
                            setEditingProjectId(project.id)
                            setEmailDraft(project.email_subject ?? "")
                          }}
                        >
                          <Pencil className="size-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                )}
              </div>

              <div className="flex flex-wrap gap-2">
                <Button asChild variant="outline">
                  <Link href={`/projets/${project.id}`}>Gérer</Link>
                </Button>
                <Button asChild variant="outline">
                  <Link href={`/projets/${project.id}/offre`}>Voir / générer l&apos;offre</Link>
                </Button>
                <Button asChild variant="outline">
                  <Link href={`/projets/${project.id}/candidatures`}>Voir les candidatures</Link>
                </Button>
                {canManageProjects && project.status !== "CLOSED" && !showArchived && (
                  <Button variant="secondary" onClick={() => void closeProject(project.id)}>
                    Fermer le projet
                  </Button>
                )}
                {canManageProjects && (
                  <Button variant="destructive" onClick={() => void deleteProject(project.id)}>
                    Supprimer
                  </Button>
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
