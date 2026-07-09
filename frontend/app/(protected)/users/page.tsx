"use client"

import { useEffect, useState } from "react"
import { List, Users } from "lucide-react"

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
import { type PaginatedResponse, type UserResponse } from "@/lib/backend-types"

type UserCreate = {
  email: string
  password: string
  full_name: string
  gsm: string
  role: UserResponse["role"]
}

const EMPTY_CREATE: UserCreate = { email: "", password: "", full_name: "", gsm: "", role: "DG" }
const ROLE_FILTERS: Array<UserResponse["role"] | "ALL"> = ["ALL", "ADMIN", "DRH", "DIRECTEUR", "DG"]

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
  const [form, setForm] = useState<UserCreate>(EMPTY_CREATE)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [draft, setDraft] = useState<UserResponse | null>(null)
  const [search, setSearch] = useState("")
  const [roleFilter, setRoleFilter] = useState<(typeof ROLE_FILTERS)[number]>("ALL")
  const [statusFilter, setStatusFilter] = useState<"ALL" | "ENABLED" | "DISABLED">("ALL")
  const [error, setError] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)

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

  const createUser = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setSaving(true)
    setActionError(null)
    try {
      await apiClient.post("/users/", form)
      setForm(EMPTY_CREATE)
      await loadUsers()
    } catch (err) {
      setActionError(err instanceof ApiHttpError ? err.message : "Impossible de créer l'utilisateur.")
    } finally {
      setSaving(false)
    }
  }

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
      setEditingId(null)
      setDraft(null)
      await loadUsers()
    } catch (err) {
      setActionError(err instanceof ApiHttpError ? err.message : "Impossible de modifier cet utilisateur.")
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

  const filteredItems = items.filter((item) => {
    const haystack = `${item.email} ${item.full_name ?? ""} ${item.gsm ?? ""}`.toLowerCase()
    const matchesSearch = search.trim() === "" || haystack.includes(search.trim().toLowerCase())
    const matchesRole = roleFilter === "ALL" || item.role === roleFilter
    const matchesStatus = statusFilter === "ALL" || (statusFilter === "ENABLED" ? item.enabled : !item.enabled)
    return matchesSearch && matchesRole && matchesStatus
  })

  return (
    <div className="space-y-6">
      <Card className="border-sky-300/70 bg-linear-to-br from-sky-200 via-blue-200 to-cyan-100">
        <CardHeader>
          <CardDescription className="text-sky-800">Administration</CardDescription>
          <CardTitle className="flex items-center gap-2 text-sky-950">
            <Users className="size-5 text-sky-800" />
            Utilisateurs
          </CardTitle>
        </CardHeader>
        <CardContent>
          {actionError && <p className="mb-4 text-sm text-destructive">{actionError}</p>}
          {(user?.role === "ADMIN" || user?.role === "DRH") && (
            <form className="grid gap-4 md:grid-cols-2 xl:grid-cols-5" onSubmit={createUser}>
              <Field label="Email"><Input value={form.email} onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))} /></Field>
              <Field label="Mot de passe"><Input type="password" value={form.password} onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))} /></Field>
              <Field label="Nom complet"><Input value={form.full_name} onChange={(event) => setForm((current) => ({ ...current, full_name: event.target.value }))} /></Field>
              <Field label="Téléphone"><Input value={form.gsm} onChange={(event) => setForm((current) => ({ ...current, gsm: event.target.value }))} /></Field>
              <Field label="Rôle"><Select value={form.role} onChange={(event) => setForm((current) => ({ ...current, role: event.target.value as UserCreate["role"] }))}><option value="ADMIN">ADMIN</option><option value="DRH">DRH</option><option value="DIRECTEUR">DIRECTEUR</option><option value="DG">DG</option></Select></Field>
              <div className="md:col-span-2 xl:col-span-5">
                <Button type="submit" disabled={saving}>{saving ? "Création…" : "Créer"}</Button>
              </div>
            </form>
          )}
          {user?.role !== "ADMIN" && user?.role !== "DRH" && <p className="text-sm text-sky-800/80">Consultation uniquement pour ce rôle.</p>}
        </CardContent>
      </Card>

      <Card className="border-sky-300/70 bg-linear-to-br from-sky-200 via-blue-200 to-cyan-100">
        <CardHeader>
          <CardDescription className="text-sky-800">{loading ? "Chargement…" : `${filteredItems.length} résultats`}</CardDescription>
          <CardTitle className="flex items-center gap-2 text-sky-950">
            <List className="size-5 text-sky-800" />
            Liste
          </CardTitle>
        </CardHeader>
        <CardContent>
          {error && <p className="mb-4 text-sm text-destructive">{error}</p>}
          {actionError && <p className="mb-4 text-sm text-destructive">{actionError}</p>}
          <div className="mb-4 grid gap-4 md:grid-cols-3">
            <Field label="Recherche"><Input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Email, nom, téléphone" /></Field>
            <Field label="Rôle"><Select value={roleFilter} onChange={(event) => setRoleFilter(event.target.value as (typeof ROLE_FILTERS)[number])}>{ROLE_FILTERS.map((role) => <option key={role} value={role}>{role === "ALL" ? "Tous" : role}</option>)}</Select></Field>
            <Field label="Statut"><Select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value as "ALL" | "ENABLED" | "DISABLED")}><option value="ALL">Tous</option><option value="ENABLED">Actifs</option><option value="DISABLED">Désactivés</option></Select></Field>
          </div>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Email</TableHead>
                <TableHead>Nom</TableHead>
                <TableHead>Téléphone</TableHead>
                <TableHead>Rôle</TableHead>
                <TableHead>Statut</TableHead>
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
                  <TableCell className="text-right">
                    {(user?.role === "ADMIN" || user?.role === "DRH") && (
                      <>
                        {editingId === item.id ? (
                          <Button size="sm" onClick={saveEdit}>Sauvegarder</Button>
                        ) : (
                          <Button variant="outline" size="sm" onClick={() => startEdit(item)}>Modifier</Button>
                        )}
                        <Button variant={item.enabled ? "secondary" : "default"} size="sm" className="ml-2" onClick={() => toggleUserEnabled(item)}>{item.enabled ? "Désactiver" : "Réactiver"}</Button>
                        <Button variant="destructive" size="sm" className="ml-2" onClick={() => deleteUser(item.id)}>Supprimer</Button>
                      </>
                    )}
                  </TableCell>
                </TableRow>
              ))}
              {filteredItems.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} className="text-center text-sm text-sky-900/70">Aucun utilisateur ne correspond aux filtres.</TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
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