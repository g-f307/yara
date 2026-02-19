import { cn } from "@/lib/utils"
import { CheckCircle2, AlertTriangle, XCircle, Info } from "lucide-react"

type Variant = "success" | "warning" | "danger" | "info"

const variantStyles: Record<Variant, string> = {
  success: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300",
  warning: "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300",
  danger: "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300",
  info: "bg-violet-100 text-violet-800 dark:bg-violet-900/40 dark:text-violet-300",
}

const variantIcons: Record<Variant, React.ComponentType<{ className?: string }>> = {
  success: CheckCircle2,
  warning: AlertTriangle,
  danger: XCircle,
  info: Info,
}

export function StatBadge({
  variant,
  label,
  className,
}: {
  variant: Variant
  label: string
  className?: string
}) {
  const Icon = variantIcons[variant]
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium",
        variantStyles[variant],
        className
      )}
    >
      <Icon className="size-3.5" />
      {label}
    </span>
  )
}
