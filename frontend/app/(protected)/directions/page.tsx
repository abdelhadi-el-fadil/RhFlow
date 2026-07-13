"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { Building2 } from "lucide-react";
import { toast } from "sonner";

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
import { Select } from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ApiHttpError, apiClient } from "@/lib/http";
import type { DirectionResponse, PaginatedResponse } from "@/lib/backend-types";

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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [directorFilter, setDirectorFilter] = useState("");

  const canManageDirections = user?.role === "ADMIN" || user?.role === "DRH"

  const loadDirections = useCallback(async () => {
    const directionsResponse = await apiClient.get<PaginatedResponse<DirectionResponse>>("/directions/", { params: { page: 1, page_size: 50 } })
    setItems(directionsResponse.data.data)
  }, []);

  useEffect(() => {
    const run = async () => {
      try {
        setError(null);
        await loadDirections();
      } catch (err) {
        setError(err instanceof ApiHttpError ? err.message : "Impossible de charger les directions.");
      } finally {
        setLoading(false);
      }
    };

    void run();
  }, [loadDirections]);

  const deleteDirection = async (id: number) => {
    if (!confirm("Supprimer cette direction ?")) return;
    try {
      await apiClient.delete(`/directions/${id}`);
      await loadDirections();
      toast.success("Direction supprimée avec succès.");
    } catch (err) {
      toast.error(err instanceof ApiHttpError ? err.message : "Impossible de supprimer cette direction.");
    }
  };

  const clearFilters = () => {
    setSearch("");
    setDirectorFilter("");
  };

  const directorOptions = Array.from(
    new Map(
      items
        .filter((item): item is DirectionResponse & { director_id: number } => item.director_id !== null)
        .map((item) => [item.director_id, item.director_name ?? `Directeur #${item.director_id}`] as const),
    ).entries(),
  ).map(([id, name]) => ({ id, name }))
  const filteredItems = items.filter((item) => {
    const matchesSearch = search.trim() === "" || `${item.name} ${item.description ?? ""} ${item.director_name ?? ""}`.toLowerCase().includes(search.trim().toLowerCase())
    const matchesDirector = directorFilter === "" || directorFilter === "ALL" || String(item.director_id ?? "") === directorFilter
    return matchesSearch && matchesDirector
  })

  return (
    <div className="space-y-6">
      <Card className="border-sky-300/70 bg-linear-to-br from-sky-200 via-blue-200 to-cyan-100">
        <CardHeader className="flex flex-row items-start justify-between gap-4">
          <div>
          <CardDescription className="text-sky-800">
            {loading ? "Chargement…" : `${filteredItems.length} résultats`}
          </CardDescription>
          <CardTitle className="flex items-center gap-2 text-sky-950">
            <Building2 className="size-5 text-sky-800" />
            Directions
          </CardTitle>
          </div>
          {canManageDirections && (
            <Button asChild>
              <Link href="/directions/nouveau">Créer une direction</Link>
            </Button>
          )}
        </CardHeader>
        <CardContent>
          {!canManageDirections && (
            <p className="mb-4 text-sm text-sky-800/80">
              Consultation uniquement pour ce rôle.
            </p>
          )}
          {error && <p className="mb-4 text-sm text-destructive">{error}</p>}
          <div className="mb-4 flex flex-col gap-4 md:flex-row md:items-end">
            <div className="grid flex-1 gap-4 md:grid-cols-2">
              <Field label="Recherche"><Input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Nom, description, directeur" /></Field>
              <Field label="Directeur"><Select value={directorFilter} onChange={(event) => setDirectorFilter(event.target.value)} placeholder="Choisir un directeur"><option value="ALL">Tous</option>{directorOptions.map((director) => <option key={String(director.id)} value={String(director.id)}>{director.name}</option>)}</Select></Field>
            </div>
            <Button
              type="button"
              variant="ghost"
              onClick={clearFilters}
              className="bg-sky-500 text-white hover:bg-sky-700 hover:text-white md:self-end"
            >
              Effacer les filtres
            </Button>
          </div>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Nom</TableHead>
                <TableHead>Directeur</TableHead>
                <TableHead>Fiches de poste</TableHead>
                <TableHead />
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredItems.map((item) => (
                <TableRow key={item.id}>
                  <TableCell>{item.name}</TableCell>
                  <TableCell>{item.director_name ?? "-"}</TableCell>
                  <TableCell><Badge variant="secondary">{item.fiche_count}</Badge></TableCell>
                  <TableCell className="text-right">
                    <Button asChild variant="outline" size="sm">
                      <a href={`/directions/${item.id}`}>Ouvrir</a>
                    </Button>
                    {canManageDirections && (
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
              {filteredItems.length === 0 && (
                <TableRow>
                  <TableCell colSpan={4} className="text-center text-sm text-sky-900/70">Aucune direction ne correspond aux filtres.</TableCell>
                </TableRow>
              )}
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