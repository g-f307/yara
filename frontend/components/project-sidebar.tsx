"use client"

import { useTheme } from "next-themes"
import { Plus, Sun, Moon, FileText, FlaskConical, LayoutDashboard, MoreHorizontal, Pencil, Trash2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { YaraLogo } from "@/components/yara-logo"
import { CreateProjectDialog } from "@/components/create-project-dialog"
import { RenameProjectDialog } from "@/components/rename-project-dialog"
import { DeleteProjectDialog } from "@/components/delete-project-dialog"
import { useUser, UserButton } from "@clerk/nextjs"
import { useRouter } from "next/navigation"
import { useState, useTransition } from "react"
import { deleteProject } from "@/lib/actions"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import Link from "next/link"

export interface SidebarProject {
  id: string
  name: string
  date: string
  fileType: string
  fileCount: number
  analysisCount: number
  files?: Array<{ id: string; name: string; type: string; url: string }>
}

const fileTypeColors: Record<string, string> = {
  ".qzv": "bg-primary/10 text-primary dark:bg-primary/20",
  ".tsv": "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400",
  ".biom": "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400",
  ".qza": "bg-sky-100 text-sky-700 dark:bg-sky-900/30 dark:text-sky-400",
}

function ProjectCard({
  project,
  active,
  onClick,
  onDeleted,
}: {
  project: SidebarProject
  active: boolean
  onClick: () => void
  onDeleted: () => void
}) {
  const [isPending, startTransition] = useTransition()
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const router = useRouter()

  return (
    <div
      className={cn(
        "group relative flex w-full flex-col gap-1.5 rounded-lg border border-transparent px-3 py-2.5 text-left transition-colors",
        active ? "border-l-2 border-l-primary bg-accent" : "hover:bg-muted",
        isPending && "opacity-50 pointer-events-none"
      )}
    >
      {/* Clickable area */}
      <button onClick={onClick} className="flex flex-col gap-1.5 w-full text-left">
        <p className="text-sm font-medium text-foreground leading-tight truncate pr-6">
          {project.name}
        </p>
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">{project.date}</span>
          <span
            className={cn(
              "inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-medium",
              fileTypeColors[project.fileType] || "bg-muted text-muted-foreground"
            )}
          >
            {project.fileType}
          </span>
        </div>
        <div className="flex items-center gap-3 text-[11px] text-muted-foreground pb-1">
          <span className="flex items-center gap-1">
            <FileText className="size-3" />
            {project.fileCount} arquivos
          </span>
          <span className="flex items-center gap-1">
            <FlaskConical className="size-3" />
            {project.analysisCount} análises
          </span>
        </div>
      </button>

      {/* Actions dropdown */}
      <div className="absolute right-2 top-2 opacity-0 group-hover:opacity-100 transition-opacity">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon-sm" className="h-6 w-6" onClick={(e) => e.stopPropagation()}>
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
        onDeleted={() => {
          if (active) onDeleted()
          else router.refresh() 
        }}
      />

      {/* Files sub-list when active */}
      {active && project.files && project.files.length > 0 && (
        <div className="mt-2 flex flex-col gap-1 border-t border-border/50 pt-2">
          {project.files.map(f => (
            <div key={f.id} className="flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground transition-colors cursor-default">
              <span className={cn(
                "inline-flex shrink-0 items-center justify-center rounded size-4 text-[8px] font-bold",
                fileTypeColors[f.type] || "bg-muted text-foreground"
              )}>
                {f.type.replace('.', '')}
              </span>
              <span className="truncate" title={f.name}>{f.name}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export function ProjectSidebar({
  projects,
  activeProjectId,
  onSelectProject,
}: {
  projects: SidebarProject[]
  activeProjectId: string | null
  onSelectProject: (id: string) => void
}) {
  const { theme, setTheme } = useTheme()
  const { user } = useUser()
  const router = useRouter()

  const displayName = user?.fullName || user?.username || user?.firstName || "Usuário"
  const initials = displayName
    .split(" ")
    .map((n: string) => n[0])
    .join("")
    .slice(0, 2)
    .toUpperCase()

  return (
    <div className="flex h-full w-[260px] flex-col border-r border-border bg-sidebar">
      {/* Logo — links back to dashboard */}
      <div className="flex items-center justify-between px-4 pt-4 pb-2">
        <Link href="/dashboard" className="hover:opacity-80 transition-opacity" title="Voltar ao painel">
          <YaraLogo />
        </Link>
        <Button
          variant="ghost"
          size="icon-sm"
          title="Ir ao painel"
          asChild
        >
          <Link href="/dashboard">
            <LayoutDashboard className="size-4 text-muted-foreground" />
          </Link>
        </Button>
      </div>

      {/* New project button */}
      <div className="px-3 py-2">
        <CreateProjectDialog>
          <Button
            className="w-full bg-primary text-primary-foreground hover:bg-primary/90"
            size="default"
          >
            <Plus className="size-4" />
            Novo Projeto
          </Button>
        </CreateProjectDialog>
      </div>

      <div className="px-3 pt-2 pb-1">
        <p className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
          Projetos
        </p>
      </div>

      <ScrollArea className="flex-1 px-2 h-full min-h-0 w-full overflow-y-auto">
        <div className="flex flex-col gap-0.5 py-1">
          {projects.length === 0 && (
            <p className="px-3 py-4 text-xs text-muted-foreground text-center">
              Nenhum projeto ainda.
            </p>
          )}
          {projects.map((project) => (
            <ProjectCard
              key={project.id}
              project={project}
              active={activeProjectId === project.id}
              onClick={() => onSelectProject(project.id)}
              onDeleted={() => router.push("/dashboard")}
            />
          ))}
        </div>
      </ScrollArea>

      {/* User section */}
      <div className="flex items-center gap-3 border-t border-border px-4 py-3">
        <UserButton afterSignOutUrl="/" />
        <div className="flex-1 min-w-0">
          <p className="truncate text-sm font-medium text-foreground">
            {displayName}
          </p>
          {user?.primaryEmailAddress && (
            <p className="truncate text-xs text-muted-foreground">
              {user.primaryEmailAddress.emailAddress}
            </p>
          )}
        </div>
        <Button
          variant="ghost"
          size="icon-sm"
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          aria-label="Alternar tema"
        >
          <Sun className="size-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
          <Moon className="absolute size-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
        </Button>
      </div>
    </div>
  )
}
