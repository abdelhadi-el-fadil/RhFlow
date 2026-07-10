"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Users } from "lucide-react";

import { RoleGate } from "@/components/role-gate";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import type { UserResponse } from "@/lib/backend-types";
import { setFlashSuccess } from "@/lib/flash";
import { ApiHttpError, apiClient } from "@/lib/http";

type UserCreate = {
  email: string;
  password: string;
  full_name: string;
  gsm: string;
  role: UserResponse["role"];
};

const EMPTY_CREATE: UserCreate = { email: "", password: "", full_name: "", gsm: "", role: "DG" };

export default function NewUserPage() {
  return (
    <RoleGate roles={["ADMIN", "DRH"]}>
      <NewUserContent />
    </RoleGate>
  );
}

function NewUserContent() {
  const router = useRouter();
  const [form, setForm] = useState<UserCreate>(EMPTY_CREATE);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const createUser = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await apiClient.post("/users/", form);
      setFlashSuccess("Utilisateur créé avec succès.");
      router.push("/users");
    } catch (err) {
      setError(err instanceof ApiHttpError ? err.message : "Impossible de créer l'utilisateur.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card className="border-sky-300/70 bg-linear-to-br from-sky-200 via-blue-200 to-cyan-100">
      <CardHeader>
        <CardDescription className="text-sky-800">Administration</CardDescription>
        <CardTitle className="flex items-center gap-2 text-sky-950">
          <Users className="size-5 text-sky-800" />
          Créer un utilisateur
        </CardTitle>
      </CardHeader>
      <CardContent>
        {error && <p className="mb-4 text-sm text-destructive">{error}</p>}
        <form className="grid gap-4 md:grid-cols-2 xl:grid-cols-5" onSubmit={createUser}>
          <Field label="Email"><Input value={form.email} onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))} /></Field>
          <Field label="Mot de passe"><Input type="password" value={form.password} onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))} /></Field>
          <Field label="Nom complet"><Input value={form.full_name} onChange={(event) => setForm((current) => ({ ...current, full_name: event.target.value }))} /></Field>
          <Field label="Téléphone"><Input value={form.gsm} onChange={(event) => setForm((current) => ({ ...current, gsm: event.target.value }))} /></Field>
          <Field label="Rôle">
            <Select value={form.role} onChange={(event) => setForm((current) => ({ ...current, role: event.target.value as UserCreate["role"] }))}>
              <option value="ADMIN">ADMIN</option>
              <option value="DRH">DRH</option>
              <option value="DIRECTEUR">DIRECTEUR</option>
              <option value="DG">DG</option>
            </Select>
          </Field>
          <div className="md:col-span-2 xl:col-span-5 flex gap-2">
            <Button type="submit" disabled={saving}>{saving ? "Création..." : "Créer"}</Button>
            <Button type="button" variant="outline" onClick={() => router.push("/users")}>Annuler</Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      {children}
    </div>
  );
}
