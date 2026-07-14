"use client"

import { use, useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { toast } from "sonner"

import { RoleGate } from "@/components/role-gate"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { ApiHttpError, apiClient } from "@/lib/http"
import type { ApiResponse, BesoinPriority, BesoinRecrutementResponse, FicheDePosteResponse, PaginatedResponse } from "@/lib/backend-types"
import { badgeVariantFromBesoinStatus } from "@/lib/status-labels"
import { useAuth } from "@/components/auth-provider"

export default function BesoinDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params)
  const besoinId = Number(resolvedParams.id)

  if (Number.isNaN(besoinId)) {
    return (
      <RoleGate roles={["ADMIN", "DRH", "DIRECTEUR", "DG"]}>
        <Card>
          <CardContent>Identifiant besoin invalide.</CardContent>
        </Card>
      </RoleGate>
    )
  }

  return (
    <RoleGate roles={["ADMIN", "DRH", "DIRECTEUR", "DG"]}>
      <DetailContent id={besoinId} />
    </RoleGate>
  )
}

function DetailContent({ id }: { id: number }) {
  const router = useRouter()
  const { user } = useAuth()
  const [item, setItem] = useState<BesoinRecrutementResponse | null>(null)
  const [fiches, setFiches] = useState<FicheDePosteResponse[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [form, setForm] = useState({ lieu_affectation: "", recruitment_reason: "", priority: "NORMALE", positions_count: "", desired_date: "", fiche_de_poste_id: "" })

  const reload = async () => {
    const [needRes, fichesRes] = await Promise.all([
      apiClient.get<ApiResponse<BesoinRecrutementResponse>>(`/besoins/${id}`),
      apiClient.get<PaginatedResponse<FicheDePosteResponse>>("/fiches-de-poste/", { params: { page: 1, page_size: 100 } }),
    ])

    setItem(needRes.data.data)
    setFiches(fichesRes.data.data)
    setForm({
      lieu_affectation: needRes.data.data.lieu_affectation ?? "",
      recruitment_reason: needRes.data.data.justification ?? "",
      priority: needRes.data.data.priority,
      positions_count: needRes.data.data.positions_count?.toString() ?? "",
      desired_date: needRes.data.data.desired_date ?? "",
      fiche_de_poste_id: needRes.data.data.fiche_de_poste_id.toString(),
    })
  }

  useEffect(() => {
    let cancelled = false

    const load = async () => {
      setIsLoading(true)
      setError(null)
      try {
        const [needRes, fichesRes] = await Promise.all([
          apiClient.get<ApiResponse<BesoinRecrutementResponse>>(`/besoins/${id}`),
          apiClient.get<PaginatedResponse<FicheDePosteResponse>>("/fiches-de-poste/", { params: { page: 1, page_size: 100 } }),
        ])
        if (cancelled) {
          return
        }

        setItem(needRes.data.data)
        setFiches(fichesRes.data.data)
        setForm({
          lieu_affectation: needRes.data.data.lieu_affectation ?? "",
          recruitment_reason: needRes.data.data.justification ?? "",
          priority: needRes.data.data.priority,
          positions_count: needRes.data.data.positions_count?.toString() ?? "",
          desired_date: needRes.data.data.desired_date ?? "",
          fiche_de_poste_id: needRes.data.data.fiche_de_poste_id.toString(),
        })
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiHttpError ? err.message : "Impossible de charger ce besoin.")
          setItem(null)
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
  }, [id])

  const save = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const availableFiches = fiches
    const directeurOwnsDirection = user?.role === "DIRECTEUR" && availableFiches.some((fiche) => fiche.id === item?.fiche_de_poste_id)
    const canEditCurrent = user?.role === "ADMIN" || user?.role === "DRH" || directeurOwnsDirection
    if (!item || !canEditCurrent || item.status !== "SUBMITTED") {
      setActionError("Vous n'avez pas la permission de modifier ce besoin.")
      return
    }

    setActionError(null)
    try {
      const response = await apiClient.put<ApiResponse<BesoinRecrutementResponse>>(`/besoins/${id}`, {
        lieu_affectation: form.lieu_affectation || null,
        recruitment_reason: form.recruitment_reason || null,
        priority: form.priority as BesoinPriority,
        positions_count: form.positions_count ? Number(form.positions_count) : null,
        desired_date: form.desired_date || null,
        fiche_de_poste_id: Number(form.fiche_de_poste_id),
      })
      setItem(response.data.data)
      toast.success("Besoin sauvegardé avec succès.")
      router.push("/besoins")
    } catch (err) {
      const message = err instanceof ApiHttpError ? err.message : "Impossible de sauvegarder ce besoin."
      setActionError(message)
      toast.error(message)
    }
  }

  if (isLoading) return <Card><CardContent>Chargement…</CardContent></Card>
  if (error) return <Card><CardContent>{error}</CardContent></Card>
  if (!item) return <Card><CardContent>Besoin introuvable.</CardContent></Card>

  const currentFiche = fiches.find((fiche) => fiche.id === item.fiche_de_poste_id)
  const directeurOwnsCurrentDirection = user?.role === "DIRECTEUR" && currentFiche != null
  const editable = (user?.role === "ADMIN" || user?.role === "DRH" || directeurOwnsCurrentDirection) && item.status === "SUBMITTED"
  const canApprove = (user?.role === "DRH" || user?.role === "ADMIN") && item.status === "SUBMITTED"
  const canReject = (user?.role === "DRH" || user?.role === "ADMIN") && item.status === "SUBMITTED"
  const canDelete = editable
  const availableFiches = fiches

  return (
    <Card>
      <CardHeader><CardTitle>{item.fiche_title ?? `Besoin #${item.id}`} <Badge variant={badgeVariantFromBesoinStatus(item.status)}>{item.status}</Badge></CardTitle></CardHeader>
      <CardContent>
        {actionError && <p className="mb-4 text-sm text-destructive">{actionError}</p>}
        <form className="grid gap-4 md:grid-cols-2" onSubmit={save}>
          <Field label="Fiche de poste"><Select disabled={!editable} value={form.fiche_de_poste_id} onChange={(event) => setForm((current) => ({ ...current, fiche_de_poste_id: event.target.value }))}>{availableFiches.map((fiche) => <option key={fiche.id} value={fiche.id}>{fiche.title}</option>)}</Select></Field>
          <Field label="Direction"><Input value={item.direction_name ?? "-"} disabled /></Field>
          <Field label="Lieu d'affectation"><Input disabled={!editable} value={form.lieu_affectation} onChange={(event) => setForm((current) => ({ ...current, lieu_affectation: event.target.value }))} /></Field>
          <Field label="Motif de recrutement"><Textarea disabled={!editable} value={form.recruitment_reason} onChange={(event) => setForm((current) => ({ ...current, recruitment_reason: event.target.value }))} /></Field>
          <Field label="Priorité"><Select disabled={!editable} value={form.priority} onChange={(event) => setForm((current) => ({ ...current, priority: event.target.value }))}><option value="HAUTE">Haute</option><option value="NORMALE">Normale</option><option value="BASSE">Basse</option></Select></Field>
          <Field label="Nombre de postes"><Input disabled={!editable} type="number" min="1" value={form.positions_count} onChange={(event) => setForm((current) => ({ ...current, positions_count: event.target.value }))} /></Field>
          <Field label="Date souhaitée"><Input disabled={!editable} type="date" value={form.desired_date} onChange={(event) => setForm((current) => ({ ...current, desired_date: event.target.value }))} /></Field>
          <div className="md:col-span-2 flex flex-wrap gap-2">
            {editable && <Button type="submit">Sauvegarder</Button>}
            {canApprove && <Button type="button" onClick={async () => {
              setActionError(null)
              try {
                await apiClient.post(`/besoins/${id}/approuver`)
                toast.success("Besoin approuvé avec succès.")
                await reload()
              } catch (err) {
                const message = err instanceof ApiHttpError ? err.message : "Impossible d'approuver ce besoin."
                setActionError(message)
                toast.error(message)
              }
            }}>Approuver</Button>}
            {canReject && <Button type="button" variant="destructive" onClick={async () => {
              const reason = prompt("Motif du rejet ?") ?? ""
              setActionError(null)
              try {
                await apiClient.post(`/besoins/${id}/rejeter`, { reason })
                toast.success("Besoin rejeté avec succès.")
                await reload()
              } catch (err) {
                const message = err instanceof ApiHttpError ? err.message : "Impossible de rejeter ce besoin."
                setActionError(message)
                toast.error(message)
              }
            }}>Rejeter</Button>}
            {canDelete && <Button type="button" variant="secondary" onClick={async () => {
              setActionError(null)
              try {
                await apiClient.delete(`/besoins/${id}`)
                toast.success("Besoin supprimé avec succès.")
                window.location.href = "/besoins"
              } catch (err) {
                const message = err instanceof ApiHttpError ? err.message : "Impossible de supprimer ce besoin."
                setActionError(message)
                toast.error(message)
              }
            }}>Supprimer</Button>}
          </div>
        </form>
      </CardContent>
    </Card>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <div className="space-y-2"><Label>{label}</Label>{children}</div>
}