import * as React from "react"

import { cn } from "@/lib/utils"

function Textarea({ className, ...props }: React.ComponentProps<"textarea">) {
  return (
    <textarea
      data-slot="textarea"
      className={cn(
        "flex min-h-24 w-full rounded-lg border border-emerald-200 bg-emerald-50/90 px-3 py-2 text-sm shadow-sm outline-none transition-all duration-200 placeholder:text-emerald-700/60 hover:border-emerald-300 focus-visible:ring-2 focus-visible:ring-emerald-200/70 disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      {...props}
    />
  )
}

export { Textarea }