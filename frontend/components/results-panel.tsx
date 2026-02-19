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

function ResultsTab() {
  return (
    <div className="flex flex-col gap-3">
      {/* PCoA result card */}
      <div className="rounded-lg border border-border bg-card overflow-hidden">
        <div className="flex items-center gap-2 px-3 py-2.5 border-b border-border">
          <div className="size-2 rounded-full bg-primary" />
          <span className="text-sm font-medium text-card-foreground">
            PCoA Ordination
          </span>
          <span className="ml-auto text-[11px] text-muted-foreground">
            10:25 AM
          </span>
        </div>
        <div className="relative aspect-[4/3] bg-muted">
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-2">
            <BarChart3 className="size-8 text-muted-foreground/40" />
            <span className="text-xs text-muted-foreground">
              PCoA Chart — Bray-Curtis
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2 border-t border-border px-3 py-2">
          <Button
            variant="ghost"
            size="sm"
            className="h-7 gap-1.5 text-xs text-muted-foreground hover:text-foreground"
          >
            <Download className="size-3.5" />
            Download PNG
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
          <span className="ml-auto text-[11px] text-muted-foreground">
            10:23 AM
          </span>
        </div>
        <div className="relative aspect-[4/3] bg-muted">
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-2">
            <BarChart3 className="size-8 text-muted-foreground/40" />
            <span className="text-xs text-muted-foreground">
              Shannon Diversity Boxplot
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2 border-t border-border px-3 py-2">
          <Button
            variant="ghost"
            size="sm"
            className="h-7 gap-1.5 text-xs text-muted-foreground hover:text-foreground"
          >
            <Download className="size-3.5" />
            Download PNG
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

export function ResultsPanel({ className }: { className?: string }) {
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
        <ScrollArea className="flex-1">
          <div className="p-3">
            <TabsContent value="results" className="mt-0">
              <ResultsTab />
            </TabsContent>
            <TabsContent value="files" className="mt-0">
              <FilesTab />
            </TabsContent>
            <TabsContent value="history" className="mt-0">
              <HistoryTab />
            </TabsContent>
          </div>
        </ScrollArea>
      </Tabs>
    </div>
  )
}
