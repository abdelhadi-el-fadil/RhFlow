"use client"

import Link from "next/link"
import { use, useEffect, useState } from "react"
import { HandCoins } from "lucide-react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

import { RoleGate } from "@/components/role-gate"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { ApiResponse, GeneratedOfferResponse } from "@/lib/backend-types"
import { ApiHttpError, apiClient } from "@/lib/http"

export default function ProjetOfferPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params)
  const projectId = Number(resolvedParams.id)

  if (Number.isNaN(projectId)) {
    return (
      <RoleGate roles={["ADMIN", "DRH", "DIRECTEUR", "DG"]}>
        <Card className="premium-panel">
          <CardContent className="premium-copy">Identifiant projet invalide.</CardContent>
        </Card>
      </RoleGate>
    )
  }

  return (
    <RoleGate roles={["ADMIN", "DRH", "DIRECTEUR", "DG"]}>
      <OfferContent projectId={projectId} />
    </RoleGate>
  )
}

function OfferContent({ projectId }: { projectId: number }) {
  const [offer, setOffer] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    const load = async () => {
      setIsLoading(true)
      setError(null)
      try {
        const response = await apiClient.get<ApiResponse<GeneratedOfferResponse>>(
          `/ai/generate-offer/${projectId}`,
        )
        if (!cancelled) {
          setOffer(response.data.data.offer)
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof ApiHttpError
              ? err.message
              : "Impossible de charger l'offre générée.",
          )
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false)
        }
      }
    }

    void load()

    return () => {
      cancelled = true
    }
  }, [projectId])

  return (
    <div className="stagger-enter space-y-6">
      <Card className="premium-panel premium-lift border-amber-200/65 bg-linear-to-br from-stone-50 via-amber-50 to-teal-50">
        <CardHeader className="flex flex-row items-start justify-between gap-4">
          <CardTitle className="premium-title flex items-center gap-2">
            <HandCoins className="size-5 text-teal-700" />
            Offre LinkedIn générée
          </CardTitle>
          <div className="flex flex-wrap gap-2">
            <Button asChild variant="outline">
              <Link href={`/projets/${projectId}`}>Retour au projet</Link>
            </Button>
            <Button asChild variant="outline">
              <Link href="/projets">Retour aux projets</Link>
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {error && <p className="mb-4 text-sm text-destructive">{error}</p>}
          {isLoading && (
            <p className="premium-copy animate-pulse motion-reduce:animate-none">
              Génération de l&apos;offre…
            </p>
          )}
          {!isLoading && offer && (
            <div className="rounded-lg border border-stone-300/70 bg-white/90 p-5 text-sm leading-6 text-stone-900">
              <MarkdownOffer content={offer} />
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

function MarkdownOffer({ content }: { content: string }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        h1: ({ children }) => <h1 className="mb-4 text-2xl font-semibold text-stone-950">{children}</h1>,
        h2: ({ children }) => <h2 className="mb-3 mt-6 text-xl font-semibold text-stone-950">{children}</h2>,
        h3: ({ children }) => <h3 className="mb-2 mt-5 text-lg font-semibold text-stone-950">{children}</h3>,
        p: ({ children }) => <p className="mb-4 last:mb-0">{children}</p>,
        ul: ({ children }) => <ul className="mb-4 list-disc space-y-2 pl-5 last:mb-0">{children}</ul>,
        ol: ({ children }) => <ol className="mb-4 list-decimal space-y-2 pl-5 last:mb-0">{children}</ol>,
        li: ({ children }) => <li className="pl-1">{children}</li>,
        blockquote: ({ children }) => (
          <blockquote className="mb-4 border-l-4 border-amber-300 bg-amber-50 px-4 py-3 italic text-stone-700 last:mb-0">
            {children}
          </blockquote>
        ),
        table: ({ children }) => (
          <div className="mb-4 overflow-x-auto last:mb-0">
            <table className="w-full border-collapse text-left text-sm">{children}</table>
          </div>
        ),
        thead: ({ children }) => <thead className="bg-stone-100 text-stone-900">{children}</thead>,
        th: ({ children }) => <th className="border border-stone-300 px-3 py-2 font-semibold">{children}</th>,
        td: ({ children }) => <td className="border border-stone-300 px-3 py-2 align-top">{children}</td>,
        hr: () => <hr className="my-6 border-stone-300" />,
        a: ({ children, href }) => (
          <a className="text-teal-700 underline underline-offset-4 hover:text-teal-900" href={href}>
            {children}
          </a>
        ),
        code: ({ children, className }) => {
          if (className) {
            return <code className={className}>{children}</code>
          }

          return (
            <code className="rounded bg-stone-100 px-1.5 py-0.5 font-mono text-[0.92em] text-stone-900">
              {children}
            </code>
          )
        },
        pre: ({ children }) => (
          <pre className="mb-4 overflow-x-auto rounded-lg bg-stone-950 p-4 font-mono text-sm text-stone-50 last:mb-0">
            {children}
          </pre>
        ),
      }}
    >
      {content}
    </ReactMarkdown>
  )
}
