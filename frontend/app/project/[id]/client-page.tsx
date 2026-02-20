import { getUserProjects } from "@/lib/actions"
import ProjectLayoutClient from "./client-page"
import { SidebarProject } from "@/components/project-sidebar"

export default async function ProjectPage({
  params,
}: {
  params: { id: string }
}) {
  const projectId = params.id

  // Fetch real database projects using Prisma Server Action
  const dbProjects = await getUserProjects()

  // Map Prisma output to UI prop requirement
  const sidebarProjects: SidebarProject[] = dbProjects.map((p) => ({
    id: p.id,
    name: p.name,
    date: p.updatedAt.toLocaleDateString("en-US", { month: "short", year: "numeric" }),
    fileType: ".qzv", // Will be dynamic once we add files
    fileCount: p._count.files,
    analysisCount: p._count.sessions,
  }))

  return <ProjectLayoutClient projectId={projectId} projects={sidebarProjects} />
}
