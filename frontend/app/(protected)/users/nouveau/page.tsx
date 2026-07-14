"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Users } from "lucide-react";

import { RoleGate } from "@/components/role-gate";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import type { UserResponse } from "@/lib/backend-types";
import { toast } from "sonner";
import { ApiHttpError, apiClient } from "@/lib/http";

type UserCreate = {
  email: string;
  password: string;
  full_name: string;
  gsm: string;
  role: UserResponse["role"] | "";
};

type FieldErrors = Partial<Record<keyof UserCreate, string>>;

const EMPTY_CREATE: UserCreate = {
  email: "",
  password: "",
  full_name: "",
  gsm: "",
  role: "",
};

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const GSM_PATTERN = /^[0-9+\s-]{6,}$/;

function validate(form: UserCreate): FieldErrors {
  const errors: FieldErrors = {};

  if (!form.email.trim()) {
    errors.email = "L'email est requis.";
  } else if (!EMAIL_PATTERN.test(form.email.trim())) {
    errors.email = "Format d'email invalide.";
  }

  if (!form.password) {
    errors.password = "Le mot de passe est requis.";
  } else if (form.password.length < 8) {
    errors.password = "Le mot de passe doit contenir au moins 8 caractères.";
  }

  if (!form.full_name.trim()) {
    errors.full_name = "Le nom complet est requis.";
  }

  if (!form.gsm.trim()) {
    errors.gsm = "Le téléphone est requis.";
  } else if (!GSM_PATTERN.test(form.gsm.trim())) {
    errors.gsm = "Format de téléphone invalide.";
  }

  if (!form.role) {
    errors.role = "Le rôle est requis.";
  }

  return errors;
}

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
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});

  const updateField = <K extends keyof UserCreate>(
    key: K,
    value: UserCreate[K],
  ) => {
    setForm((current) => ({ ...current, [key]: value }));
    setFieldErrors((current) => {
      if (!current[key]) return current;
      const next = { ...current };
      delete next[key];
      return next;
    });
  };

  const createUser = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    const errors = validate(form);
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) {
      return;
    }

    setSaving(true);
    try {
      await apiClient.post("/users/", {
        ...form,
        role: form.role as UserResponse["role"],
      });
      toast.success("Utilisateur créé avec succès.", { duration: 3000 });
      router.push("/users");
    } catch (err) {
      setError(
        err instanceof ApiHttpError
          ? err.message
          : "Impossible de créer l'utilisateur.",
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card className="premium-panel premium-lift border-amber-200/65 bg-gradient-to-br from-stone-50 via-amber-50 to-teal-50">
      <CardHeader>
        <CardDescription className="premium-copy">
          Administration
        </CardDescription>
        <CardTitle className="premium-title flex items-center gap-2">
          <Users className="size-5 text-teal-700" />
          Créer un utilisateur
        </CardTitle>
      </CardHeader>
      <CardContent>
        {error && <p className="mb-4 text-sm text-destructive">{error}</p>}
        <form
          className="grid gap-4 md:grid-cols-2 xl:grid-cols-5"
          onSubmit={createUser}
          noValidate
        >
          <Field label="Email" error={fieldErrors.email}>
            <Input
              value={form.email}
              onChange={(event) => updateField("email", event.target.value)}
              aria-invalid={Boolean(fieldErrors.email)}
            />
          </Field>
          <Field label="Mot de passe" error={fieldErrors.password}>
            <Input
              type="password"
              value={form.password}
              onChange={(event) => updateField("password", event.target.value)}
              aria-invalid={Boolean(fieldErrors.password)}
            />
          </Field>
          <Field label="Nom complet" error={fieldErrors.full_name}>
            <Input
              value={form.full_name}
              onChange={(event) => updateField("full_name", event.target.value)}
              aria-invalid={Boolean(fieldErrors.full_name)}
            />
          </Field>
          <Field label="Téléphone" error={fieldErrors.gsm}>
            <Input
              value={form.gsm}
              onChange={(event) => updateField("gsm", event.target.value)}
              aria-invalid={Boolean(fieldErrors.gsm)}
            />
          </Field>
          <Field label="Rôle" error={fieldErrors.role}>
            <Select
              value={form.role}
              onChange={(event) =>
                updateField("role", event.target.value as UserCreate["role"])
              }
              aria-invalid={Boolean(fieldErrors.role)}
              placeholder="Choisir un rôle"
            >
              <option value="ADMIN">ADMIN</option>
              <option value="DRH">DRH</option>
              <option value="DIRECTEUR">DIRECTEUR</option>
              <option value="DG">DG</option>
            </Select>
          </Field>
          <div className="md:col-span-2 xl:col-span-5 flex gap-2">
            <Button type="submit" disabled={saving}>
              {saving ? "Création..." : "Créer"}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => router.push("/users")}
            >
              Annuler
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}

function Field({
  label,
  error,
  children,
}: {
  label: string;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      {children}
      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  );
}
