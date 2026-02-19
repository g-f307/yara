"use client"

import Link from "next/link"
import { useParams } from "next/navigation"
import { ArrowLeft, Download, BarChart3 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { YaraLogo } from "@/components/yara-logo"
import { StatBadge } from "@/components/stat-badge"
import { mockProjects, mockHistory } from "@/lib/mock-data"

export default function ReportPage() {
  const params = useParams()
  const projectId = params.id as string
  const project = mockProjects.find((p) => p.id === projectId) || mockProjects[0]

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-10 flex items-center justify-between border-b border-border bg-background/80 backdrop-blur-sm px-4 py-3 md:px-6">
        <div className="flex items-center gap-3">
          <Link href={`/project/${projectId}`}>
            <Button variant="ghost" size="icon-sm" aria-label="Back to project">
              <ArrowLeft className="size-4" />
            </Button>
          </Link>
          <YaraLogo />
        </div>
        <Button className="bg-primary text-primary-foreground hover:bg-primary/90">
          <Download className="size-4" />
          Export PDF
        </Button>
      </header>

      {/* Report content */}
      <main className="mx-auto max-w-3xl px-4 py-8 md:px-6 lg:px-8">
        {/* Title section */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight text-foreground text-balance">
            {project.name}
          </h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Analysis Report — Generated {project.date}
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <StatBadge variant="info" label={`${project.fileCount} files analyzed`} />
            <StatBadge variant="success" label={`${project.analysisCount} analyses completed`} />
          </div>
        </div>

        {/* Summary section */}
        <section className="mb-8">
          <h2 className="text-lg font-semibold text-foreground mb-3">
            Executive Summary
          </h2>
          <div className="rounded-lg border border-border bg-card p-4">
            <p className="text-sm leading-relaxed text-card-foreground">
              This report summarizes the metagenomic analysis of 15 soil samples
              collected from the Amazon Basin. Alpha diversity analysis revealed
              significant differences between forest and cleared-area groups
              (Shannon Index: p=0.032). PCoA ordination using Bray-Curtis
              dissimilarity showed clear separation between the two groups, with
              the first two axes explaining 61% of total variance.
            </p>
          </div>
        </section>

        {/* Analyses */}
        <section className="mb-8">
          <h2 className="text-lg font-semibold text-foreground mb-3">
            Analyses Performed
          </h2>
          <div className="flex flex-col gap-4">
            {mockHistory.map((entry) => (
              <div
                key={entry.id}
                className="rounded-lg border border-border bg-card overflow-hidden"
              >
                <div className="flex items-center gap-2 border-b border-border px-4 py-3">
                  <div className="size-2 rounded-full bg-primary" />
                  <h3 className="text-sm font-medium text-card-foreground">
                    {entry.name}
                  </h3>
                  <span className="ml-auto text-[11px] text-muted-foreground">
                    {entry.timestamp}
                  </span>
                </div>
                <div className="p-4">
                  <p className="text-sm text-muted-foreground leading-relaxed mb-3">
                    {entry.summary}
                  </p>
                  {/* Chart placeholder */}
                  <div className="relative aspect-[16/9] rounded-lg bg-muted">
                    <div className="absolute inset-0 flex flex-col items-center justify-center gap-2">
                      <BarChart3 className="size-8 text-muted-foreground/40" />
                      <span className="text-xs text-muted-foreground">
                        Visualization
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Key findings */}
        <section className="mb-8">
          <h2 className="text-lg font-semibold text-foreground mb-3">
            Key Findings
          </h2>
          <div className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-lg border border-border bg-card p-4">
              <p className="text-[11px] uppercase tracking-wider text-muted-foreground mb-1">
                Shannon Index
              </p>
              <p className="text-2xl font-bold tabular-nums text-card-foreground">
                3.24
              </p>
              <StatBadge variant="success" label="Significant" className="mt-2" />
            </div>
            <div className="rounded-lg border border-border bg-card p-4">
              <p className="text-[11px] uppercase tracking-wider text-muted-foreground mb-1">
                P-Value
              </p>
              <p className="text-2xl font-bold tabular-nums text-card-foreground">
                0.032
              </p>
              <StatBadge variant="success" label="p &lt; 0.05" className="mt-2" />
            </div>
            <div className="rounded-lg border border-border bg-card p-4">
              <p className="text-[11px] uppercase tracking-wider text-muted-foreground mb-1">
                Variance Explained
              </p>
              <p className="text-2xl font-bold tabular-nums text-card-foreground">
                61%
              </p>
              <StatBadge variant="info" label="Axes 1 + 2" className="mt-2" />
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="border-t border-border pt-6 text-center">
          <p className="text-xs text-muted-foreground">
            Report generated by YARA — Your Assistant for Results Analysis
          </p>
        </footer>
      </main>
    </div>
  )
}
