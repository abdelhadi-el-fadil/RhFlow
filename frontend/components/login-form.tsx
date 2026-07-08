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
      <Card className="mx-auto w-full max-w-xl overflow-hidden rounded-2xl border border-sky-100 bg-gradient-to-br from-sky-100  via-sky-100 to-blue-100 shadow-2xl shadow-slate-950/20 backdrop-blur-md">
        <CardContent className="p-0">
          <div className="grid">
            <section className="flex items-center justify-center p-6 sm:p-8">
              <div className="w-full max-w-md space-y-6">
                <CardHeader className="space-y-3 rounded-xl bg-gradient-to-r from-slate-500  to-sky-400 px-5 py-5">
                  <div className="flex items-center gap-2 text-sm text-sky-200">
                    <ShieldCheck className="size-4" />
                    FastAPI connecté
                  </div>

                  <CardTitle className="text-3xl font-bold tracking-tight text-white">
                    Connexion RhFlow
                  </CardTitle>

                  <p className="text-sm leading-relaxed text-slate-300">
                    Accédez au tableau de bord RH avec votre compte backend.
                  </p>
                </CardHeader>

                <form className="space-y-5" onSubmit={handleSubmit}>
                  <div className="space-y-2">
                    <Label htmlFor="email" className="text-slate-700">
                      Email
                    </Label>

                    <Input
                      id="email"
                      type="email"
                      placeholder="prenom.nom@entreprise.com"
                      autoComplete="email"
                      required
                      value={email}
                      onChange={(event) => setEmail(event.target.value)}
                      className="border-slate-300 focus:border-blue-600 focus:ring-blue-600"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="password" className="text-slate-700">
                      Mot de passe
                    </Label>

                    <Input
                      id="password"
                      type="password"
                      autoComplete="current-password"
                      required
                      value={password}
                      onChange={(event) => setPassword(event.target.value)}
                      className="border-slate-300 focus:border-blue-600 focus:ring-blue-600"
                    />
                  </div>

                  {error && (
                    <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                      {error}
                    </div>
                  )}

                  <Button
                    type="submit"
                    className="w-full bg-blue-700 text-white transition-all duration-200 hover:bg-blue-800"
                    disabled={isLoading}
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="mr-2 size-4 animate-spin" />
                        Connexion en cours...
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