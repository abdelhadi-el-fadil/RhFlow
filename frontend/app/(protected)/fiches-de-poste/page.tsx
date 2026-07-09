"use client"

import { useEffect, useState } from "react"
import { FileText, ListPlus } from "lucide-react"

import { RoleGate } from "@/components/role-gate"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { ApiHttpError, apiClient } from "@/lib/http"
import type { DirectionResponse, FicheDePosteResponse, PaginatedResponse } from "@/lib/backend-types"
import { badgeVariantFromFicheStatus } from "@/lib/status-labels"
import { useAuth } from "@/components/auth-provider"

const EXPERIENCE_LEVELS = ["Junior", "Confirmé", "Senior", "Expert"]
const EDUCATION_LEVELS = ["Bac", "Bac+2", "Bac+3", "Bac+5", "Doctorat"]

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
  const [error, setError] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [form, setForm] = useState({ title: "", description: "", missions: "", required_skills: "", experience_level: "Confirmé", direction_id: "", formation_domain: "", education_level: "", technical_skills: "", managerial_skills: "" })
  const [search, setSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState<"ALL" | "DRAFT" | "VALIDATED" | "ARCHIVED">("ALL")
  const [directionFilter, setDirectionFilter] = useState("ALL")

  const canCreateFiche = user?.role === "ADMIN" || user?.role === "DRH" || user?.role === "DIRECTEUR"
  const canValidateOrArchive = user?.role === "ADMIN" || user?.role === "DRH"
  const availableDirections = user?.role === "DIRECTEUR"
    ? directions.filter((direction) => direction.director_id === user.id)
    : directions

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
        setError(null)
        await load()
      } catch (err) {
        setError(err instanceof ApiHttpError ? err.message : "Impossible de charger les fiches de poste.")
      } finally {
        setLoading(false)
      }
    }

    void run()
  }, [])

  const createFiche = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setActionError(null)
    try {
      await apiClient.post("/fiches-de-poste/", {
        ...form,
        direction_id: Number(form.direction_id),
      })
      setForm({ title: "", description: "", missions: "", required_skills: "", experience_level: "Confirmé", direction_id: "", formation_domain: "", education_level: "", technical_skills: "", managerial_skills: "" })
      await load()
    } catch (err) {
      setActionError(err instanceof ApiHttpError ? err.message : "Impossible de créer la fiche de poste.")
    }
  }

  const validateFiche = async (id: number) => {
    setActionError(null)
    try {
      await apiClient.patch(`/fiches-de-poste/${id}/valider`)
      await load()
    } catch (err) {
      setActionError(err instanceof ApiHttpError ? err.message : "Impossible de valider la fiche.")
    }
  }

  const archiveFiche = async (id: number) => {
    setActionError(null)
    try {
      await apiClient.patch(`/fiches-de-poste/${id}/archiver`)
      await load()
    } catch (err) {
      setActionError(err instanceof ApiHttpError ? err.message : "Impossible d'archiver la fiche.")
    }
  }

  const deleteFiche = async (id: number) => {
    if (!confirm("Supprimer cette fiche de poste ?")) {
      return
    }
    setActionError(null)
    try {
      await apiClient.delete(`/fiches-de-poste/${id}`)
      await load()
    } catch (err) {
      setActionError(err instanceof ApiHttpError ? err.message : "Impossible de supprimer la fiche.")
    }
  }

  const filteredItems = items.filter((item) => {
    const haystack = `${item.title} ${item.description} ${item.direction_name ?? ""} ${item.experience_level} ${item.education_level ?? ""} ${item.technical_skills ?? ""} ${item.managerial_skills ?? ""}`.toLowerCase()
    const matchesSearch = search.trim() === "" || haystack.includes(search.trim().toLowerCase())
    const matchesStatus = statusFilter === "ALL" || item.status === statusFilter
    const matchesDirection = directionFilter === "ALL" || String(item.direction_id) === directionFilter
    return matchesSearch && matchesStatus && matchesDirection
  })

  return (
    <div className="space-y-6">
      {canCreateFiche && (
        <Card className="border-sky-300/70 bg-linear-to-br from-sky-200 via-blue-200 to-cyan-100">
          <CardHeader>
            <CardDescription className="text-sky-800">Créer</CardDescription>
            <CardTitle className="flex items-center gap-2 text-sky-950">
              <ListPlus className="size-5 text-sky-800" />
              Fiche de poste
            </CardTitle>
          </CardHeader>
          <CardContent>
            {actionError && <p className="mb-4 text-sm text-destructive">{actionError}</p>}
            <form className="grid gap-4 md:grid-cols-2" onSubmit={createFiche}>
              <Field label="Intitulé"><Input value={form.title} onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))} /></Field>
              <Field label="Direction"><Select value={form.direction_id} onChange={(event) => setForm((current) => ({ ...current, direction_id: event.target.value }))}><option value="">Choisir</option>{availableDirections.map((direction) => <option key={direction.id} value={direction.id}>{direction.name}</option>)}</Select></Field>
              <Field label="Description"><Textarea value={form.description} onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))} /></Field>
              <Field label="Missions"><Textarea value={form.missions} onChange={(event) => setForm((current) => ({ ...current, missions: event.target.value }))} /></Field>
              <Field label="Compétences requises"><Textarea value={form.required_skills} onChange={(event) => setForm((current) => ({ ...current, required_skills: event.target.value }))} /></Field>
              <Field label="Niveau d'expérience"><Select value={form.experience_level} onChange={(event) => setForm((current) => ({ ...current, experience_level: event.target.value }))}>{EXPERIENCE_LEVELS.map((level) => <option key={level} value={level}>{level}</option>)}</Select></Field>
              <Field label="Domaine de formation"><Input value={form.formation_domain} onChange={(event) => setForm((current) => ({ ...current, formation_domain: event.target.value }))} /></Field>
              <Field label="Niveau d'études"><Select value={form.education_level} onChange={(event) => setForm((current) => ({ ...current, education_level: event.target.value }))}><option value="">Choisir</option>{EDUCATION_LEVELS.map((level) => <option key={level} value={level}>{level}</option>)}</Select></Field>
              <Field label="Compétences techniques"><Textarea value={form.technical_skills} onChange={(event) => setForm((current) => ({ ...current, technical_skills: event.target.value }))} /></Field>
              <Field label="Compétences managériales"><Textarea value={form.managerial_skills} onChange={(event) => setForm((current) => ({ ...current, managerial_skills: event.target.value }))} /></Field>
              <div className="md:col-span-2"><Button type="submit">Créer</Button></div>
            </form>
          </CardContent>
        </Card>
      )}

      <Card className="border-sky-300/70 bg-linear-to-br from-sky-200 via-blue-200 to-cyan-100">
        <CardHeader>
          <CardDescription className="text-sky-800">{loading ? "Chargement…" : `${filteredItems.length} fiches`}</CardDescription>
          <CardTitle className="flex items-center gap-2 text-sky-950">
            <FileText className="size-5 text-sky-800" />
            Fiches de poste
          </CardTitle>
        </CardHeader>
        <CardContent>
          {error && <p className="mb-4 text-sm text-destructive">{error}</p>}
          <div className="mb-4 grid gap-4 md:grid-cols-3">
            <Field label="Recherche"><Input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Titre, direction, compétences" /></Field>
            <Field label="Statut"><Select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value as "ALL" | "DRAFT" | "VALIDATED" | "ARCHIVED")}><option value="ALL">Tous</option><option value="DRAFT">Brouillon</option><option value="VALIDATED">Validée</option><option value="ARCHIVED">Archivée</option></Select></Field>
            <Field label="Direction"><Select value={directionFilter} onChange={(event) => setDirectionFilter(event.target.value)}><option value="ALL">Toutes</option>{directions.map((direction) => <option key={direction.id} value={direction.id}>{direction.name}</option>)}</Select></Field>
          </div>
          <div className="grid gap-4 xl:grid-cols-2">
            {filteredItems.map((item) => (
              <Card key={item.id} className="border-sky-200 bg-white/80">
                <CardHeader>
                  <CardDescription className="text-sky-800">{item.direction_name ?? `Direction #${item.direction_id}`}</CardDescription>
                  <CardTitle className="text-sky-950">{item.title}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid gap-3 md:grid-cols-2">
                    <Info label="Niveau d'expérience" value={item.experience_level} />
                    <Info label="Niveau d'études" value={item.education_level ?? "-"} />
                    <Info label="Domaine de formation" value={item.formation_domain ?? "-"} />
                    <Info label="Compétences requises" value={item.required_skills} />
                  </div>
                  <Info label="Description" value={item.description} />
                  <Info label="Missions" value={item.missions} />
                  <div className="grid gap-3 md:grid-cols-2">
                    <Info label="Compétences techniques" value={item.technical_skills ?? "-"} />
                    <Info label="Compétences managériales" value={item.managerial_skills ?? "-"} />
                  </div>
                  <div className="flex flex-wrap items-center justify-between gap-3 border-t border-sky-100 pt-4">
                    <Badge variant={badgeVariantFromFicheStatus(item.status)}>{item.status}</Badge>
                    <div className="flex gap-2">
                      <Button asChild variant="outline" size="sm"><a href={`/fiches-de-poste/${item.id}`}>Ouvrir</a></Button>
                      {canValidateOrArchive && item.status === "DRAFT" && <Button size="sm" onClick={() => validateFiche(item.id)}>Valider</Button>}
                      {canValidateOrArchive && item.status === "VALIDATED" && <Button variant="secondary" size="sm" onClick={() => archiveFiche(item.id)}>Archiver</Button>}
                      {canCreateFiche && <Button variant="destructive" size="sm" onClick={() => deleteFiche(item.id)}>Supprimer</Button>}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
          {filteredItems.length === 0 && <p className="text-sm text-sky-900/70">Aucune fiche ne correspond aux filtres.</p>}
        </CardContent>
      </Card>
    </div>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <div className="space-y-2"><Label>{label}</Label>{children}</div>
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="space-y-1 rounded-lg border border-sky-100 bg-sky-50/60 p-3">
      <p className="text-xs font-medium uppercase tracking-wide text-sky-700">{label}</p>
      <p className="whitespace-pre-line text-sm text-sky-950">{value}</p>
    </div>
  )
}