import * as React from "react";

import { cn } from "@/lib/utils";

function Textarea({ className, ...props }: React.ComponentProps<"textarea">) {
  return (
    <textarea
      data-slot="textarea"
      className={cn(
        "flex min-h-24 w-full rounded-lg border border-slate-300/90 bg-white px-3 py-2 text-sm text-slate-800 shadow-md shadow-slate-300/20 outline-none transition-all duration-200 placeholder:text-slate-400 hover:border-sky-400 hover:shadow-sky-300/20 focus-visible:border-sky-500 focus-visible:ring-2 focus-visible:ring-sky-400/25 disabled:pointer-events-none disabled:cursor-not-allowed disabled:border-slate-200 disabled:bg-slate-100 disabled:text-slate-500 aria-invalid:border-red-500 aria-invalid:ring-2 aria-invalid:ring-red-300",
        className,
      )}
      {...props}
    />
  );
}

export { Textarea };
