import * as React from "react"

import { cn } from "@/lib/utils"

function Input({ className, type, ...props }: React.ComponentProps<"input">) {
  return (
    <input
      type={type}
      data-slot="input"
      className={cn(
        "h-8 w-full min-w-0 rounded-lg border border-slate-300 bg-gradient-to-br from-slate-50 via-slate-100 to-sky-100 px-2.5 py-1 text-base text-slate-800 shadow-sm shadow-slate-400/20 transition-all duration-200 outline-none placeholder:text-slate-500 hover:border-sky-400 focus-visible:border-sky-500 focus-visible:ring-2 focus-visible:ring-sky-400/30 disabled:pointer-events-none disabled:cursor-not-allowed disabled:bg-slate-200 disabled:opacity-50 aria-invalid:border-red-500 aria-invalid:ring-2 aria-invalid:ring-red-300 file:inline-flex file:h-6 file:border-0 file:bg-transparent file:text-sm file:font-medium md:text-sm",
        className
      )}
      {...props}
    />
  )
}

export { Input }