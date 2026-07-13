"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { FileText } from "lucide-react";
import { toast } from "sonner";

import { useAuth } from "@/components/auth-provider";
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
import { Textarea } from "@/components/ui/textarea";
import type { DirectionResponse, PaginatedResponse } from "@/lib/backend-types";
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

type FicheForm = {
  title: string;
  main_activities: string;
  missions: string;
  required_skills: string;
  experience_level: string;
  direction_id: string;
  formation_domain: string;
  education_level: string;
  technical_skills: string;
  managerial_skills: string;
};

type FieldErrors = Partial<Record<keyof FicheForm, string>>;

const EMPTY_FORM: FicheForm = {
  title: "",
  main_activities: "",
  missions: "",
  required_skills: "",
  experience_level: "",
  direction_id: "",
  formation_domain: "",
  education_level: "",
  technical_skills: "",
  managerial_skills: "",
};

function validate(form: FicheForm): FieldErrors {
  const errors: FieldErrors = {};

  if (!form.title.trim()) {
    errors.title = "L'intitulé est requis.";
  }

  if (!form.direction_id) {
    errors.direction_id = "La direction est requise.";
  }

  if (!form.main_activities.trim()) {
    errors.main_activities = "Les activités principales sont requises.";
  }

  if (!form.missions.trim()) {
    errors.missions = "Les missions sont requises.";
  }

  if (!form.required_skills.trim()) {
    errors.required_skills = "Les compétences requises sont requises.";
  }

  if (!form.experience_level) {
    errors.experience_level = "Le niveau d'expérience est requis.";
  }

  return errors;
}

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
  const [form, setForm] = useState<FicheForm>(EMPTY_FORM);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});

  useEffect(() => {
    const run = async () => {
      setLoading(true);
      setError(null);
      try {
        const directionsRes = await apiClient.get<
          PaginatedResponse<DirectionResponse>
        >("/directions/", { params: { page: 1, page_size: 100 } });
        setDirections(directionsRes.data.data);
      } catch (err) {
        setError(
          err instanceof ApiHttpError
            ? err.message
            : "Impossible de charger les directions.",
        );
      } finally {
        setLoading(false);
      }
    };

    void run();
  }, []);

  const availableDirections = useMemo(() => {
    if (user?.role === "DIRECTEUR") {
      return directions.filter(
        (direction) => direction.director_id === user.id,
      );
    }
    return directions;
  }, [directions, user]);

  const updateField = <K extends keyof FicheForm>(
    key: K,
    value: FicheForm[K],
  ) => {
    setForm((current) => ({ ...current, [key]: value }));
    setFieldErrors((current) => {
      if (!current[key]) return current;
      const next = { ...current };
      delete next[key];
      return next;
    });
  };

  const createFiche = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    const errors = validate(form);
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) {
      return;
    }

    setSaving(true);
    try {
      await apiClient.post("/fiches-de-poste/", {
        ...form,
        direction_id: Number(form.direction_id),
        experience_level: `${form.experience_level} an${form.experience_level === "0" || form.experience_level === "1" ? "" : "s"}`,
      });
      toast.success("Fiche de poste créée avec succès.");
      router.push("/fiches-de-poste");
    } catch (err) {
      setError(
        err instanceof ApiHttpError
          ? err.message
          : "Impossible de créer la fiche de poste.",
      );
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
        {loading && (
          <p className="mb-4 text-sm text-sky-800">
            Chargement des directions...
          </p>
        )}
        <form
          className="grid gap-4 md:grid-cols-2"
          onSubmit={createFiche}
          noValidate
        >
          <Field label="Intitulé" error={fieldErrors.title}>
            <Input
              value={form.title}
              onChange={(event) => updateField("title", event.target.value)}
              aria-invalid={Boolean(fieldErrors.title)}
            />
          </Field>
          <Field label="Direction" error={fieldErrors.direction_id}>
            <Select
              value={form.direction_id}
              onChange={(event) =>
                updateField("direction_id", event.target.value)
              }
              placeholder="Choisir une direction"
              aria-invalid={Boolean(fieldErrors.direction_id)}
            >
              <option value=""></option>
              {availableDirections.map((direction) => (
                <option key={direction.id} value={direction.id}>
                  {direction.name}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Activités principales" error={fieldErrors.main_activities}>
            <Textarea
              value={form.main_activities}
              onChange={(event) =>
                updateField("main_activities", event.target.value)
              }
              aria-invalid={Boolean(fieldErrors.main_activities)}
            />
          </Field>
          <Field label="Missions" error={fieldErrors.missions}>
            <Textarea
              value={form.missions}
              onChange={(event) => updateField("missions", event.target.value)}
              aria-invalid={Boolean(fieldErrors.missions)}
            />
          </Field>
          <Field
            label="Compétences requises"
            error={fieldErrors.required_skills}
          >
            <Textarea
              value={form.required_skills}
              onChange={(event) =>
                updateField("required_skills", event.target.value)
              }
              aria-invalid={Boolean(fieldErrors.required_skills)}
            />
          </Field>
          <Field
            label="Années d'expérience"
            error={fieldErrors.experience_level}
          >
            <Select
              value={form.experience_level}
              onChange={(event) =>
                updateField("experience_level", event.target.value)
              }
              placeholder="Choisir une année d'expérience"
              aria-invalid={Boolean(fieldErrors.experience_level)}
            >
              <option value=""></option>
              {EXPERIENCE_LEVELS.map((level) => (
                <option key={level.value} value={level.value}>
                  {level.label}
                </option>
              ))}
            </Select>
          </Field>
          <Field
            label="Domaine de formation"
            error={fieldErrors.formation_domain}
          >
            <Input
              value={form.formation_domain}
              onChange={(event) =>
                updateField("formation_domain", event.target.value)
              }
              aria-invalid={Boolean(fieldErrors.formation_domain)}
            />
          </Field>
          <Field label="Niveau d'études" error={fieldErrors.education_level}>
            <Select
              value={form.education_level}
              onChange={(event) =>
                updateField("education_level", event.target.value)
              }
              placeholder="Choisir un niveau d'études"
              aria-invalid={Boolean(fieldErrors.education_level)}
            >
              <option value=""></option>
              {EDUCATION_LEVELS.map((level) => (
                <option key={level} value={level}>
                  {level}
                </option>
              ))}
            </Select>
          </Field>
          <Field
            label="Compétences techniques"
            error={fieldErrors.technical_skills}
          >
            <Textarea
              value={form.technical_skills}
              onChange={(event) =>
                updateField("technical_skills", event.target.value)
              }
              aria-invalid={Boolean(fieldErrors.technical_skills)}
            />
          </Field>
          <Field
            label="Compétences managériales"
            error={fieldErrors.managerial_skills}
          >
            <Textarea
              value={form.managerial_skills}
              onChange={(event) =>
                updateField("managerial_skills", event.target.value)
              }
              aria-invalid={Boolean(fieldErrors.managerial_skills)}
            />
          </Field>
          <div className="md:col-span-2 flex gap-2">
            <Button type="submit" disabled={saving}>
              {saving ? "Création..." : "Créer"}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => router.push("/fiches-de-poste")}
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