"use client"

import { useTheme } from "next-themes"
import { Plus, Sun, Moon, FileText, FlaskConical } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { YaraLogo } from "@/components/yara-logo"

export interface SidebarProject {
  id: string
  name: string
  date: string
  fileType: string
  fileCount: number
  analysisCount: number
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
}: {
  project: SidebarProject
  active: boolean
  onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "flex w-full flex-col gap-1.5 rounded-lg border border-transparent px-3 py-2.5 text-left transition-colors",
        active
          ? "border-l-2 border-l-primary bg-accent"
          : "hover:bg-muted"
      )}
      aria-current={active ? "page" : undefined}
    >
      <p className="text-sm font-medium text-foreground leading-tight truncate">
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
      <div className="flex items-center gap-3 text-[11px] text-muted-foreground">
        <span className="flex items-center gap-1">
          <FileText className="size-3" />
          {project.fileCount} files
        </span>
        <span className="flex items-center gap-1">
          <FlaskConical className="size-3" />
          {project.analysisCount} analyses
        </span>
      </div>
    </button>
  )
}

export function ProjectSidebar({
  projects,
  activeProjectId,
  onSelectProject,
  collapsed = false,
}: {
  projects: SidebarProject[]
  activeProjectId: string | null
  onSelectProject: (id: string) => void
  collapsed?: boolean
}) {
  const { theme, setTheme } = useTheme()

  if (collapsed) {
    return (
      <div className="flex h-full w-14 flex-col items-center border-r border-border bg-sidebar py-4">
        <YaraLogo collapsed />
        <div className="mt-4">
          <Button
            size="icon-sm"
            className="bg-primary text-primary-foreground hover:bg-primary/90"
            aria-label="New project"
          >
            <Plus className="size-4" />
          </Button>
        </div>
        <div className="mt-4 flex flex-1 flex-col items-center gap-1">
          {projects.map((p) => (
            <button
              key={p.id}
              onClick={() => onSelectProject(p.id)}
              className={cn(
                "flex size-9 items-center justify-center rounded-lg text-xs font-bold transition-colors",
                activeProjectId === p.id
                  ? "bg-accent text-primary"
                  : "text-muted-foreground hover:bg-muted"
              )}
              aria-label={p.name}
              title={p.name}
            >
              {p.name.charAt(0)}
            </button>
          ))}
        </div>
        <div className="flex flex-col items-center gap-2">
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            aria-label="Toggle theme"
          >
            <Sun className="size-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
            <Moon className="absolute size-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
          </Button>
          <Avatar className="size-8">
            <AvatarFallback className="bg-accent text-primary text-xs font-medium">
              DR
            </AvatarFallback>
          </Avatar>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-full w-[260px] flex-col border-r border-border bg-sidebar">
      <div className="flex items-center justify-between px-4 pt-4 pb-2">
        <YaraLogo />
      </div>

      <div className="px-3 py-2">
        <Button
          className="w-full bg-primary text-primary-foreground hover:bg-primary/90"
          size="default"
        >
          <Plus className="size-4" />
          New Project
        </Button>
      </div>

      <div className="px-3 pt-2 pb-1">
        <p className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
          Projects
        </p>
      </div>

      <ScrollArea className="flex-1 px-2">
        <div className="flex flex-col gap-0.5 py-1">
          {projects.map((project) => (
            <ProjectCard
              key={project.id}
              project={project}
              active={activeProjectId === project.id}
              onClick={() => onSelectProject(project.id)}
            />
          ))}
        </div>
      </ScrollArea>

      <div className="flex items-center gap-3 border-t border-border px-4 py-3">
        <Avatar className="size-8">
          <AvatarFallback className="bg-accent text-primary text-xs font-medium">
            DR
          </AvatarFallback>
        </Avatar>
        <div className="flex-1 min-w-0">
          <p className="truncate text-sm font-medium text-foreground">
            Dr. Researcher
          </p>
        </div>
        <Button
          variant="ghost"
          size="icon-sm"
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          aria-label="Toggle theme"
        >
          <Sun className="size-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
          <Moon className="absolute size-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
        </Button>
      </div>
    </div>
  )
}
