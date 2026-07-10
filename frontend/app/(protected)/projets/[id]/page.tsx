"use client"

import { use, useCallback, useEffect, useState } from "react"
import { useRouter } from "next/navigation"

import { useAuth } from "@/components/auth-provider"
import { RoleGate } from "@/components/role-gate"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Textarea } from "@/components/ui/textarea"
import { ApiHttpError, apiClient } from "@/lib/http"
import type { ApiResponse, BesoinRecrutementResponse, FicheDePosteResponse, PaginatedResponse, ProjetRecrutementResponse, UserResponse } from "@/lib/backend-types"
import { badgeVariantFromProjetStatus } from "@/lib/status-labels"
import { setFlashSuccess } from "@/lib/flash"

export default function ProjetDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params)
  const projectId = Number(resolvedParams.id)

  if (Number.isNaN(projectId)) {
    return (
      <RoleGate roles={["ADMIN", "DRH", "DIRECTEUR", "DG"]}>
        <Card>
          <CardContent>Identifiant projet invalide.</CardContent>
        </Card>
      </RoleGate>
    )
  }

  return (
    <RoleGate roles={["ADMIN", "DRH", "DIRECTEUR", "DG"]}>
      <DetailContent id={projectId} />
    </RoleGate>
  )
}

function DetailContent({ id }: { id: number }) {
  const router = useRouter()
  const { user } = useAuth()
  const [item, setItem] = useState<ProjetRecrutementResponse | null>(null)
  const [approvedNeeds, setApprovedNeeds] = useState<BesoinRecrutementResponse[]>([])
  const [fiches, setFiches] = useState<FicheDePosteResponse[]>([])
  const [managers, setManagers] = useState<UserResponse[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [attachNeedId, setAttachNeedId] = useState("")
  const [form, setForm] = useState({ title: "", description: "", start_date: "", expected_end_date: "", status: "DRAFT", manager_id: "", besoin_recrutement_id: "", fiche_de_poste_id: "", nombre_postes: "" })

  const canManage = user?.role === "ADMIN" || user?.role === "DRH" || user?.role === "DIRECTEUR" || user?.role === "DG"

  const reload = useCallback(async () => {
    const [projectRes, needsRes, fichesRes, usersRes] = await Promise.all([
      apiClient.get<ApiResponse<ProjetRecrutementResponse>>(`/projets/${id}`),
      apiClient.get<PaginatedResponse<BesoinRecrutementResponse>>("/besoins/", { params: { page: 1, page_size: 100 } }),
      apiClient.get<PaginatedResponse<FicheDePosteResponse>>("/fiches-de-poste/", { params: { page: 1, page_size: 100 } }),
      canManage ? apiClient.get<PaginatedResponse<UserResponse>>("/users/", { params: { page: 1, page_size: 100 } }) : Promise.resolve({ data: { data: [] as UserResponse[] } }),
    ])

    setItem(projectRes.data.data)
    setApprovedNeeds(needsRes.data.data.filter((need) => need.status === "APPROVED" || need.projet_id === id))
    setFiches(fichesRes.data.data)
    setManagers(usersRes.data.data)
    setForm({
      title: projectRes.data.data.title,
      description: projectRes.data.data.description ?? "",
      start_date: projectRes.data.data.start_date,
      expected_end_date: projectRes.data.data.expected_end_date,
      status: projectRes.data.data.status,
      manager_id: String(projectRes.data.data.manager_id),
      besoin_recrutement_id: projectRes.data.data.besoin_recrutement_id?.toString() ?? "",
      fiche_de_poste_id: projectRes.data.data.fiche_de_poste_id?.toString() ?? "",
      nombre_postes: projectRes.data.data.nombre_postes?.toString() ?? "",
    })
  }, [canManage, id])

  useEffect(() => {
    let cancelled = false

    const load = async () => {
      setIsLoading(true)
      setError(null)
      try {
        await reload()
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiHttpError ? err.message : "Impossible de charger ce projet.")
          setItem(null)
          setApprovedNeeds([])
          setFiches([])
          setManagers([])
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
  }, [reload])

  if (isLoading) return <Card><CardContent>Chargement…</CardContent></Card>
  if (error) return <Card><CardContent>{error}</CardContent></Card>
  if (!item) return <Card><CardContent>Projet introuvable.</CardContent></Card>

  const save = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setActionError(null)
    try {
      await apiClient.put(`/projets/${id}`, {
        title: form.title,
        description: form.description || null,
        start_date: form.start_date,
        expected_end_date: form.expected_end_date,
        status: form.status,
        manager_id: Number(form.manager_id),
        besoin_recrutement_id: form.besoin_recrutement_id ? Number(form.besoin_recrutement_id) : null,
        fiche_de_poste_id: form.fiche_de_poste_id ? Number(form.fiche_de_poste_id) : null,
        nombre_postes: form.nombre_postes ? Number(form.nombre_postes) : null,
      })
      setFlashSuccess("Projet sauvegardé avec succès.")
      router.push("/projets")
    } catch (err) {
      setActionError(err instanceof ApiHttpError ? err.message : "Impossible de sauvegarder ce projet.")
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader><CardTitle>{item.title} <Badge variant={badgeVariantFromProjetStatus(item.status)}>{item.status}</Badge></CardTitle></CardHeader>
        <CardContent>
          {actionError && <p className="mb-4 text-sm text-destructive">{actionError}</p>}
          <form className="grid gap-4 md:grid-cols-2" onSubmit={save}>
            <Field label="Titre"><Input disabled={!canManage} value={form.title} onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))} /></Field>
            <Field label="Manager"><Select disabled={!canManage} value={form.manager_id} onChange={(event) => setForm((current) => ({ ...current, manager_id: event.target.value }))}><option value="">Choisir</option>{managers.map((manager) => <option key={manager.id} value={manager.id}>{manager.full_name || manager.email}</option>)}</Select></Field>
            <Field label="Date de début"><Input disabled={!canManage} type="date" value={form.start_date} onChange={(event) => setForm((current) => ({ ...current, start_date: event.target.value }))} /></Field>
            <Field label="Date de fin prévue"><Input disabled={!canManage} type="date" value={form.expected_end_date} onChange={(event) => setForm((current) => ({ ...current, expected_end_date: event.target.value }))} /></Field>
            <Field label="Statut"><Select disabled={!canManage} value={form.status} onChange={(event) => setForm((current) => ({ ...current, status: event.target.value }))}><option value="DRAFT">Brouillon</option><option value="ACTIVE">Actif</option><option value="CLOSED">Clôturé</option></Select></Field>
            <Field label="Besoin principal"><Select disabled={!canManage} value={form.besoin_recrutement_id} onChange={(event) => { const selectedNeed = approvedNeeds.find((need) => String(need.id) === event.target.value); setForm((current) => ({ ...current, besoin_recrutement_id: event.target.value, fiche_de_poste_id: selectedNeed ? String(selectedNeed.fiche_de_poste_id) : current.fiche_de_poste_id, nombre_postes: selectedNeed?.positions_count ? String(selectedNeed.positions_count) : current.nombre_postes })) }}><option value="">Aucun</option>{approvedNeeds.map((need) => <option key={need.id} value={need.id}>{need.title}</option>)}</Select></Field>
            <Field label="Fiche de poste"><Select disabled={!canManage} value={form.fiche_de_poste_id} onChange={(event) => setForm((current) => ({ ...current, fiche_de_poste_id: event.target.value }))}><option value="">Choisir</option>{fiches.map((fiche) => <option key={fiche.id} value={fiche.id}>{fiche.title}</option>)}</Select></Field>
            <Field label="Nombre de postes"><Input disabled={!canManage} type="number" min="1" value={form.nombre_postes} onChange={(event) => setForm((current) => ({ ...current, nombre_postes: event.target.value }))} /></Field>
            <div className="md:col-span-2"><Field label="Description"><Textarea disabled={!canManage} value={form.description} onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))} /></Field></div>
            <div className="md:col-span-2 flex flex-wrap gap-2">
              {canManage && <Button type="submit">Sauvegarder</Button>}
              {canManage && item.status !== "CLOSED" && <Button type="button" variant="secondary" onClick={async () => {
                setActionError(null)
                try {
                  await apiClient.patch(`/projets/${id}/cloturer`)
                  await reload()
                } catch (err) {
                  setActionError(err instanceof ApiHttpError ? err.message : "Impossible de clôturer ce projet.")
                }
              }}>Clôturer</Button>}
              {canManage && <Button type="button" variant="destructive" onClick={async () => {
                setActionError(null)
                try {
                  await apiClient.delete(`/projets/${id}`)
                  window.location.href = "/projets"
                } catch (err) {
                  setActionError(err instanceof ApiHttpError ? err.message : "Impossible de supprimer ce projet.")
                }
              }}>Supprimer</Button>}
            </div>
          </form>
        </CardContent>
      </Card>

      {canManage && (
        <Card>
          <CardHeader><CardTitle>Rattacher un besoin approuvé</CardTitle></CardHeader>
          <CardContent>
            <form className="flex gap-3" onSubmit={async (event) => {
              event.preventDefault()
              const parsedNeedId = Number(attachNeedId)
              if (Number.isNaN(parsedNeedId)) {
                return
              }

              setActionError(null)
              try {
                await apiClient.post(`/projets/${id}/besoins/${parsedNeedId}`)
                await reload()
              } catch (err) {
                setActionError(err instanceof ApiHttpError ? err.message : "Impossible d'attacher ce besoin.")
              }
            }}>
              <div className="flex-1 space-y-2">
                <Label>Besoin approuvé</Label>
                <Select value={attachNeedId} onChange={(event) => setAttachNeedId(event.target.value)}>
                  <option value="">Choisir</option>
                  {approvedNeeds.map((need) => <option key={need.id} value={need.id}>{need.title}</option>)}
                </Select>
              </div>
              <div className="self-end"><Button type="submit" disabled={!attachNeedId}>Attacher</Button></div>
            </form>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader><CardTitle>Besoins liés</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow><TableHead>Titre</TableHead><TableHead>Statut</TableHead><TableHead>Fiche</TableHead><TableHead /></TableRow>
            </TableHeader>
            <TableBody>
              {item.besoins.map((need) => (
                <TableRow key={need.id}>
                  <TableCell>{need.title}</TableCell>
                  <TableCell><Badge variant="outline">{need.status}</Badge></TableCell>
                  <TableCell>{need.fiche_title ?? `Fiche #${need.fiche_de_poste_id}`}</TableCell>
                  <TableCell className="text-right"><Button asChild variant="outline" size="sm"><a href={`/besoins/${need.id}`}>Ouvrir</a></Button></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <div className="space-y-2"><Label>{label}</Label>{children}</div>
}
