"use client"

import {
  Download,
  FileText,
  Trash2,
  Plus,
  Clock,
  BarChart3,
  File,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { mockFiles, mockHistory } from "@/lib/mock-data"

const fileIcons: Record<string, string> = {
  ".qzv": "text-primary",
  ".tsv": "text-emerald-600 dark:text-emerald-400",
  ".biom": "text-amber-600 dark:text-amber-400",
  ".qza": "text-sky-600 dark:text-sky-400",
}

import { getAlphaDiversity, getBetaDiversity, getTaxonomy, getRarefaction } from "@/lib/actions"
import { Suspense, useState, useEffect } from "react"
import { PlotlyPlot } from "@/components/plots/plotly-plot"

// These would normally be fetched from the backend via useEffect/Server Actions
// Using an empty state initially with standard loading UI or placeholders
function ResultsTab({ projectId }: { projectId: string }) {

  const [alphaPlotData, setAlphaPlotData] = useState<any>(null);
  const [betaPlotData, setBetaPlotData] = useState<any>(null);
  const [taxonomyPlotData, setTaxonomyPlotData] = useState<any>(null);
  const [rarefactionPlotData, setRarefactionPlotData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      setIsLoading(true);
      const alphaResult = await getAlphaDiversity(projectId, "shannon", "group")
      const betaResult = await getBetaDiversity(projectId, "group")
      const taxonomyResult = await getTaxonomy(projectId, "Phylum")
      const rarefactionResult = await getRarefaction(projectId)

      if (alphaResult.success) setAlphaPlotData(alphaResult.data);
      if (betaResult.success) setBetaPlotData(betaResult.data);
      if (taxonomyResult.success) setTaxonomyPlotData(taxonomyResult.data);
      if (rarefactionResult.success) setRarefactionPlotData(rarefactionResult.data);

      setIsLoading(false);
    }
    loadData();
  }, [projectId]);

  return (
    <div className="flex flex-col gap-3">
      {/* PCoA result card */}
      <div className="rounded-lg border border-border bg-card overflow-hidden">
        <div className="flex items-center gap-2 px-3 py-2.5 border-b border-border">
          <div className="size-2 rounded-full bg-primary" />
          <span className="text-sm font-medium text-card-foreground">
            PCoA Ordination
          </span>
        </div>
        <div className="relative h-[450px] w-full min-w-0 bg-background rounded border border-border overflow-auto">
          {betaPlotData ? (
            <Suspense fallback={<div className="flex w-full h-full items-center justify-center p-4"><div className="w-8 h-8 rounded-full border-b-2 border-primary animate-spin" /></div>}>
              <div className="min-w-[500px] min-h-[400px] w-full h-full">
                <PlotlyPlot data={(betaPlotData as any).data} layout={(betaPlotData as any).layout} />
              </div>
            </Suspense>
          ) : (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-2">
              <BarChart3 className="size-8 text-muted-foreground/40" />
              <span className="text-xs text-muted-foreground">
                Waiting for Beta Diversity Analysis...
              </span>
            </div>
          )}
        </div>
        <div className="flex items-center gap-2 border-t border-border px-3 py-2">
          <Button
            variant="ghost"
            size="sm"
            className="h-7 gap-1.5 text-xs text-muted-foreground hover:text-foreground"
          >
            <Download className="size-3.5" />
            Download Data
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-7 gap-1.5 text-xs text-muted-foreground hover:text-foreground"
          >
            <Plus className="size-3.5" />
            Add to Report
          </Button>
        </div>
      </div>

      {/* Alpha diversity card */}
      <div className="rounded-lg border border-border bg-card overflow-hidden">
        <div className="flex items-center gap-2 px-3 py-2.5 border-b border-border">
          <div className="size-2 rounded-full bg-primary" />
          <span className="text-sm font-medium text-card-foreground">
            Alpha Diversity
          </span>
        </div>
        <div className="relative h-[450px] w-full min-w-0 bg-background rounded border border-border overflow-auto">
          {alphaPlotData ? (
            <Suspense fallback={<div className="flex w-full h-full items-center justify-center p-4"><div className="w-8 h-8 rounded-full border-b-2 border-primary animate-spin" /></div>}>
              <div className="min-w-[500px] min-h-[400px] w-full h-full">
                <PlotlyPlot data={(alphaPlotData as any).data} layout={(alphaPlotData as any).layout} />
              </div>
            </Suspense>
          ) : (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-2">
              <BarChart3 className="size-8 text-muted-foreground/40" />
              <span className="text-xs text-muted-foreground">
                Waiting for Alpha Diversity Analysis...
              </span>
            </div>
          )}
        </div>
        <div className="flex items-center gap-2 border-t border-border px-3 py-2">
          <Button
            variant="ghost"
            size="sm"
            className="h-7 gap-1.5 text-xs text-muted-foreground hover:text-foreground"
          >
            <Download className="size-3.5" />
            Download Data
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-7 gap-1.5 text-xs text-muted-foreground hover:text-foreground"
          >
            <Plus className="size-3.5" />
            Add to Report
          </Button>
        </div>
      </div>

      {/* Taxonomy card */}
      <div className="rounded-lg border border-border bg-card overflow-hidden">
        <div className="flex items-center gap-2 px-3 py-2.5 border-b border-border">
          <div className="size-2 rounded-full bg-primary" />
          <span className="text-sm font-medium text-card-foreground">
            Taxonomic Composition
          </span>
        </div>
        <div className="relative h-[450px] w-full min-w-0 bg-background rounded border border-border overflow-auto">
          {taxonomyPlotData ? (
            <Suspense fallback={<div className="flex w-full h-full items-center justify-center p-4"><div className="w-8 h-8 rounded-full border-b-2 border-primary animate-spin" /></div>}>
              <div className="min-w-[500px] min-h-[400px] w-full h-full">
                <PlotlyPlot data={(taxonomyPlotData as any).data} layout={(taxonomyPlotData as any).layout} />
              </div>
            </Suspense>
          ) : (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-2">
              <BarChart3 className="size-8 text-muted-foreground/40" />
              <span className="text-xs text-muted-foreground">
                Waiting for Taxonomy Analysis...
              </span>
            </div>
          )}
        </div>
        <div className="flex items-center gap-2 border-t border-border px-3 py-2">
          <Button variant="ghost" size="sm" className="h-7 gap-1.5 text-xs text-muted-foreground hover:text-foreground">
            <Download className="size-3.5" /> Download Data
          </Button>
          <Button variant="ghost" size="sm" className="h-7 gap-1.5 text-xs text-muted-foreground hover:text-foreground">
            <Plus className="size-3.5" /> Add to Report
          </Button>
        </div>
      </div>

      {/* Rarefaction card */}
      <div className="rounded-lg border border-border bg-card overflow-hidden">
        <div className="flex items-center gap-2 px-3 py-2.5 border-b border-border">
          <div className="size-2 rounded-full bg-primary" />
          <span className="text-sm font-medium text-card-foreground">
            Rarefaction Curves
          </span>
        </div>
        <div className="relative h-[450px] w-full min-w-0 bg-background rounded border border-border overflow-auto">
          {rarefactionPlotData ? (
            <Suspense fallback={<div className="flex w-full h-full items-center justify-center p-4"><div className="w-8 h-8 rounded-full border-b-2 border-primary animate-spin" /></div>}>
              <div className="min-w-[500px] min-h-[400px] w-full h-full">
                <PlotlyPlot data={(rarefactionPlotData as any).data} layout={(rarefactionPlotData as any).layout} />
              </div>
            </Suspense>
          ) : (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-2">
              <BarChart3 className="size-8 text-muted-foreground/40" />
              <span className="text-xs text-muted-foreground">
                Waiting for Rarefaction Analysis...
              </span>
            </div>
          )}
        </div>
        <div className="flex items-center gap-2 border-t border-border px-3 py-2">
          <Button variant="ghost" size="sm" className="h-7 gap-1.5 text-xs text-muted-foreground hover:text-foreground">
            <Download className="size-3.5" /> Download Data
          </Button>
          <Button variant="ghost" size="sm" className="h-7 gap-1.5 text-xs text-muted-foreground hover:text-foreground">
            <Plus className="size-3.5" /> Add to Report
          </Button>
        </div>
      </div>
    </div>
  )
}

function FilesTab() {
  return (
    <div className="flex flex-col gap-1">
      {mockFiles.map((file) => (
        <div
          key={file.id}
          className="group flex items-center gap-3 rounded-lg px-3 py-2.5 transition-colors hover:bg-muted"
        >
          <File
            className={cn("size-4 shrink-0", fileIcons[file.type] || "text-muted-foreground")}
          />
          <div className="flex-1 min-w-0">
            <p className="truncate text-sm font-medium text-foreground">
              {file.name}
            </p>
            <p className="text-[11px] text-muted-foreground">
              {file.size} — {file.uploadDate}
            </p>
          </div>
          <Button
            variant="ghost"
            size="icon-sm"
            className="opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-destructive-foreground transition-opacity"
            aria-label={`Delete ${file.name}`}
          >
            <Trash2 className="size-3.5" />
          </Button>
        </div>
      ))}
    </div>
  )
}

function HistoryTab() {
  return (
    <div className="flex flex-col gap-1">
      {mockHistory.map((entry) => (
        <div
          key={entry.id}
          className="flex gap-3 rounded-lg px-3 py-2.5 transition-colors hover:bg-muted"
        >
          <div className="mt-0.5">
            <Clock className="size-4 text-muted-foreground" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-foreground">
              {entry.name}
            </p>
            <p className="text-[11px] text-muted-foreground">
              {entry.timestamp}
            </p>
            <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
              {entry.summary}
            </p>
          </div>
        </div>
      ))}
    </div>
  )
}

export function ResultsPanel({ className, projectId }: { className?: string; projectId: string }) {
  return (
    <div className={cn("flex h-full flex-col border-l border-border bg-background", className)}>
      <Tabs defaultValue="results" className="flex h-full flex-col">
        <div className="shrink-0 border-b border-border px-3 pt-3">
          <TabsList className="w-full">
            <TabsTrigger value="results" className="flex-1">
              Results
            </TabsTrigger>
            <TabsTrigger value="files" className="flex-1">
              Files
            </TabsTrigger>
            <TabsTrigger value="history" className="flex-1">
              History
            </TabsTrigger>
          </TabsList>
        </div>
        <div className="flex-1 overflow-y-auto min-h-0 w-full pt-2">
          <div className="p-3">
            <TabsContent value="results" className="mt-0">
              <ResultsTab projectId={projectId} />
            </TabsContent>
            <TabsContent value="files" className="mt-0">
              <FilesTab />
            </TabsContent>
            <TabsContent value="history" className="mt-0">
              <HistoryTab />
            </TabsContent>
          </div>
        </div>
      </Tabs>
    </div>
  )
}
