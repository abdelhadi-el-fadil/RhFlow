"use client"

import { useEffect, useState } from "react"

import { RoleGate } from "@/components/role-gate"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Textarea } from "@/components/ui/textarea"
import { apiClient } from "@/lib/http"
import type { DirectionResponse, FicheDePosteResponse, PaginatedResponse } from "@/lib/backend-types"
import { badgeVariantFromFicheStatus } from "@/lib/status-labels"
import { useAuth } from "@/components/auth-provider"

const EXPERIENCE_LEVELS = ["Bac", "Bac+2", "Bac+3", "Bac+5", "Doctorat"]

export default function FichesPage() {
  return (
    <RoleGate roles={["ADMIN", "DRH", "DIRECTEUR", "DG"]}>
      <FichesContent />
    </RoleGate>
  )
}

function FichesContent() {
  const { user } = useAuth()
  const [items, setItems] = useState<FicheDePosteResponse[]>([])
  const [directions, setDirections] = useState<DirectionResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [form, setForm] = useState({ title: "", description: "", missions: "", required_skills: "", experience_level: "Bac+5", direction_id: "" })

  const load = async () => {
    const [fichesRes, directionsRes] = await Promise.all([
      apiClient.get<PaginatedResponse<FicheDePosteResponse>>("/fiches-de-poste/", { params: { page: 1, page_size: 50 } }),
      apiClient.get<PaginatedResponse<DirectionResponse>>("/directions/", { params: { page: 1, page_size: 100 } }),
    ])
    setItems(fichesRes.data.data)
    setDirections(directionsRes.data.data)
  }

  useEffect(() => {
    const run = async () => {
      try {
        await load()
      } finally {
        setLoading(false)
      }
    }

    // eslint-disable-next-line react-hooks/set-state-in-effect
    void run()
  }, [])

  const createFiche = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    await apiClient.post("/fiches-de-poste/", {
      ...form,
      direction_id: Number(form.direction_id),
    })
    setForm({ title: "", description: "", missions: "", required_skills: "", experience_level: "Bac+5", direction_id: "" })
    await load()
  }

  const validateFiche = async (id: number) => {
    await apiClient.patch(`/fiches-de-poste/${id}/valider`)
    await load()
  }

  const archiveFiche = async (id: number) => {
    await apiClient.patch(`/fiches-de-poste/${id}/archiver`)
    await load()
  }

  return (
    <div className="space-y-6">
      {(user?.role === "DIRECTEUR" || user?.role === "DRH") && (
        <Card>
          <CardHeader><CardDescription>Créer</CardDescription><CardTitle>Fiche de poste</CardTitle></CardHeader>
          <CardContent>
            <form className="grid gap-4 md:grid-cols-2" onSubmit={createFiche}>
              <Field label="Intitulé"><Input value={form.title} onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))} /></Field>
              <Field label="Direction"><Select value={form.direction_id} onChange={(event) => setForm((current) => ({ ...current, direction_id: event.target.value }))}><option value="">Choisir</option>{directions.map((direction) => <option key={direction.id} value={direction.id}>{direction.name}</option>)}</Select></Field>
              <Field label="Description"><Textarea value={form.description} onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))} /></Field>
              <Field label="Missions"><Textarea value={form.missions} onChange={(event) => setForm((current) => ({ ...current, missions: event.target.value }))} /></Field>
              <Field label="Compétences requises"><Textarea value={form.required_skills} onChange={(event) => setForm((current) => ({ ...current, required_skills: event.target.value }))} /></Field>
              <Field label="Niveau d'études"><Select value={form.experience_level} onChange={(event) => setForm((current) => ({ ...current, experience_level: event.target.value }))}>{EXPERIENCE_LEVELS.map((level) => <option key={level} value={level}>{level}</option>)}</Select></Field>
              <div className="md:col-span-2"><Button type="submit">Créer</Button></div>
            </form>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader><CardDescription>{loading ? "Chargement…" : `${items.length} fiches`}</CardDescription><CardTitle>Liste</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Titre</TableHead>
                <TableHead>Direction</TableHead>
                <TableHead>Niveau</TableHead>
                <TableHead>Statut</TableHead>
                <TableHead />
              </TableRow>
            </TableHeader>
            <TableBody>
              {items.map((item) => (
                <TableRow key={item.id}>
                  <TableCell>{item.title}</TableCell>
                  <TableCell>{item.direction_id}</TableCell>
                  <TableCell>{item.experience_level}</TableCell>
                  <TableCell><Badge variant={badgeVariantFromFicheStatus(item.status)}>{item.status}</Badge></TableCell>
                  <TableCell className="text-right">
                    <Button asChild variant="outline" size="sm"><a href={`/fiches-de-poste/${item.id}`}>Ouvrir</a></Button>
                    {user?.role === "DRH" && item.status === "DRAFT" && (
                      <>
                        <Button size="sm" className="ml-2" onClick={() => validateFiche(item.id)}>Valider</Button>
                      </>
                    )}
                    {user?.role === "DRH" && item.status === "VALIDATED" && (
                      <Button variant="secondary" size="sm" className="ml-2" onClick={() => archiveFiche(item.id)}>Archiver</Button>
                    )}
                  </TableCell>
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
