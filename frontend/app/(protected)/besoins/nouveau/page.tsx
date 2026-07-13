"use client"

import { useEffect, useState } from "react"
import { format } from "date-fns"
import { CalendarIcon } from "lucide-react"
import { toast } from "sonner"

import { RoleGate } from "@/components/role-gate"
import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Select } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { cn } from "@/lib/utils"
import { ApiHttpError, apiClient } from "@/lib/http"
import type { BesoinPriority, DirectionResponse, FicheDePosteResponse, PaginatedResponse } from "@/lib/backend-types"
import { useAuth } from "@/components/auth-provider"

export default function BesoinCreatePage() {
  return (
    <RoleGate roles={["DIRECTEUR", "DRH", "ADMIN"]}>
      <CreateContent />
    </RoleGate>
  )
}

function CreateContent() {
  const { user } = useAuth()
  const [fiches, setFiches] = useState<FicheDePosteResponse[]>([])
  const [directions, setDirections] = useState<DirectionResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [desiredDate, setDesiredDate] = useState<Date | undefined>(undefined)
  const [form, setForm] = useState({
    title: "",
    location: "",
    recruitment_reason: "",
    priority: "NORMALE",
    positions_count: "1",
    fiche_de_poste_id: "",
  })

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const [fichesRes, directionsRes] = await Promise.all([
          apiClient.get<PaginatedResponse<FicheDePosteResponse>>("/fiches-de-poste/", { params: { page: 1, page_size: 100 } }),
          apiClient.get<PaginatedResponse<DirectionResponse>>("/directions/", { params: { page: 1, page_size: 100 } }),
        ])
        setFiches(fichesRes.data.data)
        setDirections(directionsRes.data.data)
      } catch (err) {
        setError(err instanceof ApiHttpError ? err.message : "Impossible de charger les données de création.")
      } finally {
        setLoading(false)
      }
    }

    void load()
  }, [])

  const availableFiches = user?.role === "DIRECTEUR"
    ? fiches.filter((fiche) => directions.find((direction) => direction.id === fiche.direction_id)?.director_id === user.id)
    : fiches

  const save = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const ficheId = Number(form.fiche_de_poste_id)
    if (!Number.isFinite(ficheId) || ficheId <= 0) {
      setError("Veuillez choisir une fiche de poste.")
      return
    }
    if (!form.location.trim()) {
      setError("Le lieu d'affectation est requis.")
      return
    }
    if (!form.recruitment_reason.trim()) {
      setError("Le motif de recrutement est requis.")
      return
    }
    if (Number(form.positions_count) < 1) {
      setError("Le nombre de postes doit être au moins 1.")
      return
    }
    if (!desiredDate) {
      setError("Veuillez choisir une date souhaitée.")
      return
    }

    setError(null)
    try {
      await apiClient.post("/besoins/", {
        title: form.title || null,
        location: form.location,
        recruitment_reason: form.recruitment_reason,
        priority: form.priority as BesoinPriority,
        positions_count: Number(form.positions_count),
        desired_date: format(desiredDate, "yyyy-MM-dd"),
        fiche_de_poste_id: ficheId,
      })
      toast.success("Besoin créé avec succès.")
      window.location.href = "/besoins"
    } catch (err) {
      const message = err instanceof ApiHttpError ? err.message : "Impossible de creer le besoin."
      setError(message)
      toast.error(message)
    }
  }

  return (
    <Card>
      <CardHeader><CardTitle>Nouveau besoin</CardTitle></CardHeader>
      <CardContent>
        {error && <p className="mb-4 text-sm text-destructive">{error}</p>}
        {loading && <p className="mb-4 text-sm text-muted-foreground">Chargement des fiches...</p>}
        <form className="grid gap-4 md:grid-cols-2" onSubmit={save}>
          <Field label="Titre (optionnel)">
            <Input value={form.title} onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))} />
          </Field>
          <Field label="Fiche de poste">
            <Select value={form.fiche_de_poste_id} onChange={(event) => setForm((current) => ({ ...current, fiche_de_poste_id: event.target.value }))}>
              <option value="">Choisir une fiche</option>
              {availableFiches.map((fiche) => <option key={fiche.id} value={fiche.id}>{fiche.title}</option>)}
            </Select>
          </Field>
          <Field label="Lieu d'affectation">
            <Input value={form.location} onChange={(event) => setForm((current) => ({ ...current, location: event.target.value }))} />
          </Field>
          <Field label="Motif de recrutement">
            <Textarea value={form.recruitment_reason} onChange={(event) => setForm((current) => ({ ...current, recruitment_reason: event.target.value }))} />
          </Field>
          <Field label="Priorité">
            <Select value={form.priority} onChange={(event) => setForm((current) => ({ ...current, priority: event.target.value }))}>
              <option value="HAUTE">Haute</option>
              <option value="NORMALE">Normale</option>
              <option value="BASSE">Basse</option>
            </Select>
          </Field>
          <Field label="Nombre de postes">
            <Input type="number" min="1" value={form.positions_count} onChange={(event) => setForm((current) => ({ ...current, positions_count: event.target.value }))} />
          </Field>
          <Field label="Date souhaitée">
            <Popover>
              <PopoverTrigger asChild>
                <Button
                  type="button"
                  variant="outline"
                  className={cn(
                    "w-full justify-start text-left font-normal",
                    !desiredDate && "text-muted-foreground"
                  )}
                >
                  <CalendarIcon className="mr-2 size-4" />
                  {desiredDate ? format(desiredDate, "dd/MM/yyyy") : <span>Choisir une date</span>}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-auto p-0" align="start">
                <Calendar
                  mode="single"
                  selected={desiredDate}
                  onSelect={setDesiredDate}
                  autoFocus
                />
              </PopoverContent>
            </Popover>
          </Field>
          <div className="md:col-span-2"><Button type="submit">Créer</Button></div>
        </form>
      </CardContent>
    </Card>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <div className="space-y-2"><Label>{label}</Label>{children}</div>
}