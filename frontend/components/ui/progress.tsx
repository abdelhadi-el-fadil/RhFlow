import * as React from "react"

import { cn } from "@/lib/utils"

function Progress({ className, value = 0, ...props }: React.ComponentProps<"div"> & { value?: number }) {
  const safeValue = Math.min(100, Math.max(0, value))

  return (
    <div
      data-slot="progress"
      className={cn("h-2 w-full overflow-hidden rounded-full bg-muted", className)}
      {...props}
    >
      <div
        className="brand-gradient h-full rounded-full transition-all duration-200"
        style={{ width: `${safeValue}%` }}
      />
    </div>
  )
}

export { Progress }