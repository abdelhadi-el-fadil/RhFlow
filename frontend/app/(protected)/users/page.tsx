"use client"

import { useEffect, useState } from "react"
import { List, ShieldCheck, Users } from "lucide-react"

import { useAuth } from "@/components/auth-provider"
import { RoleGate } from "@/components/role-gate"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { apiClient } from "@/lib/http"
import { type PaginatedResponse, type UserResponse } from "@/lib/backend-types"

type UserCreate = {
  email: string
  password: string
  full_name: string
  gsm: string
  role: UserResponse["role"]
}

const EMPTY_CREATE: UserCreate = { email: "", password: "", full_name: "", gsm: "", role: "DG" }

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

  const loadUsers = async () => {
    const response = await apiClient.get<PaginatedResponse<UserResponse>>("/users/", { params: { page: 1, page_size: 50 } })
    setItems(response.data.data)
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadUsers().finally(() => setLoading(false))
  }, [])

  const createUser = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setSaving(true)
    try {
      await apiClient.post("/users/", form)
      setForm(EMPTY_CREATE)
      await loadUsers()
    } finally {
      setSaving(false)
    }
  }

  const deleteUser = async (userId: number) => {
    if (!confirm("Supprimer ce compte ?")) {
      return
    }

    await apiClient.delete(`/users/${userId}`)
    await loadUsers()
  }

  const startEdit = (item: UserResponse) => {
    setEditingId(item.id)
    setDraft(item)
  }

  const saveEdit = async () => {
    if (!draft) {
      return
    }

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
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardDescription>Administration</CardDescription>
          <CardTitle className="flex items-center gap-2"><Users className="size-5 text-indigo-700" />Utilisateurs</CardTitle>
        </CardHeader>
        <CardContent>
          {user?.role === "ADMIN" && (
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
          {user?.role !== "ADMIN" && <p className="text-sm text-muted-foreground">Consultation uniquement pour ce rôle.</p>}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardDescription>{loading ? "Chargement…" : `${items.length} résultats`}</CardDescription>
          <CardTitle className="flex items-center gap-2"><List className="size-5 text-indigo-700" />Liste</CardTitle>
        </CardHeader>
        <CardContent>
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
              {items.map((item) => (
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
                    {user?.role === "ADMIN" && (
                      <>
                        {editingId === item.id ? (
                          <Button size="sm" onClick={saveEdit}>Sauvegarder</Button>
                        ) : (
                          <Button variant="outline" size="sm" onClick={() => startEdit(item)}>Modifier</Button>
                        )}
                        <Button variant="destructive" size="sm" className="ml-2" onClick={() => deleteUser(item.id)}>Supprimer</Button>
                      </>
                    )}
                  </TableCell>
                </TableRow>
              ))}
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