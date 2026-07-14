"use client"

import { Settings } from "lucide-react"
import { RoleGate } from "@/components/role-gate"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

export default function SettingsPage() {
  return (
    <RoleGate roles={["ADMIN", "DRH", "DIRECTEUR", "DG"]}>
      <Card className="premium-panel premium-lift border-amber-200/65 bg-gradient-to-br from-stone-50 via-amber-50 to-teal-50">
        <CardHeader>
          <CardDescription className="premium-copy">Configuration de l&apos;application</CardDescription>
          <CardTitle className="premium-title flex items-center gap-2"><Settings className="size-5 text-teal-700" />Paramètres</CardTitle>
        </CardHeader>
        <CardContent className="premium-subtle space-y-2 text-sm">
          <p>Cette section est prete pour accueillir les reglages du compte, notifications et preferences.</p>
          <p>Vous pouvez maintenant y ajouter des blocs de configuration sans modifier la structure de navigation.</p>
        </CardContent>
      </Card>
    </RoleGate>
  )
}
