"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import { HandCoins } from "lucide-react"

import { RoleGate } from "@/components/role-gate"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { ApiHttpError, apiClient } from "@/lib/http"
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
  const [error, setError] = useState<string | null>(null)
  const canCreate = user?.role === "DRH" || user?.role === "ADMIN" || user?.role === "DIRECTEUR" || user?.role === "DG"

  const load = async () => {
    const response = await apiClient.get<PaginatedResponse<OffrePublicResponse>>("/offres/", { params: { page: 1, page_size: 50 } })
    setItems(response.data.data)
  }

  useEffect(() => {
    const run = async () => {
      try {
        setError(null)
        await load()
      } catch (err) {
        setError(err instanceof ApiHttpError ? err.message : "Impossible de charger les offres.")
      }
    }

    void run()
  }, [])

  return (
    <div className="space-y-6">
      <Card className="border-sky-300/70 bg-linear-to-br from-sky-200 via-blue-200 to-cyan-100">
        <CardHeader className="flex flex-row items-start justify-between gap-4">
          <CardTitle className="flex items-center gap-2 text-sky-950">
            <HandCoins className="size-5 text-sky-800" />
            Offres publiées
          </CardTitle>
          {canCreate && (
            <Button asChild>
              <Link href="/offres/nouveau">Créer une offre</Link>
            </Button>
          )}
        </CardHeader>
        <CardContent>
          {error && <p className="mb-4 text-sm text-destructive">{error}</p>}
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
