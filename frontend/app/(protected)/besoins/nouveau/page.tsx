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
import type { BesoinPriority, FicheDePosteResponse, PaginatedResponse } from "@/lib/backend-types"

export default function BesoinCreatePage() {
  return (
    <RoleGate roles={["DIRECTEUR", "DRH", "ADMIN"]}>
      <CreateContent />
    </RoleGate>
  )
}

type BesoinForm = {
  lieu_affectation: string
  recruitment_reason: string
  priority: string
  positions_count: string
  fiche_de_poste_id: string
}

type FieldErrors = Partial<Record<keyof BesoinForm | "desired_date", string>>

const EMPTY_FORM: BesoinForm = {
  lieu_affectation: "",
  recruitment_reason: "",
  priority: "",
  positions_count: "1",
  fiche_de_poste_id: "",
}

function validate(form: BesoinForm, desiredDate: Date | undefined): FieldErrors {
  const errors: FieldErrors = {}

  if (!form.fiche_de_poste_id) {
    errors.fiche_de_poste_id = "Veuillez choisir une fiche de poste."
  }

  if (!form.lieu_affectation.trim()) {
    errors.lieu_affectation = "Le lieu d'affectation est requis."
  }

  if (!form.recruitment_reason.trim()) {
    errors.recruitment_reason = "Le motif de recrutement est requis."
  }

  if (!form.priority) {
    errors.priority = "La priorité est requise."
  }

  if (!form.positions_count.trim()) {
    errors.positions_count = "Le nombre de postes est requis."
  } else if (!Number.isFinite(Number(form.positions_count)) || Number(form.positions_count) < 1) {
    errors.positions_count = "Le nombre de postes doit être au moins 1."
  }

  if (!desiredDate) {
    errors.desired_date = "Veuillez choisir une date souhaitée."
  }

  return errors
}

function CreateContent() {
  const [fiches, setFiches] = useState<FicheDePosteResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [desiredDate, setDesiredDate] = useState<Date | undefined>(undefined)
  const [form, setForm] = useState<BesoinForm>(EMPTY_FORM)
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({})

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const fichesRes = await apiClient.get<PaginatedResponse<FicheDePosteResponse>>("/fiches-de-poste/", { params: { page: 1, page_size: 100 } })
        setFiches(fichesRes.data.data)
      } catch (err) {
        setError(err instanceof ApiHttpError ? err.message : "Impossible de charger les données de création.")
      } finally {
        setLoading(false)
      }
    }

    void load()
  }, [])

  const availableFiches = fiches
  const selectedFiche = availableFiches.find((fiche) => String(fiche.id) === form.fiche_de_poste_id)

  const updateField = <K extends keyof BesoinForm>(key: K, value: BesoinForm[K]) => {
    setForm((current) => ({ ...current, [key]: value }))
    setFieldErrors((current) => {
      if (!current[key]) return current
      const next = { ...current }
      delete next[key]
      return next
    })
  }

  const updateDesiredDate = (date: Date | undefined) => {
    setDesiredDate(date)
    setFieldErrors((current) => {
      if (!current.desired_date) return current
      const next = { ...current }
      delete next.desired_date
      return next
    })
  }

  const save = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError(null)

    const errors = validate(form, desiredDate)
    setFieldErrors(errors)
    if (Object.keys(errors).length > 0) {
      return
    }

    setSaving(true)
    try {
      await apiClient.post("/besoins/", {
        lieu_affectation: form.lieu_affectation,
        recruitment_reason: form.recruitment_reason,
        priority: form.priority as BesoinPriority,
        positions_count: Number(form.positions_count),
        desired_date: format(desiredDate as Date, "yyyy-MM-dd"),
        fiche_de_poste_id: Number(form.fiche_de_poste_id),
      })
      toast.success("Besoin créé avec succès.")
      window.location.href = "/besoins"
    } catch (err) {
      const message = err instanceof ApiHttpError ? err.message : "Impossible de creer le besoin."
      setError(message)
      toast.error(message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <Card className="premium-panel premium-lift border-amber-200/65 bg-gradient-to-br from-stone-50 via-amber-50 to-teal-50">
      <CardHeader><CardTitle className="premium-title">Nouveau besoin</CardTitle></CardHeader>
      <CardContent>
        {error && <p className="mb-4 text-sm text-destructive">{error}</p>}
        {loading && <p className="premium-subtle mb-4 text-sm">Chargement des fiches...</p>}
        <form className="grid gap-4 md:grid-cols-2" onSubmit={save} noValidate>
          <Field label="Fiche de poste" error={fieldErrors.fiche_de_poste_id}>
            <Select
              value={form.fiche_de_poste_id}
              onChange={(event) => updateField("fiche_de_poste_id", event.target.value)}
              aria-invalid={Boolean(fieldErrors.fiche_de_poste_id)}
            >
              {availableFiches.map((fiche) => <option key={fiche.id} value={fiche.id}>{fiche.title}</option>)}
            </Select>
          </Field>
          <Field label="Lieu d'affectation" error={fieldErrors.lieu_affectation}>
            <Input
              value={form.lieu_affectation}
              onChange={(event) => updateField("lieu_affectation", event.target.value)}
              aria-invalid={Boolean(fieldErrors.lieu_affectation)}
            />
          </Field>
          <Field label="Motif de recrutement" error={fieldErrors.recruitment_reason}>
            <Textarea
              value={form.recruitment_reason}
              onChange={(event) => updateField("recruitment_reason", event.target.value)}
              aria-invalid={Boolean(fieldErrors.recruitment_reason)}
            />
          </Field>
          <Field label="Priorité" error={fieldErrors.priority}>
            <Select
              value={form.priority}
              onChange={(event) => updateField("priority", event.target.value)}
              aria-invalid={Boolean(fieldErrors.priority)}
            >
              <option value="HAUTE">Haute</option>
              <option value="NORMALE">Normale</option>
              <option value="BASSE">Basse</option>
            </Select>
          </Field>
          <Field label="Nombre de postes" error={fieldErrors.positions_count}>
            <Input
              type="number"
              min="1"
              value={form.positions_count}
              onChange={(event) => updateField("positions_count", event.target.value)}
              aria-invalid={Boolean(fieldErrors.positions_count)}
            />
          </Field>
          <Field label="Date souhaitée" error={fieldErrors.desired_date}>
            <Popover>
              <PopoverTrigger asChild>
                <Button
                  type="button"
                  variant="outline"
                  className={cn(
                    "w-full justify-start text-left font-normal",
                    !desiredDate && "text-muted-foreground",
                    fieldErrors.desired_date && "border-destructive"
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
                  onSelect={updateDesiredDate}
                  autoFocus
                />
              </PopoverContent>
            </Popover>
          </Field>
          <div className="md:col-span-2 flex gap-2">
            <Button type="submit" disabled={saving}>
              {saving ? "Création..." : "Créer"}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}

function Field({
  label,
  error,
  children,
}: {
  label: string
  error?: string
  children: React.ReactNode
}) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      {children}
      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  )
}