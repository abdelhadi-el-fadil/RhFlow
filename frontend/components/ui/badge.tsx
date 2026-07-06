import * as React from "react"

import { cn } from "@/lib/utils"

const badgeVariants = {
  default: "border-transparent bg-primary text-primary-foreground",
  secondary: "border-transparent bg-secondary text-secondary-foreground",
  destructive: "border-transparent bg-destructive text-destructive-foreground",
  outline: "text-foreground border-border bg-background",
}

type BadgeProps = React.ComponentProps<"span"> & {
  variant?: keyof typeof badgeVariants
}

function Badge({ className, variant = "default", ...props }: BadgeProps) {
  return (
    <span
      data-slot="badge"
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium whitespace-nowrap",
        badgeVariants[variant],
        className,
      )}
      {...props}
    />
  )
}

export { Badge }