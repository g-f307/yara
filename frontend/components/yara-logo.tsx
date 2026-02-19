import { cn } from "@/lib/utils"

export function DnaIcon({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={cn("size-6", className)}
      aria-hidden="true"
    >
      <path d="M2 15c6.667-6 13.333 0 20-6" />
      <path d="M9 3.236s1 2.764 3 2.764 3-2.764 3-2.764" />
      <path d="M12 12h4" />
      <path d="M8 12h.01" />
      <path d="M2 9c6.667 6 13.333 0 20 6" />
      <path d="M9 20.764s1-2.764 3-2.764 3 2.764 3 2.764" />
    </svg>
  )
}

export function YaraLogo({ collapsed = false }: { collapsed?: boolean }) {
  return (
    <div className="flex items-center gap-2.5">
      <div className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground">
        <DnaIcon className="size-4" />
      </div>
      {!collapsed && (
        <span className="text-lg font-semibold tracking-tight text-foreground">
          YARA
        </span>
      )}
    </div>
  )
}
