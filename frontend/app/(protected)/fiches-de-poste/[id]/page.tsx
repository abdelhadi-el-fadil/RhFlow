"use client";

import { use, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/components/auth-provider";
import { RoleGate } from "@/components/role-gate";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import type { ApiResponse, DirectionResponse, FicheDePosteResponse, PaginatedResponse } from "@/lib/backend-types";
import { setFlashSuccess } from "@/lib/flash";
import { ApiHttpError, apiClient } from "@/lib/http";
import { badgeVariantFromFicheStatus } from "@/lib/status-labels";

const EXPERIENCE_LEVELS = [
  { value: "0", label: "0 an (aucune expérience)" },
  { value: "1", label: "1 an" },
  { value: "2", label: "2 ans" },
  { value: "3", label: "3 ans" },
  { value: "4", label: "4 ans" },
  { value: "5", label: "5 ans" },
  { value: "6", label: "6 ans" },
  { value: "7", label: "7 ans" },
  { value: "8", label: "8 ans" },
  { value: "9", label: "9 ans" },
  { value: "10+", label: "10+ ans" },
];
const EDUCATION_LEVELS = ["Bac", "Bac+2", "Bac+3", "Bac+5", "Doctorat"];

export default function FicheDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const ficheId = Number(resolvedParams.id);

  if (Number.isNaN(ficheId)) {
    return (
      <RoleGate roles={["ADMIN", "DRH", "DIRECTEUR", "DG"]}>
        <Card>
          <CardContent>Identifiant fiche invalide.</CardContent>
        </Card>
      </RoleGate>
    );
  }

  return (
    <RoleGate roles={["ADMIN", "DRH", "DIRECTEUR", "DG"]}>
      <FicheDetail id={ficheId} />
    </RoleGate>
  );
}

function FicheDetail({ id }: { id: number }) {
  const router = useRouter();
  const { user } = useAuth();
  const [item, setItem] = useState<FicheDePosteResponse | null>(null);
  const [directions, setDirections] = useState<DirectionResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [form, setForm] = useState({
    title: "",
    description: "",
    missions: "",
    required_skills: "",
    experience_level: "0",
    direction_id: "",
    formation_domain: "",
    education_level: "",
    technical_skills: "",
    managerial_skills: "",
  });

  const hydrate = (fiche: FicheDePosteResponse) => {
    setItem(fiche);
    setForm({
      title: fiche.title,
      description: fiche.description,
      missions: fiche.missions,
      required_skills: fiche.required_skills,
      experience_level: fiche.experience_level.split(" ")[0] ?? "0",
      direction_id: fiche.direction_id.toString(),
      formation_domain: fiche.formation_domain ?? "",
      education_level: fiche.education_level ?? "",
      technical_skills: fiche.technical_skills ?? "",
      managerial_skills: fiche.managerial_skills ?? "",
    });
  };

  const refresh = async () => {
    const [ficheResponse, directionsResponse] = await Promise.all([
      apiClient.get<ApiResponse<FicheDePosteResponse>>(`/fiches-de-poste/${id}`),
      apiClient.get<PaginatedResponse<DirectionResponse>>("/directions/", { params: { page: 1, page_size: 100 } }),
    ]);

    hydrate(ficheResponse.data.data);
    setDirections(directionsResponse.data.data);
  };

  useEffect(() => {
    let cancelled = false;

    const run = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const [ficheResponse, directionsResponse] = await Promise.all([
          apiClient.get<ApiResponse<FicheDePosteResponse>>(`/fiches-de-poste/${id}`),
          apiClient.get<PaginatedResponse<DirectionResponse>>("/directions/", { params: { page: 1, page_size: 100 } }),
        ]);
        if (cancelled) {
          return;
        }

        hydrate(ficheResponse.data.data);
        setDirections(directionsResponse.data.data);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiHttpError ? err.message : "Impossible de charger cette fiche.");
          setItem(null);
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    };

    void run();

    return () => {
      cancelled = true;
    };
  }, [id]);

  const save = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setActionError(null);
    try {
      await apiClient.put(`/fiches-de-poste/${id}`, {
        ...form,
        direction_id: Number(form.direction_id),
        experience_level: `${form.experience_level} an${form.experience_level === "0" || form.experience_level === "1" ? "" : "s"}`,
      });
      setFlashSuccess("Fiche de poste sauvegardée avec succès.");
      router.push("/fiches-de-poste");
    } catch (err) {
      setActionError(err instanceof ApiHttpError ? err.message : "Impossible de sauvegarder cette fiche.");
    }
  };

  if (isLoading) return <Card><CardContent>Chargement...</CardContent></Card>;
  if (error) return <Card><CardContent>{error}</CardContent></Card>;
  if (!item) return <Card><CardContent>Fiche introuvable.</CardContent></Card>;

  const canAdminEdit = user?.role === "ADMIN" || user?.role === "DRH";
  const directeurCanEdit = user?.role === "DIRECTEUR" && directions.find((direction) => direction.id === item.direction_id)?.director_id === user.id;
  const editable = canAdminEdit || Boolean(directeurCanEdit);
  const canValidate = (user?.role === "DRH" || user?.role === "ADMIN") && item.status === "DRAFT";
  const canArchive = (user?.role === "DRH" || user?.role === "ADMIN") && item.status === "VALIDATED";
  const editableDirections = user?.role === "DIRECTEUR"
    ? directions.filter((direction) => direction.director_id === user.id)
    : directions;

  return (
    <Card>
      <CardHeader><CardTitle>{item.title} <Badge variant={badgeVariantFromFicheStatus(item.status)}>{item.status}</Badge></CardTitle></CardHeader>
      <CardContent>
        {actionError && <p className="mb-4 text-sm text-destructive">{actionError}</p>}
        <form className="grid gap-4 md:grid-cols-2" onSubmit={save}>
          <Field label="Intitulé"><Input disabled={!editable} value={form.title} onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))} /></Field>
          <Field label="Direction"><Select disabled={!editable} value={form.direction_id} onChange={(event) => setForm((current) => ({ ...current, direction_id: event.target.value }))}>{editableDirections.map((direction) => <option key={direction.id} value={direction.id}>{direction.name}</option>)}</Select></Field>
          <Field label="Description"><Textarea disabled={!editable} value={form.description} onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))} /></Field>
          <Field label="Missions"><Textarea disabled={!editable} value={form.missions} onChange={(event) => setForm((current) => ({ ...current, missions: event.target.value }))} /></Field>
          <Field label="Compétences requises"><Textarea disabled={!editable} value={form.required_skills} onChange={(event) => setForm((current) => ({ ...current, required_skills: event.target.value }))} /></Field>
          <Field label="Années d'expérience"><Select disabled={!editable} value={form.experience_level} onChange={(event) => setForm((current) => ({ ...current, experience_level: event.target.value }))}>{EXPERIENCE_LEVELS.map((level) => <option key={level.value} value={level.value}>{level.label}</option>)}</Select></Field>
          <Field label="Domaine de formation"><Input disabled={!editable} value={form.formation_domain} onChange={(event) => setForm((current) => ({ ...current, formation_domain: event.target.value }))} /></Field>
          <Field label="Niveau d'études"><Select disabled={!editable} value={form.education_level} onChange={(event) => setForm((current) => ({ ...current, education_level: event.target.value }))}>{EDUCATION_LEVELS.map((level) => <option key={level} value={level}>{level}</option>)}</Select></Field>
          <Field label="Compétences techniques"><Textarea disabled={!editable} value={form.technical_skills} onChange={(event) => setForm((current) => ({ ...current, technical_skills: event.target.value }))} /></Field>
          <Field label="Compétences managériales"><Textarea disabled={!editable} value={form.managerial_skills} onChange={(event) => setForm((current) => ({ ...current, managerial_skills: event.target.value }))} /></Field>
          <div className="md:col-span-2 flex gap-2">
            {editable && <Button type="submit">Sauvegarder</Button>}
            {canValidate && <Button type="button" onClick={async () => {
              setActionError(null);
              try {
                await apiClient.patch(`/fiches-de-poste/${id}/valider`);
                await refresh();
              } catch (err) {
                setActionError(err instanceof ApiHttpError ? err.message : "Impossible de valider cette fiche.");
              }
            }}>Valider</Button>}
            {canArchive && <Button type="button" variant="secondary" onClick={async () => {
              setActionError(null);
              try {
                await apiClient.patch(`/fiches-de-poste/${id}/archiver`);
                await refresh();
              } catch (err) {
                setActionError(err instanceof ApiHttpError ? err.message : "Impossible d'archiver cette fiche.");
              }
            }}>Archiver</Button>}
            {editable && <Button type="button" variant="destructive" onClick={async () => {
              if (!confirm("Supprimer cette fiche de poste ?")) {
                return;
              }
              setActionError(null);
              try {
                await apiClient.delete(`/fiches-de-poste/${id}`);
                window.location.href = "/fiches-de-poste";
              } catch (err) {
                setActionError(err instanceof ApiHttpError ? err.message : "Impossible de supprimer cette fiche.");
              }
            }}>Supprimer</Button>}
          </div>
        </form>
      </CardContent>
    </Card>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <div className="space-y-2"><Label>{label}</Label>{children}</div>;
}
