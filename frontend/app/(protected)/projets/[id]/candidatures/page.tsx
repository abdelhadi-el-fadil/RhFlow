"use client"

import Link from "next/link"
import { use, useEffect, useMemo, useRef, useState } from "react"
import { Loader2, RefreshCcw, Search, Upload } from "lucide-react"

import { RoleGate } from "@/components/role-gate"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import type {
  ApiResponse,
  CandidatureResponse,
  PaginatedResponse,
} from "@/lib/backend-types"
import { ApiHttpError, apiClient } from "@/lib/http"
import {
  badgeVariantFromCandidatureStatut,
  labelFromCandidatureStatut,
} from "@/lib/status-labels"

const MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024
const ALLOWED_EXTENSIONS = new Set(["pdf", "png", "jpg", "jpeg"])

function formatBytes(size: number | null): string {
  if (size === null) {
    return "-"
  }
  if (size < 1024) {
    return `${size} B`
  }
  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`
  }
  return `${(size / (1024 * 1024)).toFixed(2)} MB`
}

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
  const fileInputRef = useRef<HTMLInputElement | null>(null)
  const [items, setItems] = useState<CandidatureResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [reloading, setReloading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [actionInfo, setActionInfo] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [query, setQuery] = useState("")

  const loadItems = async (): Promise<void> => {
    const response = await apiClient.get<PaginatedResponse<CandidatureResponse>>(
      `/projets/${projectId}/candidatures/`,
      { params: { page: 1, page_size: 100 } },
    )
    setItems(response.data.data)
  }

  useEffect(() => {
    let cancelled = false
    const run = async () => {
      setLoading(true)
      setError(null)
      try {
        await loadItems()
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
        // silent polling
      })
    }, 3000)

    return () => {
      window.clearInterval(interval)
    }
  }, [items, projectId])

  const refreshItems = async (): Promise<void> => {
    setReloading(true)
    setActionError(null)
    setActionInfo(null)
    try {
      await loadItems()
    } catch (err) {
      setActionError(
        err instanceof ApiHttpError
          ? err.message
          : "Impossible de rafraîchir les candidatures.",
      )
    } finally {
      setReloading(false)
    }
  }

  const validateSelectedFile = (file: File): string | null => {
    const extension = file.name.split(".").pop()?.toLowerCase() ?? ""
    if (!ALLOWED_EXTENSIONS.has(extension)) {
      return "Format non supporté. Utilisez PDF, PNG, JPG ou JPEG."
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
      setActionInfo("CV uploadé. Cliquez sur Voir candidature pour lancer extraction et évaluation.")
    } catch (err) {
      if (err instanceof ApiHttpError) {
        setActionError(err.message)
      } else {
        setActionError("Échec de l'upload de la candidature.")
      }
    } finally {
      setUploading(false)
    }
  }

  const visibleItems = useMemo(() => {
    const normalized = query.trim().toLowerCase()
    if (!normalized) {
      return items
    }
    return items.filter((item) => {
      const text = [
        item.nom_candidat,
        item.email_candidat,
        item.telephone_candidat,
        item.nom_fichier,
        item.recommandation,
        item.statut,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
      return text.includes(normalized)
    })
  }, [items, query])

  return (
    <div className="stagger-enter space-y-6">
      <Card className="premium-panel premium-lift border-amber-200/65 bg-linear-to-br from-stone-50 via-amber-50 to-teal-50">
        <CardHeader>
          <CardTitle className="premium-title">CV du projet #{projectId}</CardTitle>
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
            <input
              value={selectedFile?.name ?? ""}
              readOnly
              placeholder="Aucun fichier sélectionné"
              className="w-full"
            />
            <Button onClick={() => void uploadCandidature()} disabled={uploading || !selectedFile}>
              {uploading ? (
                <><Loader2 className="mr-2 size-4 animate-spin" />Upload en cours</>
              ) : (
                <><Upload className="mr-2 size-4" />Téléverser le CV</>
              )}
            </Button>
            <Button variant="outline" onClick={() => void refreshItems()} disabled={reloading}>
              {reloading ? <Loader2 className="mr-2 size-4 animate-spin" /> : <RefreshCcw className="mr-2 size-4" />}
              Rafraîchir
            </Button>
          </div>

          <div className="relative">
            <Search className="pointer-events-none absolute left-2 top-2.5 size-4 text-muted-foreground" />
            <Input
              className="pl-8"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Rechercher candidat, email, statut, fichier"
            />
          </div>

          {selectedFile && (
            <p className="premium-subtle text-sm">
              Fichier sélectionné: {selectedFile.name} ({formatBytes(selectedFile.size)})
            </p>
          )}
          {actionInfo && <p className="text-sm text-emerald-700">{actionInfo}</p>}
          {actionError && <p className="text-sm text-destructive">{actionError}</p>}
        </CardContent>
      </Card>

      {loading && (
        <Card className="premium-panel">
          <CardContent className="premium-copy">Chargement des candidatures…</CardContent>
        </Card>
      )}

      {error && (
        <Card className="premium-panel">
          <CardContent className="premium-copy">{error}</CardContent>
        </Card>
      )}

      {!loading && !error && visibleItems.length === 0 && (
        <Card className="premium-panel">
          <CardContent className="premium-subtle">
            Aucun CV pour ce projet ou pour la recherche en cours.
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {visibleItems.map((item) => (
          <Card key={item.id} className="premium-panel premium-lift border-stone-300/70 bg-white/90">
            <CardHeader>
              <CardTitle className="flex items-center justify-between gap-3 text-base">
                <span className="line-clamp-1">{item.nom_candidat ?? item.nom_fichier}</span>
                <Badge variant={badgeVariantFromCandidatureStatut(item.statut)}>
                  {labelFromCandidatureStatut(item.statut)}
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm text-muted-foreground">
              <p>Fichier: {item.nom_fichier}</p>
              <p>Type: {item.type_fichier}</p>
              <p>Taille: {formatBytes(item.taille_fichier)}</p>
              <p>Déposé: {formatDate(item.depose_le)}</p>
              <Button asChild className="w-full">
                <Link href={`/projets/${projectId}/candidatures/${item.id}`}>
                  Voir candidature
                </Link>
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}