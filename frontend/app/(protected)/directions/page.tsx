"use client";

import { useEffect, useState } from "react";

import { useAuth } from "@/components/auth-provider";
import { RoleGate } from "@/components/role-gate";
import { Badge } from "@/components/ui/badge";
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { apiClient } from "@/lib/http";
import type { DirectionResponse, PaginatedResponse } from "@/lib/backend-types";

type DirectionCreate = {
  name: string;
  code: string;
  description: string;
  director_id: string;
};

const EMPTY: DirectionCreate = {
  name: "",
  code: "",
  description: "",
  director_id: "",
};

export default function DirectionsPage() {
  return (
    <RoleGate roles={["ADMIN", "DRH"]}>
      <DirectionsContent />
    </RoleGate>
  );
}

function DirectionsContent() {
  const { user } = useAuth();
  const [items, setItems] = useState<DirectionResponse[]>([]);
  const [form, setForm] = useState<DirectionCreate>(EMPTY);
  const [loading, setLoading] = useState(true);

  const loadDirections = async () => {
    const response = await apiClient.get<PaginatedResponse<DirectionResponse>>(
      "/directions/",
      { params: { page: 1, page_size: 50 } },
    );
    setItems(response.data.data);
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadDirections().finally(() => setLoading(false));
  }, []);

  const createDirection = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await apiClient.post("/directions/", {
      name: form.name,
      code: form.code,
      description: form.description || null,
      director_id: form.director_id ? Number(form.director_id) : null,
    });
    setForm(EMPTY);
    await loadDirections();
  };

  const deleteDirection = async (id: number) => {
    if (!confirm("Supprimer cette direction ?")) return;
    await apiClient.delete(`/directions/${id}`);
    await loadDirections();
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardDescription>Référentiel RH</CardDescription>
          <CardTitle>Directions</CardTitle>
        </CardHeader>
        <CardContent>
          {user?.role === "ADMIN" && (
            <form
              className="grid gap-4 md:grid-cols-2 xl:grid-cols-4"
              onSubmit={createDirection}
            >
              <Field label="Nom">
                <Input
                  value={form.name}
                  onChange={(event) =>
                    setForm((current) => ({
                      ...current,
                      name: event.target.value,
                    }))
                  }
                />
              </Field>
              <Field label="Code">
                <Input
                  value={form.code}
                  onChange={(event) =>
                    setForm((current) => ({
                      ...current,
                      code: event.target.value,
                    }))
                  }
                />
              </Field>
              <Field label="Description">
                <Input
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
                  value={form.director_id}
                  onChange={(event) =>
                    setForm((current) => ({
                      ...current,
                      director_id: event.target.value,
                    }))
                  }
                />
              </Field>
              <div className="md:col-span-2 xl:col-span-4">
                <Button type="submit">Créer</Button>
              </div>
            </form>
          )}
          {user?.role !== "ADMIN" && (
            <p className="text-sm text-muted-foreground">
              Consultation uniquement pour ce rôle.
            </p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardDescription>
            {loading ? "Chargement…" : `${items.length} résultats`}
          </CardDescription>
          <CardTitle>Liste des directions</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Nom</TableHead>
                <TableHead>Code</TableHead>
                <TableHead>Directeur</TableHead>
                <TableHead />
              </TableRow>
            </TableHeader>
            <TableBody>
              {items.map((item) => (
                <TableRow key={item.id}>
                  <TableCell>{item.name}</TableCell>
                  <TableCell>
                    <Badge variant="secondary">{item.code}</Badge>
                  </TableCell>
                  <TableCell>{item.director_id ?? "-"}</TableCell>
                  <TableCell className="text-right">
                    <Button asChild variant="outline" size="sm">
                      <a href={`/directions/${item.id}`}>Ouvrir</a>
                    </Button>
                    {user?.role === "ADMIN" && (
                      <Button
                        variant="destructive"
                        size="sm"
                        className="ml-2"
                        onClick={() => deleteDirection(item.id)}
                      >
                        Supprimer
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
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
