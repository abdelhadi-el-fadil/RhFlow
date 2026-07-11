import * as React from "react";

import { cn } from "@/lib/utils";
function Input({ className, type, ...props }: React.ComponentProps<"input">) {
  return (
    <input
      type={type}
      data-slot="input"
      className={cn(
        "h-8 w-full min-w-0 rounded-lg border border-slate-300/90 bg-white px-2.5 py-1 text-base text-slate-800 shadow-md shadow-slate-300/20 transition-all duration-200 outline-none placeholder:text-slate-400 hover:border-sky-400 focus-visible:border-sky-500 focus-visible:ring-2 focus-visible:ring-sky-400/25 disabled:pointer-events-none disabled:cursor-not-allowed disabled:border-slate-200 disabled:bg-slate-100 disabled:text-slate-500 aria-invalid:border-red-500 aria-invalid:ring-2 aria-invalid:ring-red-300 file:inline-flex file:h-6 file:border-0 file:bg-transparent file:text-sm file:font-medium md:text-sm",
        className,
      )}
      {...props}
    />
  );
}

export { Input };
