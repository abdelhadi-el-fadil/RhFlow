"use client"

import { use, useCallback, useEffect, useState } from "react"
import { toast } from "sonner"

import { useAuth } from "@/components/auth-provider"
import { RoleGate } from "@/components/role-gate"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"
import type { ApiResponse, PaginatedResponse, ProjetRecrutementResponse, UserResponse } from "@/lib/backend-types"
import { ApiHttpError, apiClient } from "@/lib/http"
import { badgeVariantFromProjetStatus, labelFromProjetStatus } from "@/lib/status-labels"

export default function ProjetDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params)
  const projectId = Number(resolvedParams.id)

  if (Number.isNaN(projectId)) {
    return (
      <RoleGate roles={["ADMIN", "DRH", "DIRECTEUR", "DG"]}>
        <Card className="premium-panel">
          <CardContent className="premium-copy">Identifiant projet invalide.</CardContent>
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
  const { user } = useAuth()
  const [item, setItem] = useState<ProjetRecrutementResponse | null>(null)
  const [managers, setManagers] = useState<UserResponse[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [form, setForm] = useState({ manager_id: "", email_subject: "" })

  const canManage = user?.role === "ADMIN" || user?.role === "DRH"

  const reload = useCallback(async () => {
    const [projectRes, usersRes] = await Promise.all([
      apiClient.get<ApiResponse<ProjetRecrutementResponse>>(`/projets/${id}`),
      canManage
        ? apiClient.get<PaginatedResponse<UserResponse>>("/users/", { params: { page: 1, page_size: 100 } })
        : Promise.resolve({ data: { data: [] as UserResponse[] } }),
    ])

    setItem(projectRes.data.data)
    setManagers(usersRes.data.data)
    setForm({
      manager_id: String(projectRes.data.data.manager_id),
      email_subject: projectRes.data.data.email_subject ?? "",
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

  if (isLoading) return <Card className="premium-panel"><CardContent className="premium-copy">Chargement…</CardContent></Card>
  if (error) return <Card className="premium-panel"><CardContent className="premium-copy">{error}</CardContent></Card>
  if (!item) return <Card className="premium-panel"><CardContent className="premium-subtle">Projet introuvable.</CardContent></Card>

  const save = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!canManage || item.status === "CLOSED") {
      setActionError("Ce projet est en lecture seule.")
      return
    }

    setActionError(null)
    try {
      await apiClient.put(`/projets/${id}`, {
        manager_id: Number(form.manager_id),
        email_subject: form.email_subject || null,
      })
      toast.success("Projet sauvegardé avec succès.")
      await reload()
    } catch (err) {
      const message = err instanceof ApiHttpError ? err.message : "Impossible de sauvegarder ce projet."
      setActionError(message)
      toast.error(message)
    }
  }

  return (
    <div className="space-y-6">
      <Card className="premium-panel premium-lift border-stone-300/70 bg-white/90">
        <CardHeader>
          <CardTitle className="premium-title">
            {item.title} <Badge variant={badgeVariantFromProjetStatus(item.status)}>{labelFromProjetStatus(item.status)}</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {actionError && <p className="mb-4 text-sm text-destructive">{actionError}</p>}
          <div className="premium-subtle mb-4 grid gap-2 text-sm">
            <p>Direction: {item.direction_name ?? "-"}</p>
            <p>Directeur: {item.director_name ?? "-"}</p>
            <p>Fiche de poste: {item.fiche_title ?? "-"}</p>
            <p>Besoin principal: {item.besoin_title ?? "-"}</p>
            <p>Nombre de postes: {item.nombre_postes ?? "-"}</p>
          </div>

          <form className="grid gap-4 md:grid-cols-2" onSubmit={save}>
            <Field label="Manager">
              <Select
                disabled={!canManage || item.status === "CLOSED"}
                value={form.manager_id}
                onChange={(event) => setForm((current) => ({ ...current, manager_id: event.target.value }))}
              >
                {managers.map((manager) => (
                  <option key={manager.id} value={manager.id}>{manager.full_name || manager.email}</option>
                ))}
              </Select>
            </Field>
            <Field label="Objet d'email">
              <Input
                disabled={!canManage || item.status === "CLOSED"}
                value={form.email_subject}
                onChange={(event) => setForm((current) => ({ ...current, email_subject: event.target.value }))}
              />
            </Field>
            <div className="md:col-span-2 flex flex-wrap gap-2">
              {canManage && item.status !== "CLOSED" && <Button type="submit">Sauvegarder</Button>}
              {canManage && item.status !== "CLOSED" && (
                <Button
                  type="button"
                  variant="secondary"
                  onClick={async () => {
                    setActionError(null)
                    try {
                      await apiClient.patch(`/projets/${id}/cloturer`)
                      toast.success("Projet clôturé avec succès.")
                      await reload()
                    } catch (err) {
                      const message = err instanceof ApiHttpError ? err.message : "Impossible de clôturer ce projet."
                      setActionError(message)
                      toast.error(message)
                    }
                  }}
                >
                  Clôturer
                </Button>
              )}
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <div className="space-y-2"><Label>{label}</Label>{children}</div>
}
