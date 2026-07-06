"use client"

import { use, useEffect, useState } from "react"

import { RoleGate } from "@/components/role-gate"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { ApiHttpError, apiClient } from "@/lib/http"
import type { ApiResponse, FicheDePosteResponse } from "@/lib/backend-types"
import { badgeVariantFromFicheStatus } from "@/lib/status-labels"
import { Badge } from "@/components/ui/badge"
import { useAuth } from "@/components/auth-provider"

export default function FicheDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params)
  const ficheId = Number(resolvedParams.id)

  if (Number.isNaN(ficheId)) {
    return (
      <RoleGate roles={["ADMIN", "DRH", "DIRECTEUR", "DG"]}>
        <Card>
          <CardContent>Identifiant fiche invalide.</CardContent>
        </Card>
      </RoleGate>
    )
  }

  return (
    <RoleGate roles={["ADMIN", "DRH", "DIRECTEUR", "DG"]}>
      <FicheDetail id={ficheId} />
    </RoleGate>
  )
}

function FicheDetail({ id }: { id: number }) {
  const { user } = useAuth()
  const [item, setItem] = useState<FicheDePosteResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [form, setForm] = useState({ title: "", description: "", missions: "", required_skills: "", experience_level: "Bac+5", direction_id: "" })

  useEffect(() => {
    let cancelled = false

    const load = async () => {
      setIsLoading(true)
      setError(null)
      try {
        const response = await apiClient.get<ApiResponse<FicheDePosteResponse>>(`/fiches-de-poste/${id}`)
        if (cancelled) {
          return
        }

        setItem(response.data.data)
        setForm({
          title: response.data.data.title,
          description: response.data.data.description,
          missions: response.data.data.missions,
          required_skills: response.data.data.required_skills,
          experience_level: response.data.data.experience_level,
          direction_id: response.data.data.direction_id.toString(),
        })
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiHttpError ? err.message : "Impossible de charger cette fiche.")
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
    const response = await apiClient.put<ApiResponse<FicheDePosteResponse>>(`/fiches-de-poste/${id}`, {
      ...form,
      direction_id: Number(form.direction_id),
    })
    setItem(response.data.data)
  }

  if (isLoading) return <Card><CardContent>Chargement…</CardContent></Card>
  if (error) return <Card><CardContent>{error}</CardContent></Card>
  if (!item) return <Card><CardContent>Fiche introuvable.</CardContent></Card>

  const editable = user?.id === item.created_by_id && item.status === "DRAFT"
  const canValidate = user?.role === "DRH" && item.status === "DRAFT"
  const canArchive = user?.role === "DRH" && item.status === "VALIDATED"

  return (
    <Card>
      <CardHeader><CardTitle>{item.title} <Badge variant={badgeVariantFromFicheStatus(item.status)}>{item.status}</Badge></CardTitle></CardHeader>
      <CardContent>
        <form className="grid gap-4 md:grid-cols-2" onSubmit={save}>
          <Field label="Intitulé"><Input disabled={!editable} value={form.title} onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))} /></Field>
          <Field label="Direction ID"><Input disabled={!editable} value={form.direction_id} onChange={(event) => setForm((current) => ({ ...current, direction_id: event.target.value }))} /></Field>
          <Field label="Description"><Textarea disabled={!editable} value={form.description} onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))} /></Field>
          <Field label="Missions"><Textarea disabled={!editable} value={form.missions} onChange={(event) => setForm((current) => ({ ...current, missions: event.target.value }))} /></Field>
          <Field label="Compétences requises"><Textarea disabled={!editable} value={form.required_skills} onChange={(event) => setForm((current) => ({ ...current, required_skills: event.target.value }))} /></Field>
          <Field label="Niveau"><Select disabled={!editable} value={form.experience_level} onChange={(event) => setForm((current) => ({ ...current, experience_level: event.target.value }))}><option>Bac</option><option>Bac+2</option><option>Bac+3</option><option>Bac+5</option><option>Doctorat</option></Select></Field>
          <div className="md:col-span-2 flex gap-2">
            {editable && <Button type="submit">Sauvegarder</Button>}
            {canValidate && <Button type="button" onClick={async () => { await apiClient.patch(`/fiches-de-poste/${id}/valider`); window.location.reload() }}>Valider</Button>}
            {canArchive && <Button type="button" variant="secondary" onClick={async () => { await apiClient.patch(`/fiches-de-poste/${id}/archiver`); window.location.reload() }}>Archiver</Button>}
          </div>
        </form>
      </CardContent>
    </Card>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <div className="space-y-2"><Label>{label}</Label>{children}</div>
}
