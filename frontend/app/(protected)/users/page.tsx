"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import { Eye, Users, X } from "lucide-react"

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
  const [actionError, setActionError] = useState<string | null>(null)
  const [signatureFiles, setSignatureFiles] = useState<Record<number, File | null>>({})
  const [uploadingSignatureId, setUploadingSignatureId] = useState<number | null>(null)
  const [signaturePreview, setSignaturePreview] = useState<{ userId: number; url: string } | null>(null)
  const [previewLoadingId, setPreviewLoadingId] = useState<number | null>(null)

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

  const deleteUser = async (userId: number) => {
    if (!confirm("Supprimer ce compte ?")) {
      return
    }

    setActionError(null)
    try {
      await apiClient.delete(`/users/${userId}`)
      await loadUsers()
    } catch (err) {
      setActionError(err instanceof ApiHttpError ? err.message : "Impossible de supprimer cet utilisateur.")
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

    setActionError(null)
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
    } catch (err) {
      setActionError(err instanceof ApiHttpError ? err.message : "Impossible de modifier cet utilisateur.")
    } finally {
      setUploadingSignatureId(null)
    }
  }

  const toggleUserEnabled = async (item: UserResponse) => {
    setActionError(null)
    try {
      await apiClient.put(`/users/${item.id}`, { enabled: !item.enabled })
      await loadUsers()
    } catch (err) {
      setActionError(err instanceof ApiHttpError ? err.message : "Impossible de mettre à jour le statut de cet utilisateur.")
    }
  }

  const openSignature = async (userId: number) => {
    setActionError(null)
    setPreviewLoadingId(userId)
    try {
      const response = await apiClient.get<ApiResponse<UserSignatureResponse>>(`/users/${userId}/signature`)
      setSignaturePreview({ userId, url: response.data.data.url })
    } catch (err) {
      setActionError(err instanceof ApiHttpError ? err.message : "Impossible d'afficher la signature.")
    } finally {
      setPreviewLoadingId(null)
    }
  }

  const closeSignaturePreview = () => setSignaturePreview(null)

  const uploadSignature = async (userId: number) => {
    const file = signatureFiles[userId]
    if (!file) {
      setActionError("Choisissez une image PNG ou JPEG pour la signature.")
      return
    }

    setUploadingSignatureId(userId)
    setActionError(null)
    try {
      await uploadSignatureFile(userId, file)
      setSignatureFiles((current) => ({ ...current, [userId]: null }))
      await loadUsers()
    } catch (err) {
      setActionError(err instanceof ApiHttpError ? err.message : "Impossible de mettre à jour la signature.")
    } finally {
      setUploadingSignatureId(null)
    }
  }

  const deleteSignature = async (userId: number) => {
    if (!confirm("Supprimer la signature de cet utilisateur ?")) {
      return
    }

    setActionError(null)
    setUploadingSignatureId(userId)
    try {
      await apiClient.delete(`/users/${userId}/signature`)
      setSignaturePreview((current) => (current?.userId === userId ? null : current))
      await loadUsers()
    } catch (err) {
      setActionError(err instanceof ApiHttpError ? err.message : "Impossible de supprimer la signature.")
    } finally {
      setUploadingSignatureId(null)
    }
  }

  const filteredItems = items.filter((item) => {
    const haystack = `${item.email} ${item.full_name ?? ""} ${item.gsm ?? ""}`.toLowerCase()
    const matchesSearch = search.trim() === "" || haystack.includes(search.trim().toLowerCase())
    const matchesRole = roleFilter === "" || roleFilter === "ALL" || item.role === roleFilter
    const matchesStatus = statusFilter === "" || statusFilter === "ALL" || (statusFilter === "ENABLED" ? item.enabled : !item.enabled)
    return matchesSearch && matchesRole && matchesStatus
  })

  return (
    <div className="space-y-6">
      <Card className="border-sky-300/70 bg-linear-to-br from-sky-200 via-blue-200 to-cyan-100">
        <CardHeader className="flex flex-row items-start justify-between gap-4">
          <div>
          <CardDescription className="text-sky-800">{loading ? "Chargement…" : `${filteredItems.length} résultats`}</CardDescription>
          <CardTitle className="flex items-center gap-2 text-sky-950">
            <Users className="size-5 text-sky-800" />
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
          {user?.role !== "ADMIN" && user?.role !== "DRH" && <p className="mb-4 text-sm text-sky-800/80">Consultation uniquement pour ce rôle.</p>}
          {error && <p className="mb-4 text-sm text-destructive">{error}</p>}
          {actionError && <p className="mb-4 text-sm text-destructive">{actionError}</p>}
          <div className="mb-4 grid gap-4 md:grid-cols-3">
            <Field label="Recherche"><Input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Email, nom, téléphone" /></Field>
            <Field label="Rôle"><Select value={roleFilter} onChange={(event) => setRoleFilter(event.target.value as UserResponse["role"] | "" | "ALL")} placeholder="Choisir un rôle"><option value="ALL">Tous</option>{ROLE_FILTERS.map((role) => <option key={role} value={role}>{role}</option>)}</Select></Field>
            <Field label="Statut"><Select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value as "" | "ALL" | "ENABLED" | "DISABLED")} placeholder="Choisir un statut"><option value="ALL">Tous</option><option value="ENABLED">Actifs</option><option value="DISABLED">Désactivés</option></Select></Field>
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
                    <div className="flex items-center gap-2">
                      {item.signature_key ? (
                        <Button
                          variant="outline"
                          size="icon-sm"
                          onClick={() => openSignature(item.id)}
                          aria-label="Voir la signature"
                          disabled={previewLoadingId === item.id}
                        >
                          <Eye className="size-4" />
                        </Button>
                      ) : (
                        <span className="text-xs text-sky-900/70">Aucune</span>
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
                  <TableCell colSpan={7} className="text-center text-sm text-sky-900/70">Aucun utilisateur ne correspond aux filtres.</TableCell>
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
            className="w-full max-w-lg rounded-lg border border-sky-300 bg-white p-4 shadow-xl"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="mb-3 flex items-center justify-between">
              <span className="text-sm font-medium text-sky-900">Signature</span>
              <button
                type="button"
                onClick={closeSignaturePreview}
                aria-label="Fermer"
                className="rounded-sm p-1 text-sky-700 hover:bg-sky-100"
              >
                <X className="size-4" />
              </button>
            </div>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={signaturePreview.url}
              alt="Signature utilisateur"
              className="h-64 w-full rounded border border-sky-200 bg-white object-contain"
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