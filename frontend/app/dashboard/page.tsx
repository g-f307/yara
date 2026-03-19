import Link from "next/link"
import { Plus, FileText, FlaskConical, MoreHorizontal, Pencil, Trash2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { YaraLogo } from "@/components/yara-logo"
import { getUserProjects } from "@/lib/actions"
import { ThemeToggle } from "@/components/theme-toggle"
import { UserButton } from "@clerk/nextjs"
import { CreateProjectDialog } from "@/components/create-project-dialog"
import { DashboardProjectGrid } from "@/components/dashboard-project-grid"

export default async function DashboardPage() {
  const dbProjects = await getUserProjects();

  const projects = dbProjects.map((p: any) => ({
    id: p.id,
    name: p.name,
    date: new Date(p.updatedAt).toLocaleDateString("pt-BR", { month: "short", year: "numeric" }),
    fileCount: p._count?.files ?? (p.files?.length ?? 0),
    analysisCount: p._count?.sessions ?? 0,
  }))

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <header className="flex items-center justify-between border-b border-border px-4 py-3 md:px-6">
        <YaraLogo />
        <div className="flex items-center gap-3">
          <ThemeToggle />
          <UserButton afterSignOutUrl="/" />
        </div>
      </header>

      <main className="flex-1 px-4 py-8 md:px-6 lg:px-8">
        <div className="mx-auto max-w-5xl">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-2xl font-semibold tracking-tight text-foreground">
                Meus Projetos
              </h1>
              <p className="mt-1 text-sm text-muted-foreground">
                {projects.length === 0
                  ? "Nenhum projeto ainda. Crie o primeiro para começar."
                  : `${projects.length} projeto${projects.length !== 1 ? "s" : ""} encontrado${projects.length !== 1 ? "s" : ""}`}
              </p>
            </div>
            <CreateProjectDialog>
              <Button className="bg-primary text-primary-foreground hover:bg-primary/90">
                <Plus className="size-4" />
                Novo Projeto
              </Button>
            </CreateProjectDialog>
          </div>

          <DashboardProjectGrid projects={projects} />
        </div>
      </main>
    </div>
  )
}
