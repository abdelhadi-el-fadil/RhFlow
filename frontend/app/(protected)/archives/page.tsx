"use client"

import Link from "next/link"
import { Archive, BookUser, ClipboardList } from "lucide-react"

import { RoleGate } from "@/components/role-gate"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export default function ArchivesPage() {
  return (
    <RoleGate roles={["ADMIN", "DRH", "DIRECTEUR", "DG"]}>
      <div className="stagger-enter space-y-6">
        <Card className="premium-panel premium-lift border-amber-200/65 bg-linear-to-br from-stone-50 via-amber-50 to-teal-50">
          <CardHeader>
            <CardTitle className="premium-title flex items-center gap-2">
              <Archive className="size-5 text-teal-700" />
              Archives
            </CardTitle>
          </CardHeader>
          <CardContent className="premium-subtle">
            Choisissez le type d&apos;archive à consulter depuis le sous-menu ou avec les raccourcis ci-dessous.
          </CardContent>
        </Card>

        <div className="grid gap-4 md:grid-cols-2">
          <Card className="premium-panel premium-lift border-stone-300/70 bg-white/90">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <ClipboardList className="size-5 text-teal-700" />
                Besoins de recrutement
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-slate-700">
                Consulter tous les besoins archivés avec les filtres de direction et de priorité.
              </p>
              <Button asChild>
                <Link href="/archives/besoins">Ouvrir les archives besoins</Link>
              </Button>
            </CardContent>
          </Card>

          <Card className="premium-panel premium-lift border-stone-300/70 bg-white/90">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <BookUser className="size-5 text-teal-700" />
                Projets de recrutement
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-slate-700">
                Consulter tous les projets archivés par direction avec leur contexte de recrutement.
              </p>
              <Button asChild>
                <Link href="/archives/projets">Ouvrir les archives projets</Link>
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </RoleGate>
  )
}
