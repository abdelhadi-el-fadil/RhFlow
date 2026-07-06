import Link from "next/link"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export default function ForbiddenPage() {
  return (
    <div className="flex min-h-svh items-center justify-center bg-muted/30 p-6">
      <Card className="w-full max-w-md">
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