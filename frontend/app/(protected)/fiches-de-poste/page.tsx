"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import { FileText } from "lucide-react"
import { toast } from "sonner"

import { RoleGate } from "@/components/role-gate"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"
import { ApiHttpError, apiClient } from "@/lib/http"
import type { DirectionResponse, FicheDePosteResponse, PaginatedResponse } from "@/lib/backend-types"
import { useAuth } from "@/components/auth-provider"

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
  const [search, setSearch] = useState("")
  const [directionFilter, setDirectionFilter] = useState("")

  const canCreateFiche = user?.role === "ADMIN" || user?.role === "DRH" || user?.role === "DIRECTEUR"
  const canDeleteFiche = user?.role === "ADMIN" || user?.role === "DRH"

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

  const deleteFiche = async (id: number) => {
    if (!confirm("Supprimer cette fiche de poste ?")) {
      return
    }
    try {
      await apiClient.delete(`/fiches-de-poste/${id}`)
      await load()
      toast.success("Fiche supprimée avec succès.")
    } catch (err) {
      toast.error(err instanceof ApiHttpError ? err.message : "Impossible de supprimer la fiche.")
    }
  }

  const clearFilters = () => {
    setSearch("")
    setDirectionFilter("")
  }

  const filteredItems = items.filter((item) => {
    const haystack = `${item.title} ${item.main_activities} ${item.direction_name ?? ""} ${item.experience_level} ${item.education_level ?? ""} ${item.technical_skills ?? ""} ${item.managerial_skills ?? ""}`.toLowerCase()
    const matchesSearch = search.trim() === "" || haystack.includes(search.trim().toLowerCase())
    const matchesDirection = directionFilter === "" || directionFilter === "ALL" || String(item.direction_id) === directionFilter
    return matchesSearch && matchesDirection
  })

  return (
    <div className="space-y-6">
      <Card className="border-sky-300/70 bg-linear-to-br from-sky-200 via-blue-200 to-cyan-100">
        <CardHeader className="flex flex-row items-start justify-between gap-4">
          <div>
          <CardDescription className="text-sky-800">{loading ? "Chargement…" : `${filteredItems.length} fiches`}</CardDescription>
          <CardTitle className="flex items-center gap-2 text-sky-950">
            <FileText className="size-5 text-sky-800" />
            Fiches de poste
          </CardTitle>
          </div>
          {canCreateFiche && (
            <Button asChild>
              <Link href="/fiches-de-poste/nouveau">Créer une fiche</Link>
            </Button>
          )}
        </CardHeader>
        <CardContent>
          {error && <p className="mb-4 text-sm text-destructive">{error}</p>}
          <div className="mb-4 flex flex-col gap-4 md:flex-row md:items-end">
            <div className="grid flex-1 gap-4 md:grid-cols-2">
              <Field label="Recherche"><Input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Titre, direction, compétences" /></Field>
              <Field label="Direction"><Select value={directionFilter} onChange={(event) => setDirectionFilter(event.target.value)} placeholder="Choisir une direction"><option value="ALL">Toutes</option>{directions.map((direction) => <option key={direction.id} value={direction.id}>{direction.name}</option>)}</Select></Field>
            </div>
            <Button
              type="button"
              variant="ghost"
              onClick={clearFilters}
              className="bg-sky-500 text-white hover:bg-sky-700 hover:text-white md:self-end"
            >
              Effacer les filtres
            </Button>
          </div>
          <div className="grid gap-3 xl:grid-cols-2">
            {filteredItems.map((item) => (
              <Card key={item.id} className="border-sky-200 bg-white/80">
                <CardHeader className="gap-1 p-4">
                  <CardDescription className="text-sky-800 text-xs">{item.direction_name ?? `Direction #${item.direction_id}`}</CardDescription>
                  <CardTitle className="text-base text-sky-950">{item.title}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 p-4 pt-0">
                  <div className="grid gap-2 md:grid-cols-2">
                    <Info label="Niveau d'expérience" value={item.experience_level} />
                    <Info label="Niveau d'études" value={item.education_level ?? "-"} />
                    <Info label="Domaine de formation" value={item.formation_domain ?? "-"} />
                  </div>
                  <Info label="Activités principales" value={item.main_activities} />
                  <Info label="Missions" value={item.missions} />
                  <div className="grid gap-2 md:grid-cols-2">
                    <Info label="Compétences techniques" value={item.technical_skills ?? "-"} />
                    <Info label="Compétences managériales" value={item.managerial_skills ?? "-"} />
                  </div>
                  <div className="flex flex-wrap items-center justify-between gap-2 border-t border-sky-100 pt-3">
                    <span className="text-xs text-sky-800">Direction: {item.direction_name ?? `#${item.direction_id}`}</span>
                    <div className="flex gap-2">
                      <Button asChild variant="outline" size="sm"><a href={`/fiches-de-poste/${item.id}`}>Ouvrir</a></Button>
                      {canDeleteFiche && <Button variant="destructive" size="sm" onClick={() => deleteFiche(item.id)}>Supprimer</Button>}
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
    <div className="space-y-0.5 rounded-lg border border-sky-100 bg-sky-50/60 p-2">
      <p className="text-[11px] font-medium uppercase tracking-wide text-sky-700">{label}</p>
      <p className="whitespace-pre-line text-sm leading-snug text-sky-950">{value}</p>
    </div>
  )
}