"use client"

import { useMemo, useState, useTransition } from "react"
import { AlertTriangle, CheckCircle2, ChevronLeft, ChevronRight, History, Plus, RotateCcw, Save, ShieldAlert } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { confirmProjectMetadataVersion, previewProjectMetadata, restoreProjectMetadataVersion } from "@/lib/actions"

const PAGE_SIZE = 10

export function MetadataWorkspace({ projectId, initialWorkspace }: { projectId: string; initialWorkspace: any | null }) {
  const [workspace, setWorkspace] = useState(initialWorkspace)
  const [columns, setColumns] = useState<string[]>(initialWorkspace?.columns ?? [])
  const [rows, setRows] = useState<Record<string, string>[]>(initialWorkspace?.rows ?? [])
  const [templateId, setTemplateId] = useState(initialWorkspace?.validation?.template?.id ?? "generic")
  const [preview, setPreview] = useState<any>(null)
  const [page, setPage] = useState(0)
  const [isPending, startTransition] = useTransition()

  const pageCount = Math.max(1, Math.ceil(rows.length / PAGE_SIZE))
  const visibleRows = rows.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)
  const validation = preview ?? workspace?.validation
  const diagnosticsByColumn = useMemo(() => {
    const grouped = new Map<string, any[]>()
    for (const diagnostic of validation?.diagnostics ?? []) {
      if (!diagnostic.column_name) continue
      grouped.set(diagnostic.column_name, [...(grouped.get(diagnostic.column_name) ?? []), diagnostic])
    }
    return grouped
  }, [validation])

  if (!workspace) {
    return (
      <div className="rounded-lg border border-dashed p-6 text-center text-sm text-muted-foreground">
        Selecione ou envie um arquivo classificado como metadata para habilitar a validação MIxS/MIMARKS.
      </div>
    )
  }

  const updateCell = (rowIndex: number, column: string, value: string) => {
    const absoluteIndex = page * PAGE_SIZE + rowIndex
    setRows((current) => current.map((row, index) => index === absoluteIndex ? { ...row, [column]: value } : row))
    setPreview(null)
  }

  const runPreview = () => {
    startTransition(async () => {
      const result = await previewProjectMetadata(projectId, templateId, columns, rows)
      if (!result.success) {
        toast.error(result.error || "Não foi possível validar a metadata.")
        return
      }
      setPreview(result.preview)
      toast.success("Preview validado. Nenhuma mudança foi persistida.")
    })
  }

  const addMissingTemplateFields = () => {
    const template = workspace.templates.find((item: any) => item.id === templateId)
    const additions = (template?.fields ?? []).map((field: any) => field.name).filter((name: string) => !columns.includes(name))
    if (additions.length === 0) {
      toast.info("Todos os campos desse template já estão presentes.")
      return
    }
    setColumns((current) => [...current, ...additions])
    setRows((current) => current.map((row) => ({ ...row, ...Object.fromEntries(additions.map((name: string) => [name, ""])) })))
    setPreview(null)
    toast.info("Colunas adicionadas ao rascunho. Revise os valores e gere o preview.")
  }

  const confirmVersion = () => {
    if (!preview) {
      toast.error("Gere o preview antes de confirmar uma nova versão.")
      return
    }
    const active = workspace.versions.find((version: any) => version.id === workspace.active_version_id)
    startTransition(async () => {
      const result = await confirmProjectMetadataVersion(
        projectId,
        active.artifact_id,
        active.id,
        templateId,
        columns,
        rows,
      )
      if (!result.success) {
        toast.error(result.error || "Não foi possível criar a versão.")
        return
      }
      setWorkspace(result.workspace)
      setColumns(result.workspace.columns)
      setRows(result.workspace.rows)
      setPreview(null)
      toast.success("Nova versão imutável criada e ativada.")
    })
  }

  const restore = (versionId: string) => {
    if (!window.confirm("Restaurar esta versão criará uma nova versão ativa. O histórico será preservado. Continuar?")) return
    startTransition(async () => {
      const result = await restoreProjectMetadataVersion(projectId, versionId)
      if (!result.success) {
        toast.error(result.error || "Não foi possível restaurar a versão.")
        return
      }
      setWorkspace(result.workspace)
      setColumns(result.workspace.columns)
      setRows(result.workspace.rows)
      setTemplateId(result.workspace.validation.template.id)
      setPreview(null)
      setPage(0)
      toast.success("Versão restaurada como uma nova revisão imutável.")
    })
  }

  return (
    <div className="space-y-4">
      <div className="rounded-lg border bg-card p-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-sm font-semibold">Prontidão da metadata</p>
            <p className="text-xs text-muted-foreground">Regras {validation.readiness.rules_version}; o score não substitui os diagnósticos.</p>
          </div>
          <div className={cn(
            "flex size-14 items-center justify-center rounded-full border-4 text-sm font-bold",
            validation.readiness.ready ? "border-emerald-500 text-emerald-600" : "border-amber-500 text-amber-600",
          )}>
            {validation.readiness.score}
          </div>
        </div>
        <div className="mt-3 grid grid-cols-1 gap-1 sm:grid-cols-2">
          {validation.readiness.items.map((item: any) => (
            <div key={item.id} className="flex items-center gap-2 text-xs">
              {item.passed ? <CheckCircle2 className="size-3.5 text-emerald-500" /> : <AlertTriangle className="size-3.5 text-amber-500" />}
              <span>{item.label}</span><span className="ml-auto text-muted-foreground">{item.weight}%</span>
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-lg border bg-card p-3">
        <label htmlFor="metadata-template" className="text-xs font-medium">Template de orientação</label>
        <select
          id="metadata-template"
          className="mt-1 w-full rounded-md border bg-background px-2 py-2 text-sm"
          value={templateId}
          onChange={(event) => { setTemplateId(event.target.value); setPreview(null) }}
        >
          {workspace.templates.map((template: any) => <option key={template.id} value={template.id}>{template.name}</option>)}
        </select>
        <p className="mt-1 text-[11px] text-muted-foreground">
          {workspace.templates.find((template: any) => template.id === templateId)?.description}
        </p>
        <div className="mt-2 flex flex-wrap gap-1">
          {workspace.templates.find((template: any) => template.id === templateId)?.fields.map((field: any) => (
            <span key={field.name} title={field.description} className={cn(
              "rounded px-1.5 py-0.5 text-[10px]",
              field.requirement === "MINIMUM" ? "bg-red-500/10 text-red-600" : field.requirement === "RECOMMENDED" ? "bg-amber-500/10 text-amber-600" : "bg-muted text-muted-foreground",
            )}>{field.name} · {field.requirement.toLowerCase()}</span>
          ))}
        </div>
        <Button className="mt-2" variant="outline" size="sm" disabled={isPending} onClick={addMissingTemplateFields}>
          <Plus className="mr-1 size-3.5" />Adicionar campos ausentes ao rascunho
        </Button>
      </div>

      <div className="overflow-hidden rounded-lg border bg-card">
        <div className="flex items-center justify-between border-b px-3 py-2">
          <div>
            <p className="text-sm font-semibold">Tabela de metadata</p>
            <p className="text-[11px] text-muted-foreground">{rows.length} linhas; colunas não reconhecidas são preservadas.</p>
          </div>
          <div className="flex gap-1">
            <Button variant="outline" size="sm" disabled={isPending} onClick={runPreview}>Validar preview</Button>
            <Button size="sm" disabled={isPending || !preview} onClick={confirmVersion}><Save className="mr-1 size-3.5" />Confirmar versão</Button>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-max text-xs">
            <thead className="bg-muted/50">
              <tr>{columns.map((column) => <th key={column} className="border-b px-2 py-2 text-left font-medium">{column}{diagnosticsByColumn.has(column) && <ShieldAlert className="ml-1 inline size-3 text-amber-500" />}</th>)}</tr>
            </thead>
            <tbody>
              {visibleRows.map((row, rowIndex) => (
                <tr key={page * PAGE_SIZE + rowIndex} className="border-b last:border-0">
                  {columns.map((column) => (
                    <td key={column} className="p-1">
                      <input
                        aria-label={`${column}, linha ${page * PAGE_SIZE + rowIndex + 1}`}
                        className="min-w-28 rounded border border-transparent bg-transparent px-1.5 py-1 focus:border-input focus:outline-none"
                        value={row[column] ?? ""}
                        onChange={(event) => updateCell(rowIndex, column, event.target.value)}
                      />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="flex items-center justify-end gap-2 border-t px-3 py-2 text-xs">
          <Button variant="ghost" size="icon-sm" disabled={page === 0} onClick={() => setPage((value) => value - 1)}><ChevronLeft className="size-4" /></Button>
          Página {page + 1} de {pageCount}
          <Button variant="ghost" size="icon-sm" disabled={page + 1 >= pageCount} onClick={() => setPage((value) => value + 1)}><ChevronRight className="size-4" /></Button>
        </div>
      </div>

      <div className="rounded-lg border bg-card">
        <div className="border-b px-3 py-2"><p className="text-sm font-semibold">Diagnósticos</p></div>
        <div className="divide-y">
          {(validation.diagnostics ?? []).length === 0 && <p className="p-3 text-xs text-emerald-600">Nenhum diagnóstico para as regras atuais.</p>}
          {(validation.diagnostics ?? []).map((diagnostic: any, index: number) => (
            <div key={`${diagnostic.code}-${diagnostic.column_name}-${index}`} className="p-3 text-xs">
              <div className="flex items-center gap-2">
                <span className={cn("rounded px-1.5 py-0.5 font-medium", diagnostic.severity === "BLOCKING" ? "bg-red-500/10 text-red-600" : diagnostic.severity === "WARNING" ? "bg-amber-500/10 text-amber-600" : "bg-sky-500/10 text-sky-600")}>{diagnostic.severity}</span>
                <code>{diagnostic.code}</code>{diagnostic.column_name && <span className="text-muted-foreground">· {diagnostic.column_name}</span>}
              </div>
              <p className="mt-1">{diagnostic.message}</p>
              <p className="text-muted-foreground">Ação: {diagnostic.suggestion}</p>
              {diagnostic.affected_samples?.length > 0 && <p className="mt-1 truncate text-[10px] text-muted-foreground">Afetadas: {diagnostic.affected_samples.join(", ")}</p>}
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-lg border bg-card">
        <div className="flex items-center gap-2 border-b px-3 py-2"><History className="size-4" /><p className="text-sm font-semibold">Histórico imutável</p></div>
        <div className="divide-y">
          {[...workspace.versions].reverse().map((version: any) => (
            <div key={version.id} className="flex items-center gap-3 p-3 text-xs">
              <div className="min-w-0 flex-1">
                <p className="font-medium">{version.source}{version.id === workspace.active_version_id && <span className="ml-2 text-emerald-600">ativa</span>}</p>
                <p className="truncate text-muted-foreground">{new Date(version.created_at).toLocaleString("pt-BR")} · {version.sha256.slice(0, 12)} · {version.template_id}</p>
              </div>
              {version.id !== workspace.active_version_id && <Button variant="outline" size="sm" disabled={isPending} onClick={() => restore(version.id)}><RotateCcw className="mr-1 size-3.5" />Restaurar</Button>}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
