"use client"

import { use } from "react"

import { RoleGate } from "@/components/role-gate"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export default function ProjetCandidaturesPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params)

  return (
    <RoleGate roles={["ADMIN", "DRH", "DIRECTEUR", "DG"]}>
      <Card className="premium-panel premium-lift border-amber-200/65 bg-gradient-to-br from-stone-50 via-amber-50 to-teal-50">
        <CardHeader>
          <CardTitle className="premium-title">Candidatures du projet #{resolvedParams.id}</CardTitle>
        </CardHeader>
        <CardContent className="premium-subtle space-y-2 text-sm">
          <p>La liste des candidatures sera affichée ici.</p>
          <p>Aucune candidature disponible pour le moment dans ce module.</p>
        </CardContent>
      </Card>
    </RoleGate>
  )
}
