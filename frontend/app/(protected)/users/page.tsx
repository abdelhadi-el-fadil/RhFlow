"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import { Eye, ImageIcon, Users, X } from "lucide-react"
import { toast } from "sonner"

import { useAuth } from "@/components/auth-provider"
import { RoleGate } from "@/components/role-gate"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { ApiHttpError, apiClient } from "@/lib/http"
import { type ApiResponse, type PaginatedResponse, type UserResponse, type UserSignatureResponse } from "@/lib/backend-types"
const ROLE_FILTERS: UserResponse["role"][] = ["ADMIN", "DRH", "DIRECTEUR", "DG"]

export default function UsersPage() {
  return (
    <RoleGate roles={["ADMIN", "DRH"]}>
      <UsersContent />
    </RoleGate>
  )
}

function UsersContent() {
  const { user } = useAuth()
  const [items, setItems] = useState<UserResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [draft, setDraft] = useState<UserResponse | null>(null)
  const [search, setSearch] = useState("")
  const [roleFilter, setRoleFilter] = useState<UserResponse["role"] | "" | "ALL">("")
  const [statusFilter, setStatusFilter] = useState<"" | "ALL" | "ENABLED" | "DISABLED">("")
  const [error, setError] = useState<string | null>(null)
  const [signatureFiles, setSignatureFiles] = useState<Record<number, File | null>>({})
  const [uploadingSignatureId, setUploadingSignatureId] = useState<number | null>(null)
  const [signaturePreview, setSignaturePreview] = useState<{ userId: number; url: string } | null>(null)
  const [previewLoadingId, setPreviewLoadingId] = useState<number | null>(null)
  const [signatureUrls, setSignatureUrls] = useState<Record<number, string>>({})

  const uploadSignatureFile = async (userId: number, file: File) => {
    const formData = new FormData()
    formData.append("file", file)
    await apiClient.post(`/users/${userId}/signature`, formData)
  }

  const loadUsers = async () => {
    const response = await apiClient.get<PaginatedResponse<UserResponse>>("/users/", { params: { page: 1, page_size: 50 } })
    setItems(response.data.data)
  }

  useEffect(() => {
    const run = async () => {
      try {
        setError(null)
        await loadUsers()
      } catch (err) {
        setError(err instanceof ApiHttpError ? err.message : "Impossible de charger les utilisateurs.")
      } finally {
        setLoading(false)
      }
    }

    void run()
  }, [])

  useEffect(() => {
    const targetUsers = items.filter((item) => item.signature_key && !signatureUrls[item.id])
    if (targetUsers.length === 0) {
      return
    }

    let cancelled = false

    const run = async () => {
      const entries = await Promise.all(
        targetUsers.map(async (item) => {
          try {
            const response = await apiClient.get<ApiResponse<UserSignatureResponse>>(
              `/users/${item.id}/signature`,
            )
            return [item.id, response.data.data.url] as const
          } catch {
            return null
          }
        }),
      )

      if (cancelled) {
        return
      }

      const nextEntries = Object.fromEntries(
        entries.filter((entry): entry is readonly [number, string] => entry !== null),
      )
      if (Object.keys(nextEntries).length === 0) {
        return
      }

      setSignatureUrls((current) => ({ ...current, ...nextEntries }))
    }

    void run()

    return () => {
      cancelled = true
    }
  }, [items, signatureUrls])

  const deleteUser = async (userId: number) => {
    if (!confirm("Supprimer ce compte ?")) {
      return
    }

    try {
      await apiClient.delete(`/users/${userId}`)
      await loadUsers()
      toast.success("Utilisateur supprimé avec succès.")
    } catch (err) {
      toast.error(err instanceof ApiHttpError ? err.message : "Impossible de supprimer cet utilisateur.")
    }
  }

  const startEdit = (item: UserResponse) => {
    setEditingId(item.id)
    setDraft(item)
    setSignatureFiles((current) => ({ ...current, [item.id]: null }))
  }

  const saveEdit = async () => {
    if (!draft) {
      return
    }

    try {
      await apiClient.put(`/users/${draft.id}`, {
        email: draft.email,
        password: undefined,
        full_name: draft.full_name,
        gsm: draft.gsm,
        role: draft.role,
        enabled: draft.enabled,
      })

      const signatureFile = signatureFiles[draft.id]
      if (signatureFile) {
        setUploadingSignatureId(draft.id)
        await uploadSignatureFile(draft.id, signatureFile)
      }

      setEditingId(null)
      setDraft(null)
      setSignatureFiles((current) => ({ ...current, [draft.id]: null }))
      await loadUsers()
      toast.success("Utilisateur modifié avec succès.")
    } catch (err) {
      toast.error(err instanceof ApiHttpError ? err.message : "Impossible de modifier cet utilisateur.")
    } finally {
      setUploadingSignatureId(null)
    }
  }

  const toggleUserEnabled = async (item: UserResponse) => {
    try {
      await apiClient.put(`/users/${item.id}`, { enabled: !item.enabled })
      await loadUsers()
      toast.success(item.enabled ? "Utilisateur désactivé avec succès." : "Utilisateur réactivé avec succès.")
    } catch (err) {
      toast.error(err instanceof ApiHttpError ? err.message : "Impossible de mettre à jour le statut de cet utilisateur.")
    }
  }

  const openSignature = async (userId: number) => {
    setPreviewLoadingId(userId)
    try {
      const cached = signatureUrls[userId]
      if (cached) {
        setSignaturePreview({ userId, url: cached })
        return
      }

      const response = await apiClient.get<ApiResponse<UserSignatureResponse>>(`/users/${userId}/signature`)
      const url = response.data.data.url
      setSignatureUrls((current) => ({ ...current, [userId]: url }))
      setSignaturePreview({ userId, url })
    } catch (err) {
      toast.error(err instanceof ApiHttpError ? err.message : "Impossible d'afficher la signature.")
    } finally {
      setPreviewLoadingId(null)
    }
  }

  const closeSignaturePreview = () => setSignaturePreview(null)

  const uploadSignature = async (userId: number) => {
    const file = signatureFiles[userId]
    if (!file) {
      toast.error("Choisissez une image PNG ou JPEG pour la signature.")
      return
    }

    setUploadingSignatureId(userId)
    try {
      await uploadSignatureFile(userId, file)
      setSignatureFiles((current) => ({ ...current, [userId]: null }))
      setSignatureUrls((current) => {
        const next = { ...current }
        delete next[userId]
        return next
      })
      await loadUsers()
      toast.success("Signature mise à jour avec succès.")
    } catch (err) {
      toast.error(err instanceof ApiHttpError ? err.message : "Impossible de mettre à jour la signature.")
    } finally {
      setUploadingSignatureId(null)
    }
  }

  const deleteSignature = async (userId: number) => {
    if (!confirm("Supprimer la signature de cet utilisateur ?")) {
      return
    }

    setUploadingSignatureId(userId)
    try {
      await apiClient.delete(`/users/${userId}/signature`)
      setSignaturePreview((current) => (current?.userId === userId ? null : current))
      setSignatureUrls((current) => {
        const next = { ...current }
        delete next[userId]
        return next
      })
      await loadUsers()
      toast.success("Signature supprimée avec succès.")
    } catch (err) {
      toast.error(err instanceof ApiHttpError ? err.message : "Impossible de supprimer la signature.")
    } finally {
      setUploadingSignatureId(null)
    }
  }

  const clearFilters = () => {
    setSearch("")
    setRoleFilter("")
    setStatusFilter("")
  }

  const filteredItems = items.filter((item) => {
    const haystack = `${item.email} ${item.full_name ?? ""} ${item.gsm ?? ""}`.toLowerCase()
    const matchesSearch = search.trim() === "" || haystack.includes(search.trim().toLowerCase())
    const matchesRole = roleFilter === "" || roleFilter === "ALL" || item.role === roleFilter
    const matchesStatus = statusFilter === "" || statusFilter === "ALL" || (statusFilter === "ENABLED" ? item.enabled : !item.enabled)
    return matchesSearch && matchesRole && matchesStatus
  })

  return (
    <div className="stagger-enter space-y-6">
      <Card className="premium-panel premium-lift border-amber-200/65 bg-linear-to-br from-stone-50 via-amber-50 to-teal-50">
        <CardHeader className="flex flex-row items-start justify-between gap-4">
          <div>
          <CardDescription className="premium-copy">{loading ? "Chargement…" : `${filteredItems.length} résultats`}</CardDescription>
          <CardTitle className="premium-title flex items-center gap-2">
            <Users className="size-5 text-teal-700" />
            Utilisateurs
          </CardTitle>
          </div>
          {(user?.role === "ADMIN" || user?.role === "DRH") && (
            <Button asChild>
              <Link href="/users/nouveau">Créer un utilisateur</Link>
            </Button>
          )}
        </CardHeader>
        <CardContent>
          {user?.role !== "ADMIN" && user?.role !== "DRH" && <p className="premium-subtle mb-4 text-sm">Consultation uniquement pour ce rôle.</p>}
          {error && <p className="mb-4 text-sm text-destructive">{error}</p>}
          <div className="mb-4 flex flex-col gap-4 md:flex-row md:items-end">
            <div className="grid flex-1 gap-4 md:grid-cols-3">
              <Field label="Recherche"><Input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Email, nom, téléphone" /></Field>
              <Field label="Rôle"><Select value={roleFilter} onChange={(event) => setRoleFilter(event.target.value as UserResponse["role"] | "" | "ALL")} placeholder="Choisir un rôle"><option value="ALL">Tous</option>{ROLE_FILTERS.map((role) => <option key={role} value={role}>{role}</option>)}</Select></Field>
              <Field label="Statut"><Select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value as "" | "ALL" | "ENABLED" | "DISABLED")} placeholder="Choisir un statut"><option value="ALL">Tous</option><option value="ENABLED">Actifs</option><option value="DISABLED">Désactivés</option></Select></Field>
            </div>
            <Button
              type="button"
              variant="ghost"
              onClick={clearFilters}
              className="bg-teal-700 text-white hover:bg-teal-800 hover:text-white md:self-end"
            >
              Effacer les filtres
            </Button>
          </div>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Email</TableHead>
                <TableHead>Nom</TableHead>
                <TableHead>Téléphone</TableHead>
                <TableHead>Rôle</TableHead>
                <TableHead>Statut</TableHead>
                <TableHead>Signature</TableHead>
                <TableHead />
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredItems.map((item) => (
                <TableRow key={item.id}>
                  <TableCell>{editingId === item.id && draft ? <Input value={draft.email} onChange={(event) => setDraft((current) => current ? { ...current, email: event.target.value } : current)} /> : item.email}</TableCell>
                  <TableCell>{editingId === item.id && draft ? <Input value={draft.full_name ?? ""} onChange={(event) => setDraft((current) => current ? { ...current, full_name: event.target.value } : current)} /> : (item.full_name ?? "-")}</TableCell>
                  <TableCell>{editingId === item.id && draft ? <Input value={draft.gsm ?? ""} onChange={(event) => setDraft((current) => current ? { ...current, gsm: event.target.value } : current)} /> : (item.gsm ?? "-")}</TableCell>
                  <TableCell>
                    {editingId === item.id && draft ? (
                      <Select value={draft.role} onChange={(event) => setDraft((current) => current ? { ...current, role: event.target.value as UserResponse["role"] } : current)}>
                        <option value="ADMIN">ADMIN</option><option value="DRH">DRH</option><option value="DIRECTEUR">DIRECTEUR</option><option value="DG">DG</option>
                      </Select>
                    ) : (
                      <Badge variant="secondary">{item.role}</Badge>
                    )}
                  </TableCell>
                  <TableCell>{editingId === item.id && draft ? <Select value={String(draft.enabled)} onChange={(event) => setDraft((current) => current ? { ...current, enabled: event.target.value === "true" } : current)}><option value="true">Actif</option><option value="false">Désactivé</option></Select> : <Badge variant={item.enabled ? "default" : "destructive"}>{item.enabled ? "Actif" : "Désactivé"}</Badge>}</TableCell>
                  <TableCell>
                    <div className="flex flex-wrap items-center gap-2">
                      {item.signature_key ? (
                        <>
                          <button
                            type="button"
                            onClick={() => void openSignature(item.id)}
                            className="overflow-hidden rounded-md border border-stone-300/70 bg-white"
                            aria-label="Voir la signature"
                            disabled={previewLoadingId === item.id}
                          >
                            {signatureUrls[item.id] ? (
                              // eslint-disable-next-line @next/next/no-img-element
                              <img
                                src={signatureUrls[item.id]}
                                alt={`Signature de ${item.full_name ?? item.email}`}
                                className="h-12 w-24 object-contain"
                              />
                            ) : (
                              <div className="flex h-12 w-24 items-center justify-center gap-1 text-xs text-muted-foreground">
                                <ImageIcon className="size-3.5" />
                                Signature
                              </div>
                            )}
                          </button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => void openSignature(item.id)}
                            disabled={previewLoadingId === item.id}
                          >
                            <Eye className="size-4" />
                            {previewLoadingId === item.id ? "Chargement..." : "Voir"}
                          </Button>
                        </>
                      ) : (
                        <span className="premium-subtle text-xs">Aucune</span>
                      )}

                      {editingId === item.id && (user?.role === "ADMIN" || user?.role === "DRH") && (
                        <>
                          <Input
                            type="file"
                            accept="image/png,image/jpeg"
                            className="h-8 w-44"
                            onChange={(event) => {
                              const selected = event.target.files?.[0] ?? null
                              setSignatureFiles((current) => ({ ...current, [item.id]: selected }))
                            }}
                          />
                          <Button
                            size="sm"
                            variant="secondary"
                            disabled={uploadingSignatureId === item.id}
                            onClick={() => uploadSignature(item.id)}
                          >
                            {uploadingSignatureId === item.id ? "Upload..." : "Signature"}
                          </Button>
                          {item.signature_key && (
                            <Button
                              size="sm"
                              variant="destructive"
                              disabled={uploadingSignatureId === item.id}
                              onClick={() => deleteSignature(item.id)}
                            >
                              Supprimer signature
                            </Button>
                          )}
                        </>
                      )}
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    {(user?.role === "ADMIN" || user?.role === "DRH") && (
                      <div className="flex flex-wrap items-center justify-end gap-2">
                        {editingId === item.id ? (
                          <Button size="sm" onClick={saveEdit}>Sauvegarder</Button>
                        ) : (
                          <Button variant="outline" size="sm" onClick={() => startEdit(item)}>Modifier</Button>
                        )}
                        <Button
                          variant={item.enabled ? "secondary" : "default"}
                          size="sm"
                          onClick={() => toggleUserEnabled(item)}
                        >
                          {item.enabled ? "Désactiver" : "Réactiver"}
                        </Button>
                        <Button variant="destructive" size="sm" onClick={() => deleteUser(item.id)}>
                          Supprimer
                        </Button>
                      </div>
                    )}
                  </TableCell>
                </TableRow>
              ))}
              {filteredItems.length === 0 && (
                <TableRow>
                  <TableCell colSpan={7} className="premium-subtle text-center text-sm">Aucun utilisateur ne correspond aux filtres.</TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {signaturePreview && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
          role="dialog"
          aria-modal="true"
          onClick={closeSignaturePreview}
        >
          <div
            className="premium-panel w-full max-w-lg border-stone-300/70 p-4"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="mb-3 flex items-center justify-between">
              <span className="text-sm font-medium text-slate-900">Signature</span>
              <button
                type="button"
                onClick={closeSignaturePreview}
                aria-label="Fermer"
                className="rounded-sm p-1 text-teal-700 hover:bg-amber-50"
              >
                <X className="size-4" />
              </button>
            </div>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={signaturePreview.url}
              alt="Signature utilisateur"
              className="h-64 w-full rounded border border-stone-300/70 bg-white object-contain"
            />
          </div>
        </div>
      )}
    </div>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      {children}
    </div>
  )
}