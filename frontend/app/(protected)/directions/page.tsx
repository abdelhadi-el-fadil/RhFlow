"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Building2 } from "lucide-react";

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
import type { DirectionResponse, PaginatedResponse, UserResponse } from "@/lib/backend-types";

export default function DirectionsPage() {
  return (
    <RoleGate roles={["ADMIN", "DRH", "DIRECTEUR", "DG"]}>
      <DirectionsContent />
    </RoleGate>
  );
}

function DirectionsContent() {
  const { user } = useAuth();
  const [items, setItems] = useState<DirectionResponse[]>([]);
  const [users, setUsers] = useState<UserResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [directorFilter, setDirectorFilter] = useState("ALL");

  const loadDirections = async () => {
    const [directionsResponse, usersResponse] = await Promise.all([
      apiClient.get<PaginatedResponse<DirectionResponse>>("/directions/", { params: { page: 1, page_size: 50 } }),
      apiClient.get<PaginatedResponse<UserResponse>>("/users/", { params: { page: 1, page_size: 100 } }),
    ]);
    setItems(directionsResponse.data.data);
    setUsers(usersResponse.data.data);
  };

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
  }, []);

  const deleteDirection = async (id: number) => {
    if (!confirm("Supprimer cette direction ?")) return;
    setActionError(null);
    try {
      await apiClient.delete(`/directions/${id}`);
      await loadDirections();
    } catch (err) {
      setActionError(err instanceof ApiHttpError ? err.message : "Impossible de supprimer cette direction.");
    }
  };

  const canManageDirections = user?.role === "ADMIN" || user?.role === "DRH"
  const directorOptions = users.filter((item) => item.role === "DIRECTEUR" || item.role === "DG")
  const filteredItems = items.filter((item) => {
    const matchesSearch = search.trim() === "" || `${item.name} ${item.description ?? ""} ${item.director_name ?? ""}`.toLowerCase().includes(search.trim().toLowerCase())
    const matchesDirector = directorFilter === "ALL" || String(item.director_id ?? "") === directorFilter
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
          {actionError && <p className="mb-4 text-sm text-destructive">{actionError}</p>}
          <div className="mb-4 grid gap-4 md:grid-cols-2">
            <Field label="Recherche"><Input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Nom, description, directeur" /></Field>
            <Field label="Directeur"><Select value={directorFilter} onChange={(event) => setDirectorFilter(event.target.value)}><option value="ALL">Tous</option>{directorOptions.map((director) => <option key={director.id} value={director.id}>{director.full_name || director.email}</option>)}</Select></Field>
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