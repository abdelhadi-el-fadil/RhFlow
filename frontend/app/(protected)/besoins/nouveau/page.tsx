"use client"

import { useEffect, useState } from "react"

import { RoleGate } from "@/components/role-gate"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { apiClient } from "@/lib/http"
import type { FicheDePosteResponse, PaginatedResponse } from "@/lib/backend-types"

export default function BesoinCreatePage() {
  return (
    <RoleGate roles={["DIRECTEUR"]}>
      <CreateContent />
    </RoleGate>
  )
}

function CreateContent() {
  const [fiches, setFiches] = useState<FicheDePosteResponse[]>([])
  const [form, setForm] = useState({ title: "", description: "", positions_count: "1", desired_date: "", justification: "", fiche_de_poste_id: "" })

  useEffect(() => {
    void apiClient.get<PaginatedResponse<FicheDePosteResponse>>("/fiches-de-poste/", { params: { page: 1, page_size: 100 } }).then((response) => setFiches(response.data.data))
  }, [])

  const save = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    await apiClient.post("/besoins/", {
      title: form.title,
      description: form.description || null,
      positions_count: Number(form.positions_count),
      desired_date: form.desired_date || null,
      justification: form.justification || null,
      fiche_de_poste_id: Number(form.fiche_de_poste_id),
    })
    window.location.href = "/besoins"
  }

  return (
    <Card>
      <CardHeader><CardTitle>Nouveau besoin</CardTitle></CardHeader>
      <CardContent>
        <form className="grid gap-4 md:grid-cols-2" onSubmit={save}>
          <Field label="Titre"><Input value={form.title} onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))} /></Field>
          <Field label="Fiche de poste"><Select value={form.fiche_de_poste_id} onChange={(event) => setForm((current) => ({ ...current, fiche_de_poste_id: event.target.value }))}><option value="">Choisir</option>{fiches.map((fiche) => <option key={fiche.id} value={fiche.id}>{fiche.title}</option>)}</Select></Field>
          <Field label="Description"><Textarea value={form.description} onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))} /></Field>
          <Field label="Justification"><Textarea value={form.justification} onChange={(event) => setForm((current) => ({ ...current, justification: event.target.value }))} /></Field>
          <Field label="Nombre de postes"><Input type="number" min="1" value={form.positions_count} onChange={(event) => setForm((current) => ({ ...current, positions_count: event.target.value }))} /></Field>
          <Field label="Date souhaitée"><Input type="date" value={form.desired_date} onChange={(event) => setForm((current) => ({ ...current, desired_date: event.target.value }))} /></Field>
          <div className="md:col-span-2"><Button type="submit">Créer</Button></div>
        </form>
      </CardContent>
    </Card>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <div className="space-y-2"><Label>{label}</Label>{children}</div>
}
