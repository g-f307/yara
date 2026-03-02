"use server";

import { prisma } from "@/lib/db";
import { revalidatePath } from "next/cache";

import { auth } from "@clerk/nextjs/server";

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

        // Ensure user exists (in real app, this should be a Clerk webhook)
        const dbUser = await prisma.user.upsert({
            where: { clerkId: userId },
            update: {},
            create: {
                clerkId: userId,
                email: "user@example.com", // Temporary fallback
                name: "Yara User",
            }
        });

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
        revalidatePath(`/project/[id]`);
        return { success: true, file };
    } catch (error: any) {
        console.error("Failed to save project file:", error);
        return { success: false, error: error.message || "Failed to save file to project DB" };
    }
}

// Analytics actions

import { analyzeAlpha, computePCoA, taxonomyBarplot, analyzeRarefaction, syncProjectFiles } from "./api";

async function ensureBackendSynched(projectId: string) {
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
