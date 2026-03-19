"use client"

import { useState, useTransition } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Plus, FileText, FlaskConical, MoreHorizontal, Pencil, Trash2, ChevronLeft, ChevronRight } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { CreateProjectDialog } from "@/components/create-project-dialog"
import { RenameProjectDialog } from "@/components/rename-project-dialog"
import { DeleteProjectDialog } from "@/components/delete-project-dialog"
import { deleteProject } from "@/lib/actions"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

const PAGE_SIZE = 12

interface Project {
  id: string
  name: string
  date: string
  fileCount: number
  analysisCount: number
}

function ProjectCard({ project, onDeleted }: { project: Project; onDeleted: () => void }) {
  const [isPending, startTransition] = useTransition()
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const router = useRouter()

  return (
    <div
      className={cn(
        "group relative rounded-lg border border-border bg-card p-4 transition-all hover:border-primary/30 hover:shadow-sm",
        isPending && "opacity-50 pointer-events-none"
      )}
    >
      {/* Card link */}
      <Link href={`/project/${project.id}`} className="block">
        <div className="flex items-start justify-between mb-3 pr-6">
          <h2 className="text-sm font-semibold text-card-foreground group-hover:text-primary transition-colors line-clamp-2 leading-snug">
            {project.name}
          </h2>
        </div>
        <p className="text-xs text-muted-foreground mb-3">{project.date}</p>
        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <FileText className="size-3.5" />
            {project.fileCount} {project.fileCount === 1 ? "arquivo" : "arquivos"}
          </span>
          <span className="flex items-center gap-1">
            <FlaskConical className="size-3.5" />
            {project.analysisCount} {project.analysisCount === 1 ? "análise" : "análises"}
          </span>
        </div>
      </Link>

      {/* Actions dropdown */}
      <div className="absolute right-3 top-3">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon-sm"
              className="h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity"
              onClick={(e) => e.preventDefault()}
            >
              <MoreHorizontal className="size-3.5" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-40">
            <RenameProjectDialog
              projectId={project.id}
              currentName={project.name}
              onRename={() => router.refresh()}
            >
              <DropdownMenuItem onSelect={(e) => e.preventDefault()}>
                <Pencil className="size-3.5 mr-2" />
                Renomear
              </DropdownMenuItem>
            </RenameProjectDialog>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              className="text-destructive focus:text-destructive"
              onSelect={() => setShowDeleteDialog(true)}
            >
              <Trash2 className="size-3.5 mr-2" />
              Excluir
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <DeleteProjectDialog 
        open={showDeleteDialog}
        onOpenChange={setShowDeleteDialog}
        projectId={project.id}
        projectName={project.name}
        onDeleted={onDeleted}
      />
    </div>
  )
}

export function DashboardProjectGrid({ projects }: { projects: Project[] }) {
  const [page, setPage] = useState(1)
  const router = useRouter()
  const totalPages = Math.max(1, Math.ceil(projects.length / PAGE_SIZE))
  const paginated = projects.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  return (
    <>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {paginated.map((project) => (
          <ProjectCard
            key={project.id}
            project={project}
            onDeleted={() => router.refresh()}
          />
        ))}

        {/* New project card */}
        <CreateProjectDialog>
          <button className="flex h-full min-h-[120px] w-full flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed border-muted-foreground/25 p-8 text-muted-foreground transition-colors hover:border-primary/50 hover:text-primary">
            <Plus className="size-8" strokeWidth={1.5} />
            <span className="text-sm font-medium">Criar novo projeto</span>
          </button>
        </CreateProjectDialog>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-3 mt-8">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
          >
            <ChevronLeft className="size-4" />
            Anterior
          </Button>
          <span className="text-sm text-muted-foreground">
            Página {page} de {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
          >
            Próxima
            <ChevronRight className="size-4" />
          </Button>
        </div>
      )}

      {/* Empty state */}
      {projects.length === 0 && (
        <div className="flex flex-col items-center justify-center py-20 text-center col-span-full">
          <p className="text-muted-foreground text-sm">Crie seu primeiro projeto usando o botão acima.</p>
        </div>
      )}
    </>
  )
}
