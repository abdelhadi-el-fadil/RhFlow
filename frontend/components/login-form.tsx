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
      <Card className="mx-auto w-full max-w-xl overflow-hidden border border-blue-300/80 bg-blue-100/95 shadow-2xl shadow-blue-300/30 backdrop-blur-sm">
        <CardContent className="p-0">
          <div className="grid">
            <section className="flex items-center justify-center p-6 sm:p-8">
              <div className="w-full max-w-md space-y-5">
                <CardHeader className="space-y-2 rounded-xl border border-indigo-100/80 brand-gradient-soft px-4 py-4">
                  <div className="flex items-center gap-2 text-sm text-indigo-700">
                    <ShieldCheck className="size-4" />
                    FastAPI connecte
                  </div>
                  <CardTitle className="text-2xl text-indigo-950">Connexion RhFlow</CardTitle>
                  <p className="text-sm text-indigo-700">
                    Accedez au tableau de bord RH avec votre compte backend.
                  </p>
                </CardHeader>

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
              </div>
            </section>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
