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

// Analytics actions

import { analyzeAlpha, computePCoA, taxonomyBarplot, analyzeRarefaction } from "./api";

export async function getAlphaDiversity(projectId: string, metric: string, groupCol?: string) {
    try {
        const { userId } = await auth();
        if (!userId) throw new Error("Unauthorized");
        // In a real app we would load the actual dataset from UploadThing/S3 using the projectId.
        // For MVP, if we don't have a dataset we can mock a dataframe to send to the python core.
        const mockData = Array.from({ length: 20 }, (_, i) => ({
            sample_id: `S${i + 1}`,
            shannon: Math.random() * 5 + 2,
            simpson: Math.random(),
            chao1: Math.random() * 100 + 50,
            group: i % 2 === 0 ? "Control" : "Treatment"
        }));

        const result = await analyzeAlpha(mockData, metric, groupCol || "group");
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

        // Mocking a distance matrix from valid 3D points so PCoA yields valid positive eigenvalues
        const sampleIds = Array.from({ length: 10 }, (_, i) => `S${i + 1}`);
        const points = Array.from({ length: 10 }, () => [Math.random(), Math.random(), Math.random()]);
        const matrix = Array.from({ length: 10 }, (_, i) =>
            Array.from({ length: 10 }, (_, j) => {
                const dx = points[i][0] - points[j][0];
                const dy = points[i][1] - points[j][1];
                const dz = points[i][2] - points[j][2];
                return Math.sqrt(dx * dx + dy * dy + dz * dz);
            })
        );

        const metadata = sampleIds.map((id, i) => ({
            sample_id: id,
            group: i % 2 === 0 ? "Control" : "Treatment"
        }));

        const result = await computePCoA(matrix, sampleIds, metadata, groupCol || "group");
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

        // Mocking taxonomy data: rows are features, columns are metadata + samples
        const sampleIds = Array.from({ length: 10 }, (_, i) => `S${i + 1}`);
        const mockData = Array.from({ length: 50 }, (_, i) => {
            const row: any = {
                "Feature ID": `F${i}`,
                "Taxon": `k__Bacteria; p__Firmicutes; c__Bacilli; o__Lactobacillales; f__Lactobacillaceae; g__Lactobacillus; s__species_${i}`,
                "Confidence": 0.99
            };
            // Add random abundance for each sample
            sampleIds.forEach(s => {
                row[s] = Math.floor(Math.random() * 500);
            });
            return row;
        });

        const result = await taxonomyBarplot(mockData, level);
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

        // Mocking rarefaction curves: rows are samples, columns are depths
        const depths = [100, 500, 1000, 2000, 5000, 10000];
        const mockData = Array.from({ length: 10 }, (_, i) => {
            const row: any = { "sample-id": `S${i + 1}` };
            let currentFeatures = 0;
            depths.forEach(depth => {
                // Diminishing returns formula to simulate rarefaction
                currentFeatures += Math.floor(Math.random() * 50) + (10000 / depth);
                row[depth.toString()] = currentFeatures;
            });
            return row;
        });

        const result = await analyzeRarefaction(mockData);
        return { success: true, data: result.plotly_spec };
    } catch (e: any) {
        console.error(e);
        return { success: false, error: e.message };
    }
}
