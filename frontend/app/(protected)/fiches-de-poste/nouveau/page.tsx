"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { FileText } from "lucide-react";

import { useAuth } from "@/components/auth-provider";
import { RoleGate } from "@/components/role-gate";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import type { DirectionResponse, PaginatedResponse } from "@/lib/backend-types";
import { setFlashSuccess } from "@/lib/flash";
import { ApiHttpError, apiClient } from "@/lib/http";

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

export default function NewFichePage() {
  return (
    <RoleGate roles={["ADMIN", "DRH", "DIRECTEUR"]}>
      <NewFicheContent />
    </RoleGate>
  );
}

function NewFicheContent() {
  const router = useRouter();
  const { user } = useAuth();
  const [directions, setDirections] = useState<DirectionResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({ title: "", description: "", missions: "", required_skills: "", experience_level: "0", direction_id: "", formation_domain: "", education_level: "", technical_skills: "", managerial_skills: "" });

  useEffect(() => {
    const run = async () => {
      setLoading(true);
      setError(null);
      try {
        const directionsRes = await apiClient.get<PaginatedResponse<DirectionResponse>>("/directions/", { params: { page: 1, page_size: 100 } });
        setDirections(directionsRes.data.data);
      } catch (err) {
        setError(err instanceof ApiHttpError ? err.message : "Impossible de charger les directions.");
      } finally {
        setLoading(false);
      }
    };

    void run();
  }, []);

  const availableDirections = useMemo(() => {
    if (user?.role === "DIRECTEUR") {
      return directions.filter((direction) => direction.director_id === user.id);
    }
    return directions;
  }, [directions, user]);

  const createFiche = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await apiClient.post("/fiches-de-poste/", {
        ...form,
        direction_id: Number(form.direction_id),
        experience_level: `${form.experience_level} an${form.experience_level === "0" || form.experience_level === "1" ? "" : "s"}`,
      });
      setFlashSuccess("Fiche de poste créée avec succès.");
      router.push("/fiches-de-poste");
    } catch (err) {
      setError(err instanceof ApiHttpError ? err.message : "Impossible de créer la fiche de poste.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card className="border-sky-300/70 bg-linear-to-br from-sky-200 via-blue-200 to-cyan-100">
      <CardHeader>
        <CardDescription className="text-sky-800">Créer</CardDescription>
        <CardTitle className="flex items-center gap-2 text-sky-950">
          <FileText className="size-5 text-sky-800" />
          Nouvelle fiche de poste
        </CardTitle>
      </CardHeader>
      <CardContent>
        {error && <p className="mb-4 text-sm text-destructive">{error}</p>}
        {loading && <p className="mb-4 text-sm text-sky-800">Chargement des directions...</p>}
        <form className="grid gap-4 md:grid-cols-2" onSubmit={createFiche}>
          <Field label="Intitulé"><Input value={form.title} onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))} /></Field>
          <Field label="Direction"><Select value={form.direction_id} onChange={(event) => setForm((current) => ({ ...current, direction_id: event.target.value }))}><option value="">Choisir</option>{availableDirections.map((direction) => <option key={direction.id} value={direction.id}>{direction.name}</option>)}</Select></Field>
          <Field label="Description"><Textarea value={form.description} onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))} /></Field>
          <Field label="Missions"><Textarea value={form.missions} onChange={(event) => setForm((current) => ({ ...current, missions: event.target.value }))} /></Field>
          <Field label="Compétences requises"><Textarea value={form.required_skills} onChange={(event) => setForm((current) => ({ ...current, required_skills: event.target.value }))} /></Field>
          <Field label="Années d'expérience"><Select value={form.experience_level} onChange={(event) => setForm((current) => ({ ...current, experience_level: event.target.value }))}>{EXPERIENCE_LEVELS.map((level) => <option key={level.value} value={level.value}>{level.label}</option>)}</Select></Field>
          <Field label="Domaine de formation"><Input value={form.formation_domain} onChange={(event) => setForm((current) => ({ ...current, formation_domain: event.target.value }))} /></Field>
          <Field label="Niveau d'études"><Select value={form.education_level} onChange={(event) => setForm((current) => ({ ...current, education_level: event.target.value }))}><option value="">Choisir</option>{EDUCATION_LEVELS.map((level) => <option key={level} value={level}>{level}</option>)}</Select></Field>
          <Field label="Compétences techniques"><Textarea value={form.technical_skills} onChange={(event) => setForm((current) => ({ ...current, technical_skills: event.target.value }))} /></Field>
          <Field label="Compétences managériales"><Textarea value={form.managerial_skills} onChange={(event) => setForm((current) => ({ ...current, managerial_skills: event.target.value }))} /></Field>
          <div className="md:col-span-2 flex gap-2">
            <Button type="submit" disabled={saving}>{saving ? "Création..." : "Créer"}</Button>
            <Button type="button" variant="outline" onClick={() => router.push("/fiches-de-poste")}>Annuler</Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <div className="space-y-2"><Label>{label}</Label>{children}</div>;
}
