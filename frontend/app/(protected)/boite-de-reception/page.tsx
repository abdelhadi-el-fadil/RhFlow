"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import { Inbox, Loader2, Search, TriangleAlert, Trash2, UserRound } from "lucide-react"
import { toast } from "sonner"

import { useAuth } from "@/components/auth-provider"
import { RoleGate } from "@/components/role-gate"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import type { CandidatureResponse, PaginatedResponse } from "@/lib/backend-types"
import { ApiHttpError, apiClient } from "@/lib/http"
import { badgeVariantFromCandidatureStatut, labelFromCandidatureStatut } from "@/lib/status-labels"

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

export default function InboxPage() {
  return (
    <RoleGate roles={["ADMIN", "DRH", "DIRECTEUR", "DG"]}>
      <InboxContent />
    </RoleGate>
  )
}

function InboxContent() {
  const { user } = useAuth()
  const [items, setItems] = useState<CandidatureResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [query, setQuery] = useState("")
  const [deletingId, setDeletingId] = useState<number | null>(null)

  const canDelete = user?.role === "ADMIN" || user?.role === "DRH"

  const loadItems = async (): Promise<void> => {
    const response = await apiClient.get<PaginatedResponse<CandidatureResponse>>(
      "/candidatures/errors/",
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
          setError(err instanceof ApiHttpError ? err.message : "Impossible de charger les candidatures en erreur.")
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
  }, [])

  const deleteCandidature = async (candidatureId: number): Promise<void> => {
    if (!canDelete) {
      return
    }
    if (!window.confirm("Supprimer cette candidature ?")) {
      return
    }

    setDeletingId(candidatureId)
    setError(null)
    try {
      await apiClient.delete(`/candidatures/${candidatureId}`)
      setItems((current) => current.filter((item) => item.id !== candidatureId))
      toast.success("Candidature supprimée avec succès.")
    } catch (err) {
      const message = err instanceof ApiHttpError ? err.message : "Impossible de supprimer cette candidature."
      setError(message)
      toast.error(message)
    } finally {
      setDeletingId(null)
    }
  }

  const normalizedQuery = query.trim().toLowerCase()
  const filteredItems = useMemo(() => {
    if (!normalizedQuery) {
      return items
    }
    return items.filter((item) => {
      const text = [
        item.nom_candidat,
        item.email_candidat,
        item.nom_fichier,
        item.projet_title,
        item.error_summary,
        item.error_detail,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
      return text.includes(normalizedQuery)
    })
  }, [items, normalizedQuery])

  return (
    <div className="stagger-enter space-y-6">
      <Card className="premium-panel premium-lift border-red-200/70 bg-linear-to-br from-white via-red-50 to-amber-50">
        <CardHeader>
          <CardTitle className="premium-title flex items-center gap-2">
            <Inbox className="size-5 text-red-700" />
            Boite de reception
          </CardTitle>
          <p className="premium-copy text-sm">
            Toutes les candidatures dont le traitement automatique a echoue.
          </p>
        </CardHeader>
        <CardContent>
          <div className="relative">
            <Search className="pointer-events-none absolute left-2 top-2.5 size-4 text-muted-foreground" />
            <Input
              className="pl-8"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Rechercher candidat, projet, fichier ou erreur"
            />
          </div>
        </CardContent>
      </Card>

      {loading && (
        <Card className="premium-panel">
          <CardContent className="premium-copy">Chargement des candidatures en erreur...</CardContent>
        </Card>
      )}

      {error && (
        <Card className="premium-panel">
          <CardContent className="premium-copy">{error}</CardContent>
        </Card>
      )}

      {!loading && !error && filteredItems.length === 0 && (
        <Card className="premium-panel">
          <CardContent className="premium-subtle">Aucune candidature en erreur.</CardContent>
        </Card>
      )}

      <div className="grid gap-4 xl:grid-cols-2">
        {filteredItems.map((item) => (
          <Card key={item.id} className="premium-panel border-red-200/70 bg-white/95">
            <CardHeader className="space-y-2">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <CardTitle className="text-base text-slate-900">{item.nom_candidat ?? item.nom_fichier}</CardTitle>
                  <p className="text-sm text-slate-600">{item.projet_title ?? `Projet #${item.projet_recrutement_id}`}</p>
                </div>
                <Badge variant={badgeVariantFromCandidatureStatut(item.statut)}>
                  {labelFromCandidatureStatut(item.statut)}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4 text-sm">
              <div className="inline-flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-red-950">
                <TriangleAlert className="mt-0.5 size-4 shrink-0 text-red-700" />
                <div>
                  <p className="font-medium">{item.error_summary ?? "Le traitement automatique de cette candidature a echoue."}</p>
                  <p className="mt-1 text-xs text-red-800">Depot: {formatDate(item.depose_le)}</p>
                </div>
              </div>

              {item.error_detail && (
                <div className="rounded-lg border border-stone-200 bg-stone-50 p-3">
                  <p className="mb-1 font-medium text-slate-900">Detail technique</p>
                  <p className="whitespace-pre-wrap text-slate-700">{item.error_detail}</p>
                </div>
              )}

              <div className="rounded-lg border border-stone-200 bg-white p-3 text-slate-700">
                <p className="inline-flex items-center gap-2 font-medium text-slate-900">
                  <UserRound className="size-4 text-slate-500" />
                  Contact candidat
                </p>
                <p className="mt-2">Email: {item.email_candidat ?? "-"}</p>
                <p>Téléphone: {item.telephone_candidat ?? "-"}</p>
                <p>Fichier: {item.nom_fichier}</p>
              </div>

              <div className="flex flex-wrap gap-2">
                <Button asChild>
                  <Link href={`/projets/${item.projet_recrutement_id}/candidatures/${item.id}`}>Voir la candidature</Link>
                </Button>
                {canDelete && (
                  <Button
                    type="button"
                    variant="outline"
                    disabled={deletingId === item.id}
                    onClick={() => void deleteCandidature(item.id)}
                  >
                    {deletingId === item.id ? <Loader2 className="mr-2 size-4 animate-spin" /> : <Trash2 className="mr-2 size-4" />}
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