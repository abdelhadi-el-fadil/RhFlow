"use client";

import { use, useEffect, useState } from "react";

import { RoleGate } from "@/components/role-gate";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiHttpError, apiClient } from "@/lib/http";
import type { ApiResponse, DirectionResponse } from "@/lib/backend-types";
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
        <Card>
          <CardContent>Identifiant direction invalide.</CardContent>
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
  const { user } = useAuth();
  const [item, setItem] = useState<DirectionResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const [saveError, setSaveError] = useState<string | null>(null);
  const [form, setForm] = useState({
    name: "",
    code: "",
    description: "",
    director_id: "",
  });

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await apiClient.get<ApiResponse<DirectionResponse>>(
          `/directions/${id}`,
        );
        if (cancelled) {
          return;
        }

        setItem(response.data.data);
        setForm({
          name: response.data.data.name,
          code: response.data.data.code,
          description: response.data.data.description ?? "",
          director_id: response.data.data.director_id?.toString() ?? "",
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
          code: form.code,
          description: form.description || null,
          director_id: form.director_id ? Number(form.director_id) : null,
        },
      );
      setItem(response.data.data);
    } catch (err) {
      setSaveError(
        err instanceof ApiHttpError
          ? err.message
          : "Impossible de sauvegarder cette direction.",
      );
    } finally {
      setSaving(false);
    }
  };

  if (isLoading) {
    return (
      <Card>
        <CardContent>Chargement…</CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent>{error}</CardContent>
      </Card>
    );
  }

  if (!item) {
    return (
      <Card>
        <CardContent>Direction introuvable.</CardContent>
      </Card>
    );
  }

  const canEdit = user?.role === "ADMIN";

  return (
    <Card>
      <CardHeader>
        <CardTitle>Direction #{id}</CardTitle>
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
          <Field label="Code">
            <Input
              disabled={!canEdit}
              value={form.code}
              onChange={(event) =>
                setForm((current) => ({ ...current, code: event.target.value }))
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
          <Field label="Director ID">
            <Input
              disabled={!canEdit}
              value={form.director_id}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  director_id: event.target.value,
                }))
              }
            />
          </Field>
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
