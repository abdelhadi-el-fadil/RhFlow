"use client"

import Link from "next/link"
import { use, useEffect, useMemo, useState } from "react"
import {
  ArrowLeft,
  Award,
  BadgeCheck,
  BriefcaseBusiness,
  FileText,
  GraduationCap,
  Loader2,
  Mail,
  Phone,
  UserRound,
} from "lucide-react"

import { RoleGate } from "@/components/role-gate"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type {
  CandidatureResponse,
  PaginatedResponse,
  ProjetRecrutementResponse,
  ApiResponse,
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
          <CardContent className="premium-copy">Parametres invalides.</CardContent>
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
  const [error, setError] = useState<string | null>(null)
  const [projectTitle, setProjectTitle] = useState<string>(`Projet #${projectId}`)
  const [ficheTitle, setFicheTitle] = useState<string>("Fiche de poste")

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
      setError(null)
      try {
        const [projectResponse] = await Promise.all([
          apiClient.get<ApiResponse<ProjetRecrutementResponse>>(`/projets/${projectId}`),
          loadItem(),
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

  const score = item?.score_matching ?? 0
  const scoreCircleStyle = {
    background: `conic-gradient(rgb(15 118 110) ${score * 3.6}deg, rgb(231 229 228) 0deg)`,
  }

  const recommendationLabel = useMemo(() => {
    if (!item?.recommandation) {
      return "-"
    }
    if (item.recommandation === "A_CONVOQUER") {
      return "A convoquer"
    }
    if (item.recommandation === "A_ETUDIER") {
      return "A etudier"
    }
    return "Ne correspond pas"
  }, [item?.recommandation])

  return (
    <div className="stagger-enter space-y-6">
      <div className="flex items-center justify-between gap-3">
        <Button asChild variant="outline">
          <Link href={`/projets/${projectId}/candidatures`}>
            <ArrowLeft className="mr-2 size-4" />Retour aux candidatures
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
          <CardContent className="premium-copy">Chargement de la candidature...</CardContent>
        </Card>
      )}

      {error && (
        <Card className="premium-panel">
          <CardContent className="premium-copy">{error}</CardContent>
        </Card>
      )}

      {!loading && !error && !item && (
        <Card className="premium-panel">
          <CardContent className="premium-copy">Candidature introuvable dans ce projet.</CardContent>
        </Card>
      )}

      {item && (
        <Card className="premium-panel premium-lift border-stone-300/70 bg-linear-to-br from-white to-stone-50">
          <CardHeader>
            <CardTitle className="premium-title">{ficheTitle}</CardTitle>
            <p className="premium-copy text-sm">
              {projectTitle} · {item.nom_candidat ?? "Candidat non identifie"}
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
            {item.statut === "EN_COURS" && (
              <div className="flex items-center gap-2 rounded-lg border border-teal-200 bg-teal-50 px-3 py-2 text-sm text-teal-800">
                <Loader2 className="size-4 animate-spin" />
                Traitement en cours: parsing markdown, extraction LLM, evaluation IA.
              </div>
            )}

            <div className="space-y-4">
              <Card className="border-stone-300/70 bg-white/95">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <FileText className="size-4 text-teal-700" />
                    Informations fichier
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm text-slate-700">
                  <p><strong>Nom:</strong> {item.nom_fichier}</p>
                  <p><strong>Type:</strong> {item.type_fichier}</p>
                  <p><strong>Taille:</strong> {item.taille_fichier ?? "-"} octets</p>
                  <p><strong>Date depot:</strong> {formatDate(item.depose_le)}</p>
                </CardContent>
              </Card>

              <Card className="border-stone-300/70 bg-white/95">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <UserRound className="size-4 text-emerald-700" />
                    Informations candidat
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 text-sm text-slate-700">
                  <div className="rounded-md border border-stone-200 bg-white p-3">
                    <p className="mb-1 text-xs font-medium uppercase tracking-wide text-slate-500">Nom</p>
                    <p className="flex items-center gap-2"><UserRound className="size-4 text-slate-500" />{item.nom_candidat ?? "-"}</p>
                  </div>
                  <div className="rounded-md border border-stone-200 bg-white p-3">
                    <p className="mb-1 text-xs font-medium uppercase tracking-wide text-slate-500">Email</p>
                    <p className="flex items-center gap-2"><Mail className="size-4 text-slate-500" />{item.email_candidat ?? "-"}</p>
                  </div>
                  <div className="rounded-md border border-stone-200 bg-white p-3">
                    <p className="mb-1 text-xs font-medium uppercase tracking-wide text-slate-500">Telephone</p>
                    <p className="flex items-center gap-2"><Phone className="size-4 text-slate-500" />{item.telephone_candidat ?? "-"}</p>
                  </div>

                  <div>
                    <p className="mb-1 font-medium text-slate-900">Skills</p>
                    {item.skills && item.skills.length > 0 ? (
                      <div className="flex flex-wrap gap-2">
                        {item.skills.map((skill) => (
                          <Badge key={`${item.id}-${skill}`} variant="secondary">{skill}</Badge>
                        ))}
                      </div>
                    ) : (
                      <p className="text-slate-500">-</p>
                    )}
                  </div>

                  {item.formations && item.formations.length > 0 && (
                    <div>
                      <p className="mb-1 inline-flex items-center gap-2 font-medium text-slate-900">
                        <GraduationCap className="size-4 text-slate-500" />Formations
                      </p>
                      <ul className="list-disc pl-5">
                        {item.formations.map((formation, idx) => (
                          <li key={`${item.id}-f-${idx}`}>
                            {formation.titre}
                            {formation.dateObtention ? ` (${formation.dateObtention})` : ""}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {item.experiences && item.experiences.length > 0 && (
                    <div>
                      <p className="mb-1 inline-flex items-center gap-2 font-medium text-slate-900">
                        <BriefcaseBusiness className="size-4 text-slate-500" />Experiences
                      </p>
                      <ul className="list-disc pl-5">
                        {item.experiences.map((experience, idx) => (
                          <li key={`${item.id}-e-${idx}`}>
                            {experience.titre}
                            {experience.entreprise ? ` - ${experience.entreprise}` : ""}
                            {experience.periode ? ` (${experience.periode})` : ""}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card className="border-stone-300/70 bg-white/95">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Award className="size-4 text-amber-700" />
                    Evaluation IA
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="mx-auto grid size-36 place-items-center rounded-full" style={scoreCircleStyle}>
                    <div className="grid size-24 place-items-center rounded-full bg-white text-center">
                      <p className="text-xs text-muted-foreground">Score</p>
                      <p className="text-2xl font-bold">{item.score_matching ?? "-"}</p>
                    </div>
                  </div>

                  <p className="inline-flex items-center gap-2 text-sm text-slate-700">
                    <BadgeCheck className="size-4 text-slate-500" />
                    Recommandation: {recommendationLabel}
                  </p>
                  <p className="text-sm text-slate-700">Evalue le: {formatDate(item.evalue_le)}</p>

                  {item.justification_ia && (
                    <div>
                      <p className="mb-1 font-medium text-slate-900">Justification</p>
                      <p className="text-sm text-slate-700">{item.justification_ia}</p>
                    </div>
                  )}

                  {item.points_forts && item.points_forts.length > 0 && (
                    <div>
                      <p className="mb-1 font-medium text-slate-900">Points forts</p>
                      <ul className="list-disc pl-5 text-sm text-slate-700">
                        {item.points_forts.map((point, idx) => (
                          <li key={`${item.id}-pf-${idx}`}>{point}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {item.points_manquants && item.points_manquants.length > 0 && (
                    <div>
                      <p className="mb-1 font-medium text-slate-900">Points a renforcer</p>
                      <ul className="list-disc pl-5 text-sm text-slate-700">
                        {item.points_manquants.map((point, idx) => (
                          <li key={`${item.id}-pm-${idx}`}>{point}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {item.questions_entretien && item.questions_entretien.length > 0 && (
                    <div>
                      <p className="mb-1 font-medium text-slate-900">Questions d'entretien</p>
                      <ul className="list-disc pl-5 text-sm text-slate-700">
                        {item.questions_entretien.map((question, idx) => (
                          <li key={`${item.id}-q-${idx}`}>{question}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
