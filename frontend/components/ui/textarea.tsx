import * as React from "react";

import { cn } from "@/lib/utils";

function Textarea({ className, ...props }: React.ComponentProps<"textarea">) {
  return (
    <textarea
      data-slot="textarea"
      className={cn(
        "flex min-h-24 w-full rounded-lg border border-slate-300 bg-gradient-to-br from-slate-50 via-slate-100 to-sky-100 px-3 py-2 text-sm text-slate-800 shadow-sm shadow-slate-400/20 outline-none transition-all duration-200 placeholder:text-slate-500 hover:border-sky-400 focus-visible:border-sky-500 focus-visible:ring-2 focus-visible:ring-sky-400/30 disabled:pointer-events-none disabled:cursor-not-allowed disabled:bg-slate-200 disabled:opacity-50 aria-invalid:border-red-500 aria-invalid:ring-2 aria-invalid:ring-red-300",
        className,
      )}
      {...props}
    />
  );
}

export { Textarea };
