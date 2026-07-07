import * as React from "react"

import { cn } from "@/lib/utils"

function Select({ className, ...props }: React.ComponentProps<"select">) {
  return (
    <select
      data-slot="select"
      className={cn(
        "flex h-9 w-full rounded-lg border border-emerald-200 bg-emerald-50/90 px-3 py-2 text-sm shadow-sm outline-none transition-all duration-200 hover:border-emerald-300 focus-visible:ring-2 focus-visible:ring-emerald-200/70 disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      {...props}
    />
  )
}

export { Select }