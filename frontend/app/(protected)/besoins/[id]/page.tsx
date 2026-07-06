"use client"

import { use, useEffect, useState } from "react"

import { RoleGate } from "@/components/role-gate"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { ApiHttpError, apiClient } from "@/lib/http"
import type { ApiResponse, BesoinRecrutementResponse, FicheDePosteResponse, PaginatedResponse } from "@/lib/backend-types"
import { badgeVariantFromBesoinStatus } from "@/lib/status-labels"
import { useAuth } from "@/components/auth-provider"

export default function BesoinDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params)
  const besoinId = Number(resolvedParams.id)

  if (Number.isNaN(besoinId)) {
    return (
      <RoleGate roles={["ADMIN", "DRH", "DIRECTEUR"]}>
        <Card>
          <CardContent>Identifiant besoin invalide.</CardContent>
        </Card>
      </RoleGate>
    )
  }

  return (
    <RoleGate roles={["ADMIN", "DRH", "DIRECTEUR"]}>
      <DetailContent id={besoinId} />
    </RoleGate>
  )
}

function DetailContent({ id }: { id: number }) {
  const { user } = useAuth()
  const [item, setItem] = useState<BesoinRecrutementResponse | null>(null)
  const [fiches, setFiches] = useState<FicheDePosteResponse[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [form, setForm] = useState({ title: "", description: "", positions_count: "", desired_date: "", justification: "", fiche_de_poste_id: "" })

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
          title: needRes.data.data.title,
          description: needRes.data.data.description ?? "",
          positions_count: needRes.data.data.positions_count?.toString() ?? "",
          desired_date: needRes.data.data.desired_date ?? "",
          justification: needRes.data.data.justification ?? "",
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
    const response = await apiClient.put<ApiResponse<BesoinRecrutementResponse>>(`/besoins/${id}`, {
      title: form.title,
      description: form.description || null,
      positions_count: form.positions_count ? Number(form.positions_count) : null,
      desired_date: form.desired_date || null,
      justification: form.justification || null,
      fiche_de_poste_id: Number(form.fiche_de_poste_id),
    })
    setItem(response.data.data)
  }

  if (isLoading) return <Card><CardContent>Chargement…</CardContent></Card>
  if (error) return <Card><CardContent>{error}</CardContent></Card>
  if (!item) return <Card><CardContent>Besoin introuvable.</CardContent></Card>

  const editable = user?.id === item.created_by_id && item.status === "DRAFT"
  const canSubmit = user?.role === "DIRECTEUR" && item.status === "DRAFT"
  const canApprove = user?.role === "DRH" && item.status === "SUBMITTED"
  const canReject = user?.role === "DRH" && item.status === "SUBMITTED"
  const canDelete = user?.id === item.created_by_id && item.status === "DRAFT"

  return (
    <Card>
      <CardHeader><CardTitle>{item.title} <Badge variant={badgeVariantFromBesoinStatus(item.status)}>{item.status}</Badge></CardTitle></CardHeader>
      <CardContent>
        <form className="grid gap-4 md:grid-cols-2" onSubmit={save}>
          <Field label="Titre"><Input disabled={!editable} value={form.title} onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))} /></Field>
          <Field label="Fiche de poste"><Select disabled={!editable} value={form.fiche_de_poste_id} onChange={(event) => setForm((current) => ({ ...current, fiche_de_poste_id: event.target.value }))}>{fiches.map((fiche) => <option key={fiche.id} value={fiche.id}>{fiche.title}</option>)}</Select></Field>
          <Field label="Description"><Textarea disabled={!editable} value={form.description} onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))} /></Field>
          <Field label="Justification"><Textarea disabled={!editable} value={form.justification} onChange={(event) => setForm((current) => ({ ...current, justification: event.target.value }))} /></Field>
          <Field label="Nombre de postes"><Input disabled={!editable} type="number" min="1" value={form.positions_count} onChange={(event) => setForm((current) => ({ ...current, positions_count: event.target.value }))} /></Field>
          <Field label="Date souhaitée"><Input disabled={!editable} type="date" value={form.desired_date} onChange={(event) => setForm((current) => ({ ...current, desired_date: event.target.value }))} /></Field>
          <div className="md:col-span-2 flex flex-wrap gap-2">
            {editable && <Button type="submit">Sauvegarder</Button>}
            {canSubmit && <Button type="button" onClick={async () => { await apiClient.post(`/besoins/${id}/soumettre`); window.location.reload() }}>Soumettre</Button>}
            {canApprove && <Button type="button" onClick={async () => { await apiClient.post(`/besoins/${id}/approuver`); window.location.reload() }}>Approuver</Button>}
            {canReject && <Button type="button" variant="destructive" onClick={async () => { const reason = prompt("Motif du rejet ?") ?? ""; await apiClient.post(`/besoins/${id}/rejeter`, { reason }); window.location.reload() }}>Rejeter</Button>}
            {canDelete && <Button type="button" variant="secondary" onClick={async () => { await apiClient.delete(`/besoins/${id}`); window.location.href = "/besoins" }}>Supprimer</Button>}
          </div>
        </form>
      </CardContent>
    </Card>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <div className="space-y-2"><Label>{label}</Label>{children}</div>
}
