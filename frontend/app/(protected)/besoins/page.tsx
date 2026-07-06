"use client"

import Link from "next/link"
import { useEffect, useState } from "react"

import { RoleGate } from "@/components/role-gate"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { apiClient } from "@/lib/http"
import type { BesoinRecrutementResponse, PaginatedResponse } from "@/lib/backend-types"
import { badgeVariantFromBesoinStatus } from "@/lib/status-labels"
import { useAuth } from "@/components/auth-provider"

export default function BesoinsPage() {
  return (
    <RoleGate roles={["ADMIN", "DRH", "DIRECTEUR"]}>
      <BesoinsContent />
    </RoleGate>
  )
}

function BesoinsContent() {
  const { user } = useAuth()
  const [items, setItems] = useState<BesoinRecrutementResponse[]>([])
  const [loading, setLoading] = useState(true)

  const load = async () => {
    const response = await apiClient.get<PaginatedResponse<BesoinRecrutementResponse>>("/besoins/", { params: { page: 1, page_size: 50 } })
    setItems(response.data.data)
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load().finally(() => setLoading(false))
  }, [])

  return (
    <Card>
      <CardHeader>
        <CardTitle>Besoins de recrutement</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {(user?.role === "DIRECTEUR" || user?.role === "DRH") && (
          <Button asChild><Link href="/besoins/nouveau">Créer un besoin</Link></Button>
        )}
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Titre</TableHead>
              <TableHead>Fiche</TableHead>
              <TableHead>Statut</TableHead>
              <TableHead />
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.map((item) => (
              <TableRow key={item.id}>
                <TableCell>{item.title}</TableCell>
                <TableCell>{item.fiche_de_poste_id}</TableCell>
                <TableCell><Badge variant={badgeVariantFromBesoinStatus(item.status)}>{item.status}</Badge></TableCell>
                <TableCell className="text-right"><Button asChild variant="outline" size="sm"><Link href={`/besoins/${item.id}`}>Ouvrir</Link></Button></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        {loading && <p className="text-sm text-muted-foreground">Chargement…</p>}
      </CardContent>
    </Card>
  )
}
