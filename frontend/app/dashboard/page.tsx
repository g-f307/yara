"use client"

import Link from "next/link"
import { useTheme } from "next-themes"
import { Plus, FileText, FlaskConical, Sun, Moon } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { YaraLogo } from "@/components/yara-logo"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { mockProjects } from "@/lib/mock-data"

const fileTypeColors: Record<string, string> = {
  ".qzv": "bg-primary/10 text-primary dark:bg-primary/20",
  ".tsv": "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400",
  ".biom": "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400",
  ".qza": "bg-sky-100 text-sky-700 dark:bg-sky-900/30 dark:text-sky-400",
}

export default function DashboardPage() {
  const { theme, setTheme } = useTheme()

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <header className="flex items-center justify-between border-b border-border px-4 py-3 md:px-6">
        <YaraLogo />
        <div className="flex items-center gap-3">
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
      </header>

      <main className="flex-1 px-4 py-8 md:px-6 lg:px-8">
        <div className="mx-auto max-w-4xl">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-2xl font-semibold tracking-tight text-foreground">
                Projects
              </h1>
              <p className="mt-1 text-sm text-muted-foreground">
                Manage your metagenomic analysis projects
              </p>
            </div>
            <Button className="bg-primary text-primary-foreground hover:bg-primary/90">
              <Plus className="size-4" />
              New Project
            </Button>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {mockProjects.map((project) => (
              <Link
                key={project.id}
                href={`/project/${project.id}`}
                className="group rounded-lg border border-border bg-card p-4 transition-all hover:border-primary/30 hover:shadow-sm"
              >
                <div className="flex items-start justify-between mb-3">
                  <h2 className="text-sm font-semibold text-card-foreground group-hover:text-primary transition-colors">
                    {project.name}
                  </h2>
                  <span
                    className={cn(
                      "inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-medium",
                      fileTypeColors[project.fileType] ||
                        "bg-muted text-muted-foreground"
                    )}
                  >
                    {project.fileType}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground mb-3">
                  {project.date}
                </p>
                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <FileText className="size-3.5" />
                    {project.fileCount} files
                  </span>
                  <span className="flex items-center gap-1">
                    <FlaskConical className="size-3.5" />
                    {project.analysisCount} analyses
                  </span>
                </div>
              </Link>
            ))}

            {/* New Project card */}
            <button className="flex flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed border-muted-foreground/25 p-8 text-muted-foreground transition-colors hover:border-primary/50 hover:text-primary">
              <Plus className="size-8" strokeWidth={1.5} />
              <span className="text-sm font-medium">Create new project</span>
            </button>
          </div>
        </div>
      </main>
    </div>
  )
}
