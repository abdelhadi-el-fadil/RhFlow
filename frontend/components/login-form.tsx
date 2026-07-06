"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Loader2, ShieldCheck } from "lucide-react"

import { useAuth } from "@/components/auth-provider"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { ApiHttpError } from "@/lib/http"

export function LoginForm({
  className,
  ...props
}: React.ComponentProps<"div">) {
  const router = useRouter()
  const { signIn } = useAuth()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setIsLoading(true)
    setError(null)

    try {
      await signIn(email, password)
      router.push("/dashboard")
    } catch (err) {
      if (err instanceof ApiHttpError) {
        if (err.status === 401) {
          setError("Identifiants incorrects")
        } else if (err.status === 403) {
          setError("Compte désactivé, contactez l'administrateur")
        } else {
          setError(err.message)
        }
      } else {
        setError("Impossible de contacter le backend FastAPI")
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className={className} {...props}>
      <Card className="overflow-hidden border-border/70 bg-white/95 shadow-2xl shadow-slate-200/60 backdrop-blur">
        <CardHeader className="space-y-2 border-b border-border/60 bg-gradient-to-br from-slate-950 to-slate-800 text-white">
          <div className="flex items-center gap-2 text-sm text-slate-200">
            <ShieldCheck className="size-4" />
            FastAPI connecté
          </div>
          <CardTitle className="text-2xl text-white">Connexion RhFlow</CardTitle>
          <p className="text-sm text-slate-200">
            Accédez au tableau de bord RH avec votre compte backend.
          </p>
        </CardHeader>
        <CardContent className="p-6 md:p-8">
          <form className="space-y-5" onSubmit={handleSubmit}>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="prenom.nom@entreprise.com"
                autoComplete="email"
                required
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Mot de passe</Label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />
            </div>

            {error && (
              <div className="rounded-lg border border-destructive/20 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                {error}
              </div>
            )}

            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? (
                <>
                  <Loader2 className="size-4 animate-spin" />
                  Connexion en cours
                </>
              ) : (
                "Se connecter"
              )}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
