"use client"

import { useState } from "react"
import { ChevronDown } from "lucide-react"
import { cn } from "@/lib/utils"
import { StatBadge } from "@/components/stat-badge"
import type { AnalysisCardData } from "@/lib/mock-data"

export function AnalysisCard({ data }: { data: AnalysisCardData }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="mt-3 rounded-lg border border-border bg-card">
      <div className="flex items-start justify-between gap-3 p-3">
        <div className="flex flex-col gap-1.5">
          <p className="text-sm font-medium text-card-foreground">
            {data.metricName}
          </p>
          <div className="flex items-center gap-3">
            <span className="text-2xl font-bold tabular-nums text-card-foreground">
              {data.value}
            </span>
            {data.pValue && (
              <span className="text-xs text-muted-foreground">
                {"p = "}
                {data.pValue}
              </span>
            )}
          </div>
          <StatBadge variant={data.interpretation} label={data.interpretationLabel} />
        </div>
      </div>
      {data.stats && data.stats.length > 0 && (
        <>
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex w-full items-center justify-center gap-1 border-t border-border px-3 py-2 text-xs text-muted-foreground transition-colors hover:bg-muted/50 focus-visible:ring-2 focus-visible:ring-ring"
            aria-expanded={expanded}
            aria-label={expanded ? "Collapse statistics" : "Expand statistics"}
          >
            {expanded ? "Hide details" : "Show details"}
            <ChevronDown
              className={cn(
                "size-3 transition-transform",
                expanded && "rotate-180"
              )}
            />
          </button>
          {expanded && (
            <div className="border-t border-border p-3">
              <div className="grid grid-cols-2 gap-2">
                {data.stats.map((stat) => (
                  <div key={stat.label} className="flex flex-col">
                    <span className="text-[11px] text-muted-foreground">
                      {stat.label}
                    </span>
                    <span className="text-sm font-medium tabular-nums text-card-foreground">
                      {stat.value}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
