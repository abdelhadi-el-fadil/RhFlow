"use client";

import { use, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

import { RoleGate } from "@/components/role-gate";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { ApiHttpError, apiClient } from "@/lib/http";
import type { ApiResponse, DirectionResponse, PaginatedResponse, UserResponse } from "@/lib/backend-types";
import { useAuth } from "@/components/auth-provider";

export default function DirectionDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const directionId = Number(resolvedParams.id);

  if (Number.isNaN(directionId)) {
    return (
      <RoleGate roles={["ADMIN", "DRH"]}>
        <Card className="premium-panel">
          <CardContent className="premium-copy">Identifiant direction invalide.</CardContent>
        </Card>
      </RoleGate>
    );
  }

  return (
    <RoleGate roles={["ADMIN", "DRH"]}>
      <DirectionDetail id={directionId} />
    </RoleGate>
  );
}

function DirectionDetail({ id }: { id: number }) {
  const router = useRouter();
  const { user } = useAuth();
  const [item, setItem] = useState<DirectionResponse | null>(null);
  const [users, setUsers] = useState<UserResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const [saveError, setSaveError] = useState<string | null>(null);
  const [form, setForm] = useState({
    name: "",
    description: "",
    director_id: "",
  });

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const [directionResponse, usersResponse] = await Promise.all([
          apiClient.get<ApiResponse<DirectionResponse>>(`/directions/${id}`),
          apiClient.get<PaginatedResponse<UserResponse>>("/users/", { params: { page: 1, page_size: 100 } }),
        ]);
        if (cancelled) {
          return;
        }

        setItem(directionResponse.data.data);
        setUsers(usersResponse.data.data);
        setForm({
          name: directionResponse.data.data.name,
          description: directionResponse.data.data.description ?? "",
          director_id: directionResponse.data.data.director_id?.toString() ?? "",
        });
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof ApiHttpError
              ? err.message
              : "Impossible de charger cette direction.",
          );
          setItem(null);
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    };

    void load();

    return () => {
      cancelled = true;
    };
  }, [id]);

  const save = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSaving(true);
    setSaveError(null);
    try {
      const response = await apiClient.put<ApiResponse<DirectionResponse>>(
        `/directions/${id}`,
        {
          name: form.name,
          description: form.description || null,
          director_id: form.director_id ? Number(form.director_id) : null,
        },
      );
      setItem(response.data.data);
      toast.success("Direction sauvegardée avec succès.");
      router.push("/directions");
    } catch (err) {
      const message =
        err instanceof ApiHttpError
          ? err.message
          : "Impossible de sauvegarder cette direction.";
      setSaveError(message);
      toast.error(message);
    } finally {
      setSaving(false);
    }
  };

  if (isLoading) {
    return (
      <Card className="premium-panel">
        <CardContent className="premium-copy">Chargement…</CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="premium-panel">
        <CardContent className="premium-copy">{error}</CardContent>
      </Card>
    );
  }

  if (!item) {
    return (
      <Card className="premium-panel">
        <CardContent className="premium-subtle">Direction introuvable.</CardContent>
      </Card>
    );
  }

  const canEdit = user?.role === "ADMIN" || user?.role === "DRH";
  const directorOptions = users.filter((entry) => entry.role === "DIRECTEUR" || entry.role === "DG");

  return (
    <Card className="premium-panel premium-lift border-stone-300/70 bg-white/90">
      <CardHeader>
        <CardDescription className="premium-copy">{item.director_name ? `Directeur: ${item.director_name}` : "Aucun directeur assigné"}</CardDescription>
        <CardTitle className="premium-title">{item.name}</CardTitle>
      </CardHeader>
      <CardContent>
        <form className="grid gap-4 md:grid-cols-2" onSubmit={save}>
          <Field label="Nom">
            <Input
              disabled={!canEdit}
              value={form.name}
              onChange={(event) =>
                setForm((current) => ({ ...current, name: event.target.value }))
              }
            />
          </Field>
          <Field label="Description">
            <Input
              disabled={!canEdit}
              value={form.description}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  description: event.target.value,
                }))
              }
            />
          </Field>
          <Field label="Directeur">
            <Select
              disabled={!canEdit}
              value={form.director_id}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  director_id: event.target.value,
                }))
              }
            >
              <option value="">Aucun</option>
              {directorOptions.map((director) => <option key={director.id} value={director.id}>{director.full_name || director.email}</option>)}
            </Select>
          </Field>
          <div className="md:col-span-2 rounded-lg border border-stone-300/70 bg-stone-50/70 p-4 text-sm text-slate-900">
            Nombre de fiches de poste liées: <span className="font-semibold">{item.fiche_count}</span>
          </div>
          {saveError && (
            <p className="md:col-span-2 text-sm text-destructive">
              {saveError}
            </p>
          )}
          <div className="md:col-span-2">
            {canEdit && (
              <Button type="submit" disabled={saving}>
                {saving ? "Sauvegarde…" : "Sauvegarder"}
              </Button>
            )}
          </div>
        </form>
      </CardContent>
    </Card>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      {children}
    </div>
  );
}