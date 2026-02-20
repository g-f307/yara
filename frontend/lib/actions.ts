"use server";

import { prisma } from "@/lib/db";
import { revalidatePath } from "next/cache";

// Temporary fallback userId until Clerk is integrated
const TEMP_USER_ID = "temp-user-id";

export async function getUserProjects() {
    try {
        const projects = await prisma.project.findMany({
            where: {
                userId: TEMP_USER_ID,
            },
            orderBy: {
                updatedAt: "desc",
            },
            include: {
                _count: {
                    select: { files: true, sessions: true }
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
        // Ensure temporary user exists
        await prisma.user.upsert({
            where: { clerkId: TEMP_USER_ID },
            update: {},
            create: {
                clerkId: TEMP_USER_ID,
                email: "demo@yara.app",
                name: "Demo User",
            }
        });

        const project = await prisma.project.create({
            data: {
                name,
                description,
                userId: TEMP_USER_ID,
            },
        });

        revalidatePath("/dashboard");
        return { success: true, project };
    } catch (error) {
        console.error("Failed to create project:", error);
        return { success: false, error: "Failed to create project" };
    }
}
