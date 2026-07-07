import Link from "next/link"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export default function ForbiddenPage() {
  return (
    <div className="relative flex min-h-svh items-center justify-center p-6">
      <div className="pointer-events-none absolute inset-0 brand-gradient-soft opacity-60" />
      <Card className="relative w-full max-w-md border-indigo-200/70 bg-white/90">
        <CardHeader>
          <CardTitle>Accès refusé</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-sm text-muted-foreground">
          <p>Votre rôle ne permet pas d’accéder à cette page.</p>
          <Button asChild>
            <Link href="/dashboard">Retour au tableau de bord</Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}