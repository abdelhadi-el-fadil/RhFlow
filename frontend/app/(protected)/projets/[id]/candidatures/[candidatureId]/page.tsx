"use client"

import Link from "next/link"
import { use, useEffect, useMemo, useState } from "react"
import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  Loader2,
  RefreshCcw,
} from "lucide-react"

import { RoleGate } from "@/components/role-gate"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
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

export default function CandidatureDetailPage({
  params,
}: {
  params: Promise<{ id: string; candidatureId: string }>
}) {
  const resolved = use(params)
  const projectId = Number(resolved.id)
  const candidatureId = Number(resolved.candidatureId)

  if (Number.isNaN(projectId) || Number.isNaN(candidatureId)) {
    return (
      <RoleGate roles={["ADMIN", "DRH", "DIRECTEUR", "DG"]}>
        <Card className="premium-panel">
          <CardContent className="premium-copy">Paramètres invalides.</CardContent>
        </Card>
      </RoleGate>
    )
  }

  return (
    <RoleGate roles={["ADMIN", "DRH", "DIRECTEUR", "DG"]}>
      <DetailContent projectId={projectId} candidatureId={candidatureId} />
    </RoleGate>
  )
}

function DetailContent({
  projectId,
  candidatureId,
}: {
  projectId: number
  candidatureId: number
}) {
  const [item, setItem] = useState<CandidatureResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [extracting, setExtracting] = useState(false)
  const [evaluating, setEvaluating] = useState(false)
  const [actionInfo, setActionInfo] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)

  const loadItem = async (): Promise<CandidatureResponse | null> => {
    const response = await apiClient.get<PaginatedResponse<CandidatureResponse>>(
      `/projets/${projectId}/candidatures/`,
      { params: { page: 1, page_size: 100 } },
    )
    const found = response.data.data.find((candidate) => candidate.id === candidatureId) ?? null
    setItem(found)
    return found
  }

  useEffect(() => {
    let cancelled = false
    const run = async () => {
      setLoading(true)
      try {
        await loadItem()
      } catch (err) {
        if (!cancelled) {
          setActionError(
            err instanceof ApiHttpError
              ? err.message
              : "Impossible de charger la candidature.",
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
  }, [projectId, candidatureId])

  useEffect(() => {
    if (!item || item.statut !== "EN_COURS") {
      return
    }

    const interval = window.setInterval(() => {
      void loadItem().catch(() => {
        // silent polling while processing
      })
    }, 3000)

    return () => {
      window.clearInterval(interval)
    }
  }, [item, projectId, candidatureId])

  const hasExtractedInfo = useMemo(() => {
    if (!item) {
      return false
    }
    return Boolean(
      item.nom_candidat ||
        item.email_candidat ||
        item.telephone_candidat ||
        (item.formations && item.formations.length > 0) ||
        (item.experiences && item.experiences.length > 0),
    )
  }, [item])

  const hasEvaluation = useMemo(() => {
    if (!item) {
      return false
    }
    return Boolean(
      typeof item.score_matching === "number" ||
        item.recommandation ||
        (item.points_forts && item.points_forts.length > 0) ||
        (item.points_manquants && item.points_manquants.length > 0) ||
        (item.questions_entretien && item.questions_entretien.length > 0),
    )
  }, [item])

  const extract = async (): Promise<void> => {
    if (!item) {
      return
    }
    setActionError(null)
    setActionInfo(null)
    setExtracting(true)
    try {
      const response = await apiClient.post<ApiResponse<CandidatureResponse>>(
        `/candidatures/${item.id}/extract`,
      )
      const updated = response.data.data
      setItem(updated)
      if (updated.statut === "ERREUR") {
        setActionError(updated.justification_ia ?? "L'extraction a échoué.")
      } else {
        setActionInfo("Extraction terminée.")
      }
    } catch (err) {
      setActionError(
        err instanceof ApiHttpError ? err.message : "Impossible de lancer l'extraction.",
      )
    } finally {
      setExtracting(false)
    }
  }

  const evaluate = async (): Promise<void> => {
    if (!item) {
      return
    }
    setActionError(null)
    setActionInfo(null)
    setEvaluating(true)
    try {
      const response = await apiClient.post<ApiResponse<CandidatureResponse>>(
        `/candidatures/${item.id}/evaluate`,
      )
      const updated = response.data.data
      setItem(updated)
      if (updated.statut === "ERREUR") {
        setActionError(updated.justification_ia ?? "L'évaluation a échoué.")
      } else {
        setActionInfo("Évaluation IA terminée.")
      }
    } catch (err) {
      setActionError(
        err instanceof ApiHttpError ? err.message : "Impossible de lancer l'évaluation.",
      )
    } finally {
      setEvaluating(false)
    }
  }

  const score = item?.score_matching ?? 0
  const scoreCircleStyle = {
    background: `conic-gradient(rgb(16 185 129) ${score * 3.6}deg, rgb(231 229 228) 0deg)`,
  }

  return (
    <div className="stagger-enter space-y-6">
      <div className="flex items-center justify-between gap-3">
        <Button asChild variant="outline">
          <Link href={`/projets/${projectId}/candidatures`}>
            <ArrowLeft className="mr-2 size-4" />Retour aux CV
          </Link>
        </Button>
        {item && (
          <Badge variant={badgeVariantFromCandidatureStatut(item.statut)}>
            {labelFromCandidatureStatut(item.statut)}
          </Badge>
        )}
      </div>

      {loading && (
        <Card className="premium-panel">
          <CardContent className="premium-copy">Chargement de la candidature…</CardContent>
        </Card>
      )}

      {!loading && !item && (
        <Card className="premium-panel">
          <CardContent className="premium-copy">Candidature introuvable dans ce projet.</CardContent>
        </Card>
      )}

      {item && (
        <>
          <Card className="premium-panel premium-lift border-stone-300/70 bg-white/90">
            <CardHeader>
              <CardTitle>{item.nom_candidat ?? item.nom_fichier}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <p>Fichier: {item.nom_fichier}</p>
              <p>Type: {item.type_fichier}</p>
              <p>Déposé le: {formatDate(item.depose_le)}</p>

              <div className="grid gap-2 md:grid-cols-2">
                <Button variant="outline" onClick={() => void extract()} disabled={extracting || evaluating}>
                  {extracting ? <><Loader2 className="mr-2 size-4 animate-spin" />Extraction...</> : <><RefreshCcw className="mr-2 size-4" />Extraire les champs</>}
                </Button>
                <Button variant="outline" onClick={() => void evaluate()} disabled={extracting || evaluating}>
                  {evaluating ? <><Loader2 className="mr-2 size-4 animate-spin" />Évaluation...</> : <><RefreshCcw className="mr-2 size-4" />Évaluer avec IA</>}
                </Button>
              </div>

              <div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setActionError(null)
                    setActionInfo(null)
                    void loadItem()
                  }}
                >
                  <RefreshCcw className="mr-2 size-4" />Actualiser l'état
                </Button>
              </div>

              {actionInfo && <p className="text-emerald-700">{actionInfo}</p>}
              {actionError && <p className="text-destructive">{actionError}</p>}
            </CardContent>
          </Card>

          <div className="grid gap-4 lg:grid-cols-2">
            <Card className="premium-panel border-stone-300/70 bg-white/90">
              <CardHeader>
                <CardTitle>Informations extraites</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm text-muted-foreground">
                <p>Nom: {item.nom_candidat ?? "-"}</p>
                <p>Email: {item.email_candidat ?? "-"}</p>
                <p>Téléphone: {item.telephone_candidat ?? "-"}</p>

                {item.formations && item.formations.length > 0 && (
                  <div>
                    <p className="font-medium text-foreground">Formations</p>
                    <ul className="list-disc pl-5">
                      {item.formations.map((formation, idx) => (
                        <li key={`${item.id}-f-${idx}`}>{formation.titre}{formation.dateObtention ? ` (${formation.dateObtention})` : ""}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {item.experiences && item.experiences.length > 0 && (
                  <div>
                    <p className="font-medium text-foreground">Expériences</p>
                    <ul className="list-disc pl-5">
                      {item.experiences.map((experience, idx) => (
                        <li key={`${item.id}-e-${idx}`}>{experience.titre}{experience.entreprise ? ` - ${experience.entreprise}` : ""}{experience.periode ? ` (${experience.periode})` : ""}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card className="premium-panel border-stone-300/70 bg-white/90">
              <CardHeader>
                <CardTitle>Score IA</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="mx-auto grid size-40 place-items-center rounded-full" style={scoreCircleStyle}>
                  <div className="grid size-28 place-items-center rounded-full bg-white text-center">
                    <p className="text-xs text-muted-foreground">Matching</p>
                    <p className="text-3xl font-bold">{item.score_matching ?? "-"}</p>
                  </div>
                </div>

                {item.statut === "EVALUE" && (
                  <p className="inline-flex items-center gap-2 text-xs font-medium text-emerald-700">
                    <CheckCircle2 className="size-4" /> Analyse IA terminée
                  </p>
                )}
                {item.statut === "ERREUR" && (
                  <p className="inline-flex items-center gap-2 text-xs font-medium text-destructive">
                    <AlertTriangle className="size-4" /> Analyse IA en erreur
                  </p>
                )}

                {hasEvaluation && (
                  <>
                    <p className="text-sm text-muted-foreground">Recommandation: {item.recommandation ?? "-"}</p>
                    <p className="text-sm text-muted-foreground">Évalué le: {formatDate(item.evalue_le)}</p>
                  </>
                )}

                {item.justification_ia && (
                  <div>
                    <p className="font-medium">Justification IA</p>
                    <p className="text-sm text-muted-foreground">{item.justification_ia}</p>
                  </div>
                )}

                {item.points_forts && item.points_forts.length > 0 && (
                  <div>
                    <p className="font-medium">Points forts</p>
                    <ul className="list-disc pl-5 text-sm text-muted-foreground">
                      {item.points_forts.map((point, idx) => (
                        <li key={`${item.id}-pf-${idx}`}>{point}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {item.points_manquants && item.points_manquants.length > 0 && (
                  <div>
                    <p className="font-medium">Points faibles</p>
                    <ul className="list-disc pl-5 text-sm text-muted-foreground">
                      {item.points_manquants.map((point, idx) => (
                        <li key={`${item.id}-pm-${idx}`}>{point}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {item.questions_entretien && item.questions_entretien.length > 0 && (
                  <div>
                    <p className="font-medium">Questions d'entretien</p>
                    <ul className="list-disc pl-5 text-sm text-muted-foreground">
                      {item.questions_entretien.map((question, idx) => (
                        <li key={`${item.id}-q-${idx}`}>{question}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  )
}
