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
import { toast } from "sonner"

const fileIcons: Record<string, string> = {
  ".qzv": "text-primary",
  ".tsv": "text-emerald-600 dark:text-emerald-400",
  ".biom": "text-amber-600 dark:text-amber-400",
  ".qza": "text-sky-600 dark:text-sky-400",
}

import { getAlphaDiversity, getBetaDiversity, getTaxonomy, getRarefaction, buildReport } from "@/lib/actions"
import { Suspense, useState, useEffect } from "react"
import { PlotlyPlot } from "@/components/plots/plotly-plot"

import { useResultsStore } from "@/store/use-results-store"

function ResultsTab({ projectId }: { projectId: string }) {
  const alphaPlotData = useResultsStore((state: any) => state.alpha);
  const betaPlotData = useResultsStore((state: any) => state.beta);
  const taxonomyPlotData = useResultsStore((state: any) => state.taxonomy);
  const rarefactionPlotData = useResultsStore((state: any) => state.rarefaction);
  const statisticsPlotData = useResultsStore((state: any) => state.statistics);

  const handleAddToReport = async (type: 'alpha' | 'beta' | 'taxonomy' | 'rarefaction', plotData: any, title: string) => {
    if (!plotData) return;
    const divId = `plot-${type}`;
    const graphDiv = document.getElementById(divId);
    if (!graphDiv) {
      toast.error("Gráfico não encontrado ou ainda carregando.");
      return;
    }
    
    try {
      // @ts-ignore
      const Plotly = (await import('plotly.js-dist-min')).default;
      const b64 = await Plotly.toImage(graphDiv as any, { format: 'png', width: 800, height: 600 });
      
      useResultsStore.getState().addReportItem({
        id: `${type}-${Date.now()}`,
        type: 'plot',
        title,
        base64Image: b64,
      });
      
      useResultsStore.getState().setActiveTab('report');
      toast.success(`${title} adicionado ao relatório!`);
    } catch (e) {
      console.error(e);
      toast.error("Erro ao capturar gráfico.");
    }
  };

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
                <PlotlyPlot divId="plot-beta" data={(betaPlotData as any).data} layout={(betaPlotData as any).layout} />
              </div>
            </Suspense>
          ) : (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-2">
              <BarChart3 className="size-8 text-muted-foreground/40" />
              <span className="text-xs text-muted-foreground">
                Ask YARA to plot Beta Diversity or PCoA
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
            onClick={() => handleAddToReport('beta', betaPlotData, 'Beta Diversity (PCoA)')}
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
                <PlotlyPlot divId="plot-alpha" data={(alphaPlotData as any).data} layout={(alphaPlotData as any).layout} />
              </div>
            </Suspense>
          ) : (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-2">
              <BarChart3 className="size-8 text-muted-foreground/40" />
              <span className="text-xs text-muted-foreground">
                Ask YARA to plot Alpha Diversity
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
            onClick={() => handleAddToReport('alpha', alphaPlotData, 'Alpha Diversity')}
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
                <PlotlyPlot divId="plot-taxonomy" data={(taxonomyPlotData as any).data} layout={(taxonomyPlotData as any).layout} />
              </div>
            </Suspense>
          ) : (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-2">
              <BarChart3 className="size-8 text-muted-foreground/40" />
              <span className="text-xs text-muted-foreground">
                Ask YARA to visualize Taxonomic Composition
              </span>
            </div>
          )}
        </div>
        <div className="flex items-center gap-2 border-t border-border px-3 py-2">
          <Button variant="ghost" size="sm" className="h-7 gap-1.5 text-xs text-muted-foreground hover:text-foreground">
            <Download className="size-3.5" /> Download Data
          </Button>
          <Button variant="ghost" size="sm" className="h-7 gap-1.5 text-xs text-muted-foreground hover:text-foreground" onClick={() => handleAddToReport('taxonomy', taxonomyPlotData, 'Taxonomic Composition')}>
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
                <PlotlyPlot divId="plot-rarefaction" data={(rarefactionPlotData as any).data} layout={(rarefactionPlotData as any).layout} />
              </div>
            </Suspense>
          ) : (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-2">
              <BarChart3 className="size-8 text-muted-foreground/40" />
              <span className="text-xs text-muted-foreground">
                Ask YARA to check Rarefaction Curves
              </span>
            </div>
          )}
        </div>
        <div className="flex items-center gap-2 border-t border-border px-3 py-2">
          <Button variant="ghost" size="sm" className="h-7 gap-1.5 text-xs text-muted-foreground hover:text-foreground">
            <Download className="size-3.5" /> Download Data
          </Button>
          <Button variant="ghost" size="sm" className="h-7 gap-1.5 text-xs text-muted-foreground hover:text-foreground" onClick={() => handleAddToReport('rarefaction', rarefactionPlotData, 'Rarefaction Curves')}>
            <Plus className="size-3.5" /> Add to Report
          </Button>
        </div>
      </div>

      {/* Statistics card */}
      <div className="rounded-lg border border-border bg-card overflow-hidden">
        <div className="flex items-center gap-2 px-3 py-2.5 border-b border-border">
          <div className="size-2 rounded-full bg-primary" />
          <span className="text-sm font-medium text-card-foreground">
            Statistical Comparison
          </span>
        </div>
        <div className="relative h-[450px] w-full min-w-0 bg-background rounded border border-border overflow-auto">
          {statisticsPlotData ? (
            <Suspense fallback={<div className="flex w-full h-full items-center justify-center p-4"><div className="w-8 h-8 rounded-full border-b-2 border-primary animate-spin" /></div>}>
              <div className="min-w-[500px] min-h-[400px] w-full h-full">
                <PlotlyPlot divId="plot-statistics" data={(statisticsPlotData as any).data} layout={(statisticsPlotData as any).layout} />
              </div>
            </Suspense>
          ) : (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-2">
              <BarChart3 className="size-8 text-muted-foreground/40" />
              <span className="text-xs text-muted-foreground">
                Ask YARA to compare groups statistically
              </span>
            </div>
          )}
        </div>
        <div className="flex items-center gap-2 border-t border-border px-3 py-2">
          <Button variant="ghost" size="sm" className="h-7 gap-1.5 text-xs text-muted-foreground hover:text-foreground">
            <Download className="size-3.5" /> Download Data
          </Button>
          <Button variant="ghost" size="sm" className="h-7 gap-1.5 text-xs text-muted-foreground hover:text-foreground" onClick={() => handleAddToReport('statistics' as any, statisticsPlotData, 'Statistical Comparison')}>
            <Plus className="size-3.5" /> Add to Report
          </Button>
        </div>
      </div>
    </div>
  )
}

function FilesTab({ files }: { files: any[] }) {
  if (!files || files.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
        <File className="size-8 mb-2 opacity-20" />
        <p className="text-sm">Nenhum arquivo enviado ainda.</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-1">
      {files.map((file) => (
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
              {(file.size / 1024 / 1024).toFixed(1)} MB — {new Date(file.createdAt).toLocaleDateString("pt-BR")}
            </p>
          </div>
        </div>
      ))}
    </div>
  )
}

function HistoryTab({ sessions }: { sessions: any[] }) {
  if (!sessions || sessions.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
        <Clock className="size-8 mb-2 opacity-20" />
        <p className="text-sm">Nenhum histórico encontrado.</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-1">
      {sessions.map((entry) => (
        <div
          key={entry.id}
          className="flex gap-3 rounded-lg px-3 py-2.5 transition-colors hover:bg-muted"
        >
          <div className="mt-0.5">
            <Clock className="size-4 text-muted-foreground" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-foreground">
              Sessão de Análise
            </p>
            <p className="text-[11px] text-muted-foreground">
              {new Date(entry.createdAt).toLocaleString("pt-BR")}
            </p>
            <p className="mt-1 text-xs text-muted-foreground leading-relaxed truncate">
              ID: {entry.id}
            </p>
          </div>
        </div>
      ))}
    </div>
  )
}

function ReportTab({ projectId }: { projectId: string }) {
  const reportItems = useResultsStore((state: any) => state.reportItems);
  const removeReportItem = useResultsStore((state: any) => state.removeReportItem);
  const updateReportItemText = useResultsStore((state: any) => state.updateReportItemText);
  const [isExporting, setIsExporting] = useState(false);

  const handleExport = async (format: "pdf" | "docx") => {
    if (reportItems.length === 0) {
      toast.error("O relatório está vazio.");
      return;
    }
    
    setIsExporting(true);
    const toastId = toast.loading(`Iniciando geração do ${format.toUpperCase()}...`);
    
    try {
      const result = await buildReport(projectId, format, reportItems);
      if (result.success && result.downloadUrl) {
        toast.success(`${format.toUpperCase()} gerado com sucesso!`, { id: toastId });
        
        // Auto-download the file by creating a temporary anchor tag
        const fileUrl = `/api/core${result.downloadUrl}`;
        
        const a = document.createElement("a");
        a.href = fileUrl;
        a.download = result.downloadUrl.split("/").pop() || `report.${format}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        
      } else {
        toast.error(`Falha ao gerar ${format.toUpperCase()}: ${result.error}`, { id: toastId });
      }
    } catch (error) {
       toast.error(`Falha na comunicação com o servidor.`, { id: toastId });
    } finally {
       setIsExporting(false);
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-foreground">Construtor de Relatórios</h3>
        <div className="flex gap-2">
          <Button size="sm" variant="outline" className="h-8 text-xs" onClick={() => handleExport("docx")} disabled={isExporting}>
             Export DOCX
          </Button>
          <Button size="sm" className="h-8 text-xs" onClick={() => handleExport("pdf")} disabled={isExporting}>
             <FileText className="size-3.5 mr-1.5" />
             Export PDF
          </Button>
        </div>
      </div>
      
      {reportItems.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-[80px] text-center border rounded-lg border-dashed border-border bg-card/50 text-muted-foreground mt-2">
          <FileText className="size-8 mb-3 opacity-20" />
          <p className="text-sm font-medium">Seu relatório está vazio.</p>
          <p className="text-xs max-w-[200px] mt-1">Gere análises no chat e clique em "Add to Report" nas figuras para compilá-las aqui.</p>
        </div>
      ) : (
        <div className="flex flex-col gap-4 mt-2">
          {reportItems.map((item: any) => (
            <div key={item.id} className="border border-border rounded-lg p-3 bg-card shadow-sm flex flex-col gap-3">
              <div className="flex items-center justify-between border-b border-border pb-2">
                <span className="text-sm font-semibold">{item.title}</span>
                <Button variant="ghost" size="icon-sm" className="h-6 w-6" onClick={() => removeReportItem(item.id)}>
                  <Trash2 className="size-3.5 text-muted-foreground hover:text-destructive" />
                </Button>
              </div>
              
              {item.type === 'plot' && item.base64Image && (
                <div className="bg-background border border-border rounded overflow-hidden flex justify-center p-2 relative h-[250px]">
                  <img src={item.base64Image} alt={item.title} className="w-full h-full object-contain" />
                </div>
              )}
              
              <textarea
                className="w-full text-sm p-3 rounded-md border border-input bg-background resize-y min-h-[80px] placeholder:text-muted-foreground/50 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                placeholder="Adicione notas ou interprete os achados biológicos deste gráfico..."
                value={item.textNotes || ''}
                onChange={(e) => updateReportItemText(item.id, e.target.value)}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function ResultsPanel({ className, projectId, files = [], sessions = [] }: { className?: string; projectId: string; files?: any[]; sessions?: any[] }) {
  const activeTab = useResultsStore((state: any) => 
    ['files', 'history', 'report', 'results'].includes(state.activeTab) ? state.activeTab : 'results'
  );
  const setActiveTab = useResultsStore((state: any) => state.setActiveTab);
  const pendingNotifications = useResultsStore((state: any) => state.pendingNotifications);
  const clearNotifications = useResultsStore((state: any) => state.clearNotifications);

  const handleTabChange = (tabId: string) => {
    setActiveTab(tabId);
    if (tabId === "results") clearNotifications();
  };

  return (
    <div className={cn("flex h-full flex-col border-l border-border bg-background", className)}>
      <Tabs value={activeTab} onValueChange={handleTabChange} className="flex h-full flex-col">
        <div className="shrink-0 border-b border-border px-3 pt-3">
          <TabsList className="w-full">
            <TabsTrigger value="results" className="flex-1 relative">
              Results
              {pendingNotifications.length > 0 && activeTab !== "results" && (
                <span className="absolute right-2 top-1.5 size-2 rounded-full bg-primary" />
              )}
            </TabsTrigger>
            <TabsTrigger value="report" className="flex-1">
              Report
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
            <TabsContent value="report" className="mt-0">
               <ReportTab projectId={projectId} />
            </TabsContent>
            <TabsContent value="files" className="mt-0">
              <FilesTab files={files} />
            </TabsContent>
            <TabsContent value="history" className="mt-0">
              <HistoryTab sessions={sessions} />
            </TabsContent>
          </div>
        </div>
      </Tabs>
    </div>
  )
}
