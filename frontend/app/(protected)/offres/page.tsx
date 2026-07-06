"use client"

import { useEffect, useState } from "react"

import { RoleGate } from "@/components/role-gate"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Textarea } from "@/components/ui/textarea"
import { apiClient } from "@/lib/http"
import type { OffrePublicResponse, PaginatedResponse } from "@/lib/backend-types"
import { useAuth } from "@/components/auth-provider"

export default function OffresPage() {
  return (
    <RoleGate roles={["ADMIN", "DRH", "DIRECTEUR", "DG"]}>
      <Content />
    </RoleGate>
  )
}

function Content() {
  const { user } = useAuth()
  const [items, setItems] = useState<OffrePublicResponse[]>([])
  const [form, setForm] = useState({ title: "", description: "", requirements: "", deadline: "", besoin_id: "" })
  const [actionId, setActionId] = useState("")

  const load = async () => {
    const response = await apiClient.get<PaginatedResponse<OffrePublicResponse>>("/offres/", { params: { page: 1, page_size: 50 } })
    setItems(response.data.data)
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load()
  }, [])

  const create = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    await apiClient.post("/offres/", {
      title: form.title,
      description: form.description || null,
      requirements: form.requirements || null,
      deadline: form.deadline || null,
      besoin_id: Number(form.besoin_id),
    })
    setForm({ title: "", description: "", requirements: "", deadline: "", besoin_id: "" })
    await load()
  }

  const publish = async () => {
    await apiClient.patch(`/offres/${actionId}/publier`)
    await load()
  }

  const close = async () => {
    await apiClient.patch(`/offres/${actionId}/cloturer`)
    await load()
  }

  return (
    <div className="space-y-6">
      {user?.role === "DRH" && (
        <Card>
          <CardHeader><CardTitle>Créer une offre</CardTitle></CardHeader>
          <CardContent>
            <form className="grid gap-4 md:grid-cols-2" onSubmit={create}>
              <Field label="Besoin ID"><Input value={form.besoin_id} onChange={(event) => setForm((current) => ({ ...current, besoin_id: event.target.value }))} /></Field>
              <Field label="Deadline"><Input type="date" value={form.deadline} onChange={(event) => setForm((current) => ({ ...current, deadline: event.target.value }))} /></Field>
              <Field label="Titre"><Input value={form.title} onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))} /></Field>
              <Field label="Description"><Textarea value={form.description} onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))} /></Field>
              <Field label="Requirements"><Textarea value={form.requirements} onChange={(event) => setForm((current) => ({ ...current, requirements: event.target.value }))} /></Field>
              <div className="md:col-span-2"><Button type="submit">Créer</Button></div>
            </form>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader><CardTitle>Actions par ID</CardTitle></CardHeader>
        <CardContent className="flex flex-wrap gap-3">
          <div className="space-y-2">
            <Label>Offre ID</Label>
            <Input value={actionId} onChange={(event) => setActionId(event.target.value)} />
          </div>
          {user?.role === "DRH" && (
            <div className="flex items-end gap-2">
              <Button onClick={publish}>Publier</Button>
              <Button variant="secondary" onClick={close}>Clôturer</Button>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Offres publiées</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow><TableHead>Titre</TableHead><TableHead>Deadline</TableHead><TableHead /></TableRow>
            </TableHeader>
            <TableBody>
              {items.map((item) => (
                <TableRow key={`${item.title}-${item.published_at}`}>
                  <TableCell>{item.title}</TableCell>
                  <TableCell>{item.deadline ?? "-"}</TableCell>
                  <TableCell><Badge variant="default">Publié</Badge></TableCell>
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
