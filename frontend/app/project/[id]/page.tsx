import { getUserProjects, getProjectSession } from "@/lib/actions"
import ProjectLayoutClient from "./client-page"
import { SidebarProject } from "@/components/project-sidebar"
import { syncProjectFiles } from "@/lib/api"

export const dynamic = "force-dynamic";

export default async function ProjectPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id: projectId } = await params

  // Fetch real database projects using Prisma Server Action
  const dbProjects = await getUserProjects()

  // Map Prisma output to UI prop requirement
  const sidebarProjects: SidebarProject[] = dbProjects.map((p) => ({
    id: p.id,
    name: p.name,
    date: p.updatedAt.toLocaleDateString("en-US", { month: "short", year: "numeric" }),
    fileType: p.files.length > 0 ? p.files[0].type : ".qzv",
    fileCount: p.files.length,
    analysisCount: p._count.sessions,
    files: p.files.map(f => ({ id: f.id, name: f.name, type: f.type, url: f.url }))
  }))

  const currentProject = sidebarProjects.find(p => p.id === projectId)
  if (currentProject && currentProject.files && currentProject.files.length > 0) {
    try {
      await syncProjectFiles(projectId, currentProject.files)
    } catch (e) {
      console.error("Failed to sync project files to backend", e)
    }
  }

  // Fetch past chat session
  const sessionResult = await getProjectSession(projectId);
  const initialMessages = sessionResult.success ? sessionResult.messages : [];
  console.log("INITIAL MESSAGES FROM DB:", initialMessages.length, initialMessages);

  return <ProjectLayoutClient projectId={projectId} projects={sidebarProjects} initialMessages={initialMessages} />
}
