"use client"

import Link from "next/link"
import { use, useEffect, useEffectEvent, useMemo, useRef, useState } from "react"
import { FileText, Loader2, Search, Sparkles, Trash2, Upload } from "lucide-react"
import { toast } from "sonner"

import { useAuth } from "@/components/auth-provider"
import { RoleGate } from "@/components/role-gate"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import type {
  ApiResponse,
  CandidatureResponse,
  PaginatedResponse,
  ProjetRecrutementResponse,
} from "@/lib/backend-types"
import { ApiHttpError, apiClient } from "@/lib/http"
import {
  badgeVariantFromCandidatureStatut,
  labelFromCandidatureStatut,
} from "@/lib/status-labels"

const MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024
const ALLOWED_EXTENSIONS = new Set(["pdf", "png", "jpg", "jpeg"])

function formatDate(value: string | null): string {
  if (!value) {
    return "-"
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return new Intl.DateTimeFormat("fr-FR", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date)
}

export default function ProjetCandidaturesPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params)
  const projectId = Number(resolvedParams.id)

  if (Number.isNaN(projectId)) {
    return (
      <RoleGate roles={["ADMIN", "DRH", "DIRECTEUR", "DG"]}>
        <Card className="premium-panel">
          <CardContent className="premium-copy">Identifiant projet invalide.</CardContent>
        </Card>
      </RoleGate>
    )
  }

  return (
    <RoleGate roles={["ADMIN", "DRH", "DIRECTEUR", "DG"]}>
      <Content projectId={projectId} />
    </RoleGate>
  )
}

function Content({ projectId }: { projectId: number }) {
  const { user } = useAuth()
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  const [items, setItems] = useState<CandidatureResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionInfo, setActionInfo] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const [deletingId, setDeletingId] = useState<number | null>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [query, setQuery] = useState("")
  const [projectTitle, setProjectTitle] = useState<string>(`Projet #${projectId}`)
  const [ficheTitle, setFicheTitle] = useState<string>("Fiche de poste")
  const canDelete = user?.role === "ADMIN" || user?.role === "DRH"

  const loadItems = useEffectEvent(async (): Promise<void> => {
    const response = await apiClient.get<PaginatedResponse<CandidatureResponse>>(
      `/projets/${projectId}/candidatures/`,
      { params: { page: 1, page_size: 100 } },
    )
    setItems(response.data.data)
  })

  useEffect(() => {
    let cancelled = false
    const run = async () => {
      setLoading(true)
      setError(null)
      try {
        const [projectResponse] = await Promise.all([
          apiClient.get<ApiResponse<ProjetRecrutementResponse>>(`/projets/${projectId}`),
          loadItems(),
        ])

        if (cancelled) {
          return
        }

        const project = projectResponse.data.data
        setProjectTitle(project.title)
        setFicheTitle(project.fiche_title ?? "Fiche de poste")
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof ApiHttpError
              ? err.message
              : "Impossible de charger les candidatures.",
          )
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    void run()
    return () => {
      cancelled = true
    }
  }, [projectId])

  useEffect(() => {
    const hasPending = items.some((item) => item.statut === "EN_COURS")
    if (!hasPending) {
      return
    }

    const interval = window.setInterval(() => {
      void loadItems().catch(() => {
        // silent polling while background pipeline runs
      })
    }, 3000)

    return () => {
      window.clearInterval(interval)
    }
  }, [items, projectId])

  const validateSelectedFile = (file: File): string | null => {
    const extension = file.name.split(".").pop()?.toLowerCase() ?? ""
    if (!ALLOWED_EXTENSIONS.has(extension)) {
      return "Format non supporte. Utilisez PDF, PNG, JPG ou JPEG."
    }
    if (file.size > MAX_UPLOAD_SIZE_BYTES) {
      return "Fichier trop volumineux (max 10 MB)."
    }
    return null
  }

  const uploadCandidature = async (): Promise<void> => {
    if (!selectedFile) {
      setActionError("Choisissez un fichier CV avant l'envoi.")
      return
    }

    const validationError = validateSelectedFile(selectedFile)
    if (validationError) {
      setActionError(validationError)
      return
    }

    setActionError(null)
    setActionInfo(null)
    setUploading(true)
    try {
      const formData = new FormData()
      formData.append("file", selectedFile)
      formData.append("projet_recrutement_id", String(projectId))

      const response = await apiClient.post<ApiResponse<CandidatureResponse>>(
        "/candidatures/",
        formData,
      )

      const uploaded = response.data.data
      setItems((current) => [uploaded, ...current.filter((item) => item.id !== uploaded.id)])

      setSelectedFile(null)
      if (fileInputRef.current) {
        fileInputRef.current.value = ""
      }
      setActionInfo(
        "CV televerse. Le parsing markdown, l'extraction LLM et l'evaluation IA s'executent en arriere-plan.",
      )
    } catch (err) {
      if (err instanceof ApiHttpError) {
        setActionError(err.message)
      } else {
        setActionError("Echec de l'upload de la candidature.")
      }
    } finally {
      setUploading(false)
    }
  }

  const deleteCandidature = async (candidatureId: number): Promise<void> => {
    if (!canDelete) {
      return
    }
    if (!window.confirm("Supprimer cette candidature ?")) {
      return
    }

    setActionError(null)
    setActionInfo(null)
    setDeletingId(candidatureId)
    try {
      await apiClient.delete(`/candidatures/${candidatureId}`)
      setItems((current) => current.filter((item) => item.id !== candidatureId))
      toast.success("Candidature supprimée avec succès.")
    } catch (err) {
      const message = err instanceof ApiHttpError ? err.message : "Impossible de supprimer cette candidature."
      setActionError(message)
      toast.error(message)
    } finally {
      setDeletingId(null)
    }
  }

  const normalizedQuery = query.trim().toLowerCase()
  const matchingItems = useMemo(() => {
    if (!normalizedQuery) {
      return items
    }
    return items.filter((item) => {
      const text = [
        item.nom_candidat,
        item.email_candidat,
        item.nom_fichier,
        item.type_fichier,
        item.statut,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
      return text.includes(normalizedQuery)
    })
  }, [items, normalizedQuery])

  const readyItems = matchingItems.filter((item) => item.statut === "EVALUE")

  return (
    <div className="stagger-enter space-y-6">
      <Card className="premium-panel premium-lift border-amber-200/65 bg-linear-to-br from-stone-50 via-amber-50 to-teal-50">
        <CardHeader>
          <CardTitle className="premium-title">{projectTitle}</CardTitle>
          <p className="premium-copy text-sm">{ficheTitle}</p>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex flex-col gap-3 rounded-lg border border-stone-300/70 bg-white/70 p-3 md:flex-row md:items-center">
            <input
              ref={fileInputRef}
              id="candidature-cv-file"
              type="file"
              accept=".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg"
              onChange={(event) => {
                const file = event.target.files?.[0] ?? null
                setSelectedFile(file)
                setActionError(null)
                setActionInfo(null)
              }}
              className="hidden"
            />
            <Button asChild variant="outline">
              <label htmlFor="candidature-cv-file">
                <Upload className="mr-2 size-4" />
                Choisir un CV
              </label>
            </Button>
            <Input
              value={selectedFile?.name ?? ""}
              readOnly
              placeholder="Aucun fichier selectionne"
              className="w-full"
            />
            <Button onClick={() => void uploadCandidature()} disabled={uploading || !selectedFile}>
              {uploading ? (
                <><Loader2 className="mr-2 size-4 animate-spin" />Upload en cours</>
              ) : (
                <><Sparkles className="mr-2 size-4" />Upload et traitement IA</>
              )}
            </Button>
          </div>

          <div className="relative">
            <Search className="pointer-events-none absolute left-2 top-2.5 size-4 text-muted-foreground" />
            <Input
              className="pl-8"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Rechercher candidat, fichier, type, statut"
            />
          </div>

          {actionInfo && <p className="text-sm text-emerald-700">{actionInfo}</p>}
          {actionError && <p className="text-sm text-destructive">{actionError}</p>}
        </CardContent>
      </Card>

      {loading && (
        <Card className="premium-panel">
          <CardContent className="premium-copy">Chargement des candidatures...</CardContent>
        </Card>
      )}

      {error && (
        <Card className="premium-panel">
          <CardContent className="premium-copy">{error}</CardContent>
        </Card>
      )}

      {!loading && !error && readyItems.length === 0 && (
        <Card className="premium-panel">
          <CardContent className="premium-subtle">
            Aucune candidature evaluee pour le moment.
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {readyItems.map((item) => (
          <Card key={item.id} className="premium-panel premium-lift border-stone-300/70 bg-white/90">
            <CardHeader className="space-y-1">
              <CardTitle className="text-base">{ficheTitle}</CardTitle>
              <p className="text-sm text-slate-700">{item.nom_candidat ?? "Candidat non identifie"}</p>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-muted-foreground">
              <div className="flex items-center gap-2">
                <FileText className="size-4 text-teal-700" />
                <span className="line-clamp-1">{item.nom_fichier}</span>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="outline">{item.type_fichier}</Badge>
                <Badge variant={badgeVariantFromCandidatureStatut(item.statut)}>
                  {labelFromCandidatureStatut(item.statut)}
                </Badge>
              </div>
              <p className="text-xs text-slate-600">Depose le {formatDate(item.depose_le)}</p>
              <div className="flex gap-2">
                <Button asChild className="flex-1">
                  <Link href={`/projets/${projectId}/candidatures/${item.id}`}>Voir details</Link>
                </Button>
                {canDelete && (
                  <Button
                    type="button"
                    variant="outline"
                    size="icon"
                    disabled={deletingId === item.id}
                    onClick={() => void deleteCandidature(item.id)}
                    aria-label="Supprimer la candidature"
                  >
                    {deletingId === item.id ? <Loader2 className="size-4 animate-spin" /> : <Trash2 className="size-4" />}
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
