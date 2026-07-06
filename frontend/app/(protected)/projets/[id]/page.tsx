"use client"

import { use, useEffect, useState } from "react"

import { RoleGate } from "@/components/role-gate"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { ApiHttpError, apiClient } from "@/lib/http"
import type { ApiResponse, BesoinRecrutementResponse, ProjetRecrutementResponse, PaginatedResponse } from "@/lib/backend-types"
import { badgeVariantFromProjetStatus } from "@/lib/status-labels"
import { useAuth } from "@/components/auth-provider"

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
  const { user } = useAuth()
  const [item, setItem] = useState<ProjetRecrutementResponse | null>(null)
  const [approvedNeeds, setApprovedNeeds] = useState<BesoinRecrutementResponse[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [attachNeedId, setAttachNeedId] = useState("")

  useEffect(() => {
    let cancelled = false

    const load = async () => {
      setIsLoading(true)
      setError(null)
      try {
        const [projectRes, needsRes] = await Promise.all([
          apiClient.get<ApiResponse<ProjetRecrutementResponse>>(`/projets/${id}`),
          apiClient.get<PaginatedResponse<BesoinRecrutementResponse>>("/besoins/", { params: { page: 1, page_size: 100 } }),
        ])
        if (cancelled) {
          return
        }

        setItem(projectRes.data.data)
        setApprovedNeeds(needsRes.data.data.filter((need) => need.status === "APPROVED"))
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiHttpError ? err.message : "Impossible de charger ce projet.")
          setItem(null)
          setApprovedNeeds([])
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

  if (isLoading) return <Card><CardContent>Chargement…</CardContent></Card>
  if (error) return <Card><CardContent>{error}</CardContent></Card>
  if (!item) return <Card><CardContent>Projet introuvable.</CardContent></Card>

  const attach = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const parsedNeedId = Number(attachNeedId)
    if (Number.isNaN(parsedNeedId)) {
      return
    }

    await apiClient.post(`/projets/${id}/besoins/${parsedNeedId}`)
    window.location.reload()
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader><CardTitle>{item.title} <Badge variant={badgeVariantFromProjetStatus(item.status)}>{item.status}</Badge></CardTitle></CardHeader>
        <CardContent className="grid gap-2 text-sm text-muted-foreground">
          <p>Manager ID: {item.manager_id}</p>
          <p>Période: {item.start_date} → {item.expected_end_date}</p>
          <p>{item.description ?? "-"}</p>
        </CardContent>
      </Card>

      {user?.role === "DRH" && (
        <Card>
          <CardHeader><CardTitle>Rattacher un besoin approuvé</CardTitle></CardHeader>
          <CardContent>
            <form className="flex gap-3" onSubmit={attach}>
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
              <TableRow><TableHead>Titre</TableHead><TableHead>Statut</TableHead><TableHead /></TableRow>
            </TableHeader>
            <TableBody>
              {item.besoins.map((need) => (
                <TableRow key={need.id}>
                  <TableCell>{need.title}</TableCell>
                  <TableCell><Badge variant="outline">{need.status}</Badge></TableCell>
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
