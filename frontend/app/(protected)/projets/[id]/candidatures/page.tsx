"use client"

import { use } from "react"

import { RoleGate } from "@/components/role-gate"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export default function ProjetCandidaturesPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params)

  return (
    <RoleGate roles={["ADMIN", "DRH", "DIRECTEUR", "DG"]}>
      <Card>
        <CardHeader>
          <CardTitle>Candidatures du projet #{resolvedParams.id}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
          <p>La liste des candidatures sera affichée ici.</p>
          <p>Aucune candidature disponible pour le moment dans ce module.</p>
        </CardContent>
      </Card>
    </RoleGate>
  )
}
