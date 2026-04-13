"use server";

import { prisma } from "@/lib/db";
import { revalidatePath } from "next/cache";

import { auth, currentUser } from "@clerk/nextjs/server";

export async function getUserProjects() {
    try {
        const { userId } = await auth();
        if (!userId) {
            throw new Error("Unauthorized");
        }
        const projects = await prisma.project.findMany({
            where: {
                user: { clerkId: userId },
            },
            orderBy: {
                updatedAt: "desc",
            },
            include: {
                files: true,
                _count: {
                    select: { sessions: true }
                }
            }
        });
        return projects;
    } catch (error) {
        console.error("Failed to fetch projects:", error);
        return [];
    }
}

export async function createProject(name: string, description?: string) {
    try {
        const { userId } = await auth();
        if (!userId) throw new Error("Unauthorized");

        let dbUser = await prisma.user.findUnique({ where: { clerkId: userId } });
        if (!dbUser) {
            const clerkUser = await currentUser();
            const email = clerkUser?.emailAddresses[0]?.emailAddress;
            if (!email) {
                throw new Error("User not found. Please sign in again.");
            }

            dbUser = await prisma.user.create({
                data: {
                    clerkId: userId,
                    email,
                    name: clerkUser?.fullName || "Usuario YARA",
                }
            });
        }

        const project = await prisma.project.create({
            data: {
                name,
                description,
                userId: dbUser.id,
            },
        });

        revalidatePath("/dashboard");
        return { success: true, project };
    } catch (error) {
        console.error("Failed to create project:", error);
        return { success: false, error: "Failed to create project" };
    }
}

export async function deleteProject(projectId: string) {
    try {
        const { userId } = await auth();
        if (!userId) throw new Error("Unauthorized");

        const user = await prisma.user.findUnique({ where: { clerkId: userId } });
        if (!user) throw new Error("User not found");

        // Verify ownership before deleting
        const project = await prisma.project.findFirst({
            where: { id: projectId, userId: user.id },
        });
        if (!project) throw new Error("Project not found or access denied");

        await prisma.project.delete({ where: { id: projectId } });

        revalidatePath("/dashboard");
        return { success: true };
    } catch (error: any) {
        console.error("Failed to delete project:", error);
        return { success: false, error: error.message || "Failed to delete project" };
    }
}

export async function renameProject(projectId: string, newName: string) {
    try {
        const { userId } = await auth();
        if (!userId) throw new Error("Unauthorized");

        const user = await prisma.user.findUnique({ where: { clerkId: userId } });
        if (!user) throw new Error("User not found");

        // Verify ownership before updating
        const project = await prisma.project.findFirst({
            where: { id: projectId, userId: user.id },
        });
        if (!project) throw new Error("Project not found or access denied");

        const updated = await prisma.project.update({
            where: { id: projectId },
            data: { name: newName.trim() },
        });

        revalidatePath("/dashboard");
        revalidatePath(`/project/${projectId}`);
        return { success: true, project: updated };
    } catch (error: any) {
        console.error("Failed to rename project:", error);
        return { success: false, error: error.message || "Failed to rename project" };
    }
}

export async function createProjectFile(projectId: string, fileData: { name: string, type: string, url: string, key: string, size: number }) {
    try {
        const { userId } = await auth();
        if (!userId) throw new Error("Unauthorized");

        const file = await prisma.file.create({
            data: {
                ...fileData,
                projectId,
            },
        });

        // Revalidate project page to show new files in sidebar
        revalidatePath(`/project/${projectId}`);
        return { success: true, file };
    } catch (error: any) {
        console.error("Failed to save project file:", error);
        return { success: false, error: error.message || "Failed to save file to project DB" };
    }
}

// Analytics actions

import { analyzeAlpha, computePCoA, taxonomyBarplot, analyzeRarefaction, syncProjectFiles, compareStatistics } from "./api";

async function ensureBackendSynched(projectId: string) {
    const pythonCoreUrl = process.env.PYTHON_CORE_URL || "http://localhost:8000";

    // Fast check if Python backend already has the files downloaded
    try {
        const check = await fetch(`${pythonCoreUrl}/api/project/status/${projectId}`, { cache: 'no-store' });
        if (check.ok) {
            const { synced } = await check.json();
            if (synced) return; // Exit early, skipping database query and sync trigger
        }
    } catch (e) {
        console.warn("Could not check python backend sync status, falling back to force sync.", e);
    }

    const project = await prisma.project.findUnique({
        where: { id: projectId },
        include: { files: true }
    });
    
    if (project && project.files.length > 0) {
        await syncProjectFiles(projectId, project.files.map((f: any) => ({
            id: f.id,
            name: f.name,
            type: f.type,
            url: f.url
        })));
    }
}

export async function getAlphaDiversity(projectId: string, metric: string, groupCol?: string) {
    try {
        const { userId } = await auth();
        if (!userId) throw new Error("Unauthorized");

        await ensureBackendSynched(projectId);

        const result: any = await analyzeAlpha(projectId, metric, groupCol || "group");
        if (result.error || result.data?.error) throw new Error(result.error || result.data.error);

        return { success: true, data: result.plotly_spec };
    } catch (e: any) {
        console.error(e);
        return { success: false, error: e.message };
    }
}

export async function getBetaDiversity(projectId: string, groupCol?: string) {
    try {
        const { userId } = await auth();
        if (!userId) throw new Error("Unauthorized");

        await ensureBackendSynched(projectId);

        const result: any = await computePCoA(projectId, groupCol || "group");
        if (result.error || result.data?.error) throw new Error(result.error || result.data.error);

        return { success: true, data: result.plotly_spec };
    } catch (e: any) {
        console.error(e);
        return { success: false, error: e.message };
    }
}

export async function parseFile(projectId: string, fileId: string) {
    try {
        const { userId } = await auth();
        if (!userId) throw new Error("Unauthorized");

        await ensureBackendSynched(projectId);

        // MVP: Simulate network delay for python parsing a QIIME 2 QZV zip file
        await new Promise(resolve => setTimeout(resolve, 1500));

        return {
            success: true,
            message: "Data successfully parsed into analysis matrix. You may now request Alpha and Beta diversity plots, as well as Taxonomy and Rarefaction curves."
        };
    } catch (e: any) {
        console.error(e);
        return { success: false, error: e.message };
    }
}

export async function getTaxonomy(projectId: string, level: string = "Phylum") {
    try {
        const { userId } = await auth();
        if (!userId) throw new Error("Unauthorized");

        await ensureBackendSynched(projectId);

        const result: any = await taxonomyBarplot(projectId, level);
        if (result.error || result.data?.error) throw new Error(result.error || result.data.error);

        return { success: true, data: result.plotly_spec };
    } catch (e: any) {
        console.error(e);
        return { success: false, error: e.message };
    }
}

export async function getRarefaction(projectId: string) {
    try {
        const { userId } = await auth();
        if (!userId) throw new Error("Unauthorized");

        await ensureBackendSynched(projectId);

        const result: any = await analyzeRarefaction(projectId);
        if (result.error || result.data?.error) throw new Error(result.error || result.data.error);

        return { success: true, data: result.plotly_spec };
    } catch (e: any) {
        console.error(e);
        return { success: false, error: e.message };
    }
}

export async function getStatistics(
    projectId: string,
    groupCol?: string,
    metricCol?: string,
    test: "kruskal" | "mann_whitney" = "kruskal",
    group1?: string,
    group2?: string
) {
    try {
        const { userId } = await auth();
        if (!userId) throw new Error("Unauthorized");

        await ensureBackendSynched(projectId);

        const result: any = await compareStatistics(projectId, groupCol, metricCol, test, group1, group2);
        if (result.error || result.data?.error) throw new Error(result.error || result.data.error);

        return { success: true, data: result.plotly_spec };
    } catch (e: any) {
        console.error(e);
        return { success: false, error: e.message };
    }
}

export async function getProjectSession(projectId: string) {
    try {
        const { userId: clerkId } = await auth();
        if (!clerkId) throw new Error("Unauthorized");

        const user = await prisma.user.findUnique({ where: { clerkId } });
        if (!user) {
            return { success: false, messages: [] };
        }

        const session = await prisma.analysisSession.findFirst({
            where: {
                projectId,
                project: { userId: user.id }
            },
            orderBy: { createdAt: "desc" },
        });

        if (!session?.messages) {
            return { success: true, messages: [] };
        }

        try {
            const stored: any[] = JSON.parse(session.messages as string);
            const uiMessages: any[] = [];

            for (const m of stored) {
                if (!m?.id || !m?.role) continue;

                if (m.role === 'tool') continue; // legacy — skip bare tool entries

                if (m.role === 'user') {
                    // Ensure content is always the text string
                    const text = typeof m.content === 'string' && m.content
                        ? m.content
                        : (m.parts?.find((p: any) => p.type === 'text')?.text ?? '');
                    uiMessages.push({
                        id: m.id,
                        role: 'user',
                        content: text,
                        parts: [{ type: 'text', text }],
                    });
                    continue;
                }

                if (m.role === 'assistant') {
                    const text = typeof m.content === 'string' ? m.content : '';
                    const parts: any[] = text ? [{ type: 'text', text }] : [];
                    const toolInvocations: any[] = [];

                    // Restore toolInvocations — the new serializer stores them with state:'result'
                    if (Array.isArray(m.toolInvocations) && m.toolInvocations.length > 0) {
                        for (const ti of m.toolInvocations) {
                            // Force completed state so the LLM API never receives an unresolved call
                            const result = ti.result ?? { success: false, error: 'Resultado não disponível.' };
                            toolInvocations.push({ ...ti, state: 'result', result });
                            // Also add to parts so MessageBubble can render the graph card
                            if (!parts.find((p: any) => p.toolCallId === ti.toolCallId)) {
                                parts.push({
                                    type: `tool-${ti.toolName}`,
                                    toolCallId: ti.toolCallId,
                                    toolName: ti.toolName,
                                    args: ti.args,
                                    state: 'result',
                                    result,
                                });
                            }
                        }
                    } else if (Array.isArray(m.parts)) {
                        // Fallback: restore from parts (handles messages saved by older serializer)
                        for (const p of m.parts) {
                            if (p.type?.startsWith('tool-') && p.toolCallId) {
                                const result = p.result ?? { success: false, error: 'Resultado não disponível.' };
                                toolInvocations.push({
                                    state: 'result',
                                    toolCallId: p.toolCallId,
                                    toolName: p.toolName,
                                    args: p.args,
                                    result,
                                });
                                parts.push({ ...p, state: 'result', result });
                            }
                        }
                    }

                    uiMessages.push({ id: m.id, role: 'assistant', content: text, parts, toolInvocations });
                }
            }

            return { success: true, messages: uiMessages };
        } catch (e) {
            console.error("Failed to parse session messages", e);
            return { success: true, messages: [] };
        }
    } catch (error) {
        console.error("Failed to fetch project session:", error);
        return { success: false, messages: [] };
    }
}


import { generateReport as apiGenerateReport } from "./api";

export async function getProjectFiles(projectId: string) {
    try {
        const { userId } = await auth();
        if (!userId) throw new Error("Unauthorized");

        const files = await prisma.file.findMany({
            where: { projectId },
            orderBy: { createdAt: "desc" }
        });
        return { success: true, files };
    } catch (e: any) {
        return { success: false, files: [], error: e.message };
    }
}

export async function getProjectSessions(projectId: string) {
    try {
        const { userId } = await auth();
        if (!userId) throw new Error("Unauthorized");

        const sessions = await prisma.analysisSession.findMany({
            where: { projectId },
            orderBy: { createdAt: "desc" },
            take: 20
        });
        return { success: true, sessions };
    } catch (e: any) {
        return { success: false, sessions: [], error: e.message };
    }
}

export async function buildReport(projectId: string, format: "pdf" | "docx", items: any[]) {
    try {
        const { userId } = await auth();
        if (!userId) throw new Error("Unauthorized");

        const project = await prisma.project.findUnique({ where: { id: projectId } });
        if (!project) throw new Error("Project not found");

        const sections = items.map((item: any) => ({
            title: item.title || "Seção de Análise",
            content: item.textNotes || "",
            image_base64: item.base64Image || undefined,
            level: 2
        }));

        const result: any = await apiGenerateReport(sections, project.name, format);
        if (result.error || result.data?.error) throw new Error(result.error || result.data.error);

        return { success: true, downloadUrl: result.data?.path };
    } catch (e: any) {
        console.error(e);
        return { success: false, error: e.message };
    }
}
