"use client"

import { Settings } from "lucide-react"
import { RoleGate } from "@/components/role-gate"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

export default function SettingsPage() {
  return (
    <RoleGate roles={["ADMIN", "DRH", "DIRECTEUR", "DG"]}>
      <Card>
        <CardHeader>
          <CardDescription>Configuration de l&apos;application</CardDescription>
          <CardTitle className="flex items-center gap-2"><Settings className="size-5 text-indigo-700" />Paramètres</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
          <p>Cette section est prete pour accueillir les reglages du compte, notifications et preferences.</p>
          <p>Vous pouvez maintenant y ajouter des blocs de configuration sans modifier la structure de navigation.</p>
        </CardContent>
      </Card>
    </RoleGate>
  )
}
