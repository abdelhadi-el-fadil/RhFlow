"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Building2 } from "lucide-react";
import { toast } from "sonner";

import { RoleGate } from "@/components/role-gate";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import type { PaginatedResponse, UserResponse } from "@/lib/backend-types";
import { ApiHttpError, apiClient } from "@/lib/http";

type DirectionCreate = {
  name: string;
  description: string;
  director_id: string;
};

type FieldErrors = Partial<Record<keyof DirectionCreate, string>>;

const EMPTY: DirectionCreate = {
  name: "",
  description: "",
  director_id: "",
};

function validate(form: DirectionCreate): FieldErrors {
  const errors: FieldErrors = {};

  if (!form.name.trim()) {
    errors.name = "Le nom est requis.";
  } else if (form.name.trim().length < 2) {
    errors.name = "Le nom doit contenir au moins 2 caractères.";
  }

  if (form.description.trim().length > 500) {
    errors.description = "La description ne doit pas dépasser 500 caractères.";
  }

  if (!form.director_id) {
    errors.director_id = "Le directeur est requis.";
  }

  return errors;
}

export default function NewDirectionPage() {
  return (
    <RoleGate roles={["ADMIN", "DRH"]}>
      <NewDirectionContent />
    </RoleGate>
  );
}

function NewDirectionContent() {
  const router = useRouter();
  const [users, setUsers] = useState<UserResponse[]>([]);
  const [form, setForm] = useState<DirectionCreate>(EMPTY);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});

  useEffect(() => {
    const run = async () => {
      setLoading(true);
      setError(null);
      try {
        const usersResponse = await apiClient.get<PaginatedResponse<UserResponse>>("/users/", { params: { page: 1, page_size: 100 } });
        setUsers(usersResponse.data.data);
      } catch (err) {
        setError(err instanceof ApiHttpError ? err.message : "Impossible de charger les directeurs.");
      } finally {
        setLoading(false);
      }
    };

    void run();
  }, []);

  const updateField = <K extends keyof DirectionCreate>(key: K, value: DirectionCreate[K]) => {
    setForm((current) => ({ ...current, [key]: value }));
    setFieldErrors((current) => {
      if (!current[key]) return current;
      const next = { ...current };
      delete next[key];
      return next;
    });
  };

  const createDirection = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    const errors = validate(form);
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) {
      return;
    }

    setSaving(true);
    try {
      await apiClient.post("/directions/", {
        name: form.name,
        description: form.description || null,
        director_id: Number(form.director_id),
      });
      toast.success("Direction créée avec succès.");
      router.push("/directions");
      router.refresh();
    } catch (err) {
      const message = err instanceof ApiHttpError ? err.message : "Impossible de créer la direction.";
      setError(message);
      toast.error(message);
    } finally {
      setSaving(false);
    }
  };

  const directorOptions = users.filter((item) => item.role === "DIRECTEUR" || item.role === "DG");

  return (
    <Card className="border-sky-300/70 bg-linear-to-br from-sky-200 via-blue-200 to-cyan-100">
      <CardHeader>
        <CardDescription className="text-sky-800">Référentiel RH</CardDescription>
        <CardTitle className="flex items-center gap-2 text-sky-950">
          <Building2 className="size-5 text-sky-800" />
          Créer une direction
        </CardTitle>
      </CardHeader>
      <CardContent>
        {error && <p className="mb-4 text-sm text-destructive">{error}</p>}
        {loading && <p className="mb-4 text-sm text-sky-800">Chargement des directeurs...</p>}
        <form className="grid gap-4 md:grid-cols-2 xl:grid-cols-3" onSubmit={createDirection} noValidate>
          <Field label="Nom" error={fieldErrors.name}>
            <Input
              value={form.name}
              onChange={(event) => updateField("name", event.target.value)}
              aria-invalid={Boolean(fieldErrors.name)}
            />
          </Field>
          <Field label="Description" error={fieldErrors.description}>
            <Input
              value={form.description}
              onChange={(event) => updateField("description", event.target.value)}
              aria-invalid={Boolean(fieldErrors.description)}
            />
          </Field>
          <Field label="Directeur" error={fieldErrors.director_id}>
            <Select
              value={form.director_id}
              onChange={(event) => updateField("director_id", event.target.value)}
              placeholder="Choisir un directeur"
              aria-invalid={Boolean(fieldErrors.director_id)}
            >
              <option value=""></option>
              {directorOptions.map((director) => <option key={director.id} value={director.id}>{director.full_name || director.email}</option>)}
            </Select>
          </Field>
          <div className="md:col-span-2 xl:col-span-3 flex gap-2">
            <Button type="submit" disabled={saving}>{saving ? "Création..." : "Créer"}</Button>
            <Button type="button" variant="outline" onClick={() => router.push("/directions")}>Annuler</Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}

function Field({ label, error, children }: { label: string; error?: string; children: React.ReactNode }) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      {children}
      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  );
}