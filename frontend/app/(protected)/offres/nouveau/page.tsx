"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { WandSparkles } from "lucide-react";
import { toast } from "sonner";

import { RoleGate } from "@/components/role-gate";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ApiHttpError, apiClient } from "@/lib/http";

export default function NewOffrePage() {
  return (
    <RoleGate roles={["ADMIN", "DRH", "DIRECTEUR", "DG"]}>
      <NewOffreContent />
    </RoleGate>
  );
}

function NewOffreContent() {
  const router = useRouter();
  const [form, setForm] = useState({ title: "", description: "", requirements: "", deadline: "", besoin_id: "" });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const create = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await apiClient.post("/offres/", {
        title: form.title,
        description: form.description || null,
        requirements: form.requirements || null,
        deadline: form.deadline || null,
        besoin_id: Number(form.besoin_id),
      });
      toast.success("Offre créée avec succès.");
      router.push("/offres");
    } catch (err) {
      const message = err instanceof ApiHttpError ? err.message : "Impossible de créer l'offre.";
      setError(message);
      toast.error(message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card className="premium-panel premium-lift border-amber-200/65 bg-gradient-to-br from-stone-50 via-amber-50 to-teal-50">
      <CardHeader>
        <CardTitle className="premium-title flex items-center gap-2">
          <WandSparkles className="size-5 text-teal-700" />
          Créer une offre
        </CardTitle>
      </CardHeader>
      <CardContent>
        {error && <p className="mb-4 text-sm text-destructive">{error}</p>}
        <form className="grid gap-4 md:grid-cols-2" onSubmit={create}>
          <Field label="Besoin ID"><Input value={form.besoin_id} onChange={(event) => setForm((current) => ({ ...current, besoin_id: event.target.value }))} /></Field>
          <Field label="Deadline"><Input type="date" value={form.deadline} onChange={(event) => setForm((current) => ({ ...current, deadline: event.target.value }))} /></Field>
          <Field label="Titre"><Input value={form.title} onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))} /></Field>
          <Field label="Description"><Textarea value={form.description} onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))} /></Field>
          <Field label="Requirements"><Textarea value={form.requirements} onChange={(event) => setForm((current) => ({ ...current, requirements: event.target.value }))} /></Field>
          <div className="md:col-span-2 flex gap-2">
            <Button type="submit" disabled={saving}>{saving ? "Création..." : "Créer"}</Button>
            <Button type="button" variant="outline" onClick={() => router.push("/offres")}>Annuler</Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <div className="space-y-2"><Label>{label}</Label>{children}</div>;
}