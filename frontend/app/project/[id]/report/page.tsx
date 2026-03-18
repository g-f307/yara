"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { useParams } from "next/navigation"
import { ArrowLeft, Download, FileText, Loader2, Trash2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { YaraLogo } from "@/components/yara-logo"
import { useResultsStore } from "@/store/use-results-store"
import { getUserProjects, buildReport } from "@/lib/actions"

export default function ReportPage() {
  const params = useParams()
  const projectId = params.id as string

  const reportItems = useResultsStore((s: any) => s.reportItems)
  const removeReportItem = useResultsStore((s: any) => s.removeReportItem)

  const [project, setProject] = useState<any>(null)
  const [exporting, setExporting] = useState<"pdf" | "docx" | null>(null)
  const [exportError, setExportError] = useState<string | null>(null)

  useEffect(() => {
    getUserProjects().then((r: any) => {
      if (r.projects) {
        const found = r.projects.find((p: any) => p.id === projectId)
        setProject(found ?? null)
      }
    })
  }, [projectId])

  const handleExport = async (format: "pdf" | "docx") => {
    setExporting(format)
    setExportError(null)
    try {
      const result: any = await buildReport(projectId, format, reportItems)
      if (!result.success) throw new Error(result.error || "Falha ao gerar relatório")
      if (result.downloadUrl) {
        window.open(result.downloadUrl, "_blank")
      }
    } catch (e: any) {
      setExportError(e.message)
    } finally {
      setExporting(null)
    }
  }

  const formatDate = (d: string | Date) =>
    new Date(d).toLocaleDateString("pt-BR", { day: "2-digit", month: "long", year: "numeric" })

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-10 flex items-center justify-between border-b border-border bg-background/80 backdrop-blur-sm px-4 py-3 md:px-6">
        <div className="flex items-center gap-3">
          <Link href={`/project/${projectId}`}>
            <Button variant="ghost" size="icon-sm" aria-label="Voltar ao projeto">
              <ArrowLeft className="size-4" />
            </Button>
          </Link>
          <YaraLogo />
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={reportItems.length === 0 || !!exporting}
            onClick={() => handleExport("docx")}
          >
            {exporting === "docx" ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <FileText className="size-4" />
            )}
            DOCX
          </Button>
          <Button
            size="sm"
            className="bg-primary text-primary-foreground hover:bg-primary/90"
            disabled={reportItems.length === 0 || !!exporting}
            onClick={() => handleExport("pdf")}
          >
            {exporting === "pdf" ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <Download className="size-4" />
            )}
            PDF
          </Button>
        </div>
      </header>

      {/* Report content */}
      <main className="mx-auto max-w-3xl px-4 py-8 md:px-6 lg:px-8">
        {/* Title section */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight text-foreground text-balance">
            {project?.name ?? "Carregando projeto..."}
          </h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Relatório de Análise Metagenômica
            {project?.createdAt && ` — Projeto criado em ${formatDate(project.createdAt)}`}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            {reportItems.length} {reportItems.length === 1 ? "análise incluída" : "análises incluídas"}
          </p>
        </div>

        {/* Export error */}
        {exportError && (
          <div className="mb-6 rounded-lg border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-destructive">
            {exportError}
          </div>
        )}

        {/* Empty state */}
        {reportItems.length === 0 && (
          <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border py-20 text-center">
            <FileText className="mb-3 size-10 text-muted-foreground/30" />
            <p className="text-sm font-medium text-muted-foreground">Nenhuma análise adicionada</p>
            <p className="mt-1 text-xs text-muted-foreground max-w-[280px]">
              Gere gráficos no chat e clique em "Add to Report" nas figuras para compilar este relatório.
            </p>
            <Link href={`/project/${projectId}`} className="mt-4">
              <Button variant="outline" size="sm">Voltar ao projeto</Button>
            </Link>
          </div>
        )}

        {/* Analyses */}
        {reportItems.length > 0 && (
          <section className="mb-8">
            <h2 className="text-lg font-semibold text-foreground mb-4">Análises Incluídas</h2>
            <div className="flex flex-col gap-6">
              {reportItems.map((item: any) => (
                <div
                  key={item.id}
                  className="rounded-lg border border-border bg-card overflow-hidden"
                >
                  <div className="flex items-center gap-2 border-b border-border px-4 py-3">
                    <div className="size-2 rounded-full bg-primary" />
                    <h3 className="text-sm font-medium text-card-foreground flex-1">
                      {item.title || "Análise"}
                    </h3>
                    <button
                      onClick={() => removeReportItem(item.id)}
                      className="text-muted-foreground hover:text-destructive transition-colors"
                      aria-label="Remover análise"
                    >
                      <Trash2 className="size-3.5" />
                    </button>
                  </div>
                  <div className="p-4">
                    {/* Notes */}
                    {item.textNotes && (
                      <p className="text-sm text-muted-foreground leading-relaxed mb-4">
                        {item.textNotes}
                      </p>
                    )}
                    {/* Chart image */}
                    {item.base64Image ? (
                      <img
                        src={item.base64Image}
                        alt={item.title}
                        className="w-full rounded-lg border border-border"
                      />
                    ) : (
                      <div className="flex items-center justify-center aspect-[16/9] rounded-lg bg-muted text-xs text-muted-foreground">
                        Imagem não disponível
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Footer */}
        <footer className="border-t border-border pt-6 text-center">
          <p className="text-xs text-muted-foreground">
            Relatório gerado pelo YARA — Your Assistant for Results Analysis
          </p>
          {project?.createdAt && (
            <p className="mt-1 text-xs text-muted-foreground">
              Exportado em {formatDate(new Date().toISOString())}
            </p>
          )}
        </footer>
      </main>
    </div>
  )
}
