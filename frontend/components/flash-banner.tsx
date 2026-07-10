"use client";

import { useState } from "react";
import { CheckCircle2, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { takeFlashSuccess } from "@/lib/flash";

export function FlashBanner() {
  const [message, setMessage] = useState<string | null>(() => takeFlashSuccess());

  if (!message) {
    return null;
  }

  return (
    <div className="mb-4 flex items-start justify-between gap-3 rounded-lg border border-emerald-300 bg-emerald-100 px-4 py-3 text-emerald-900">
      <p className="flex items-center gap-2 text-sm font-medium">
        <CheckCircle2 className="size-4" />
        {message}
      </p>
      <Button
        type="button"
        size="icon-sm"
        variant="ghost"
        className="h-7 w-7 text-emerald-900 hover:bg-emerald-200"
        onClick={() => setMessage(null)}
        aria-label="Fermer le message"
      >
        <X className="size-4" />
      </Button>
    </div>
  );
}
