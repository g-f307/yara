import type { File, PrismaClient, Project } from "@prisma/client";

type ProjectWithFiles = Project & { files: File[] };

declare function findOwnedProject(
    prismaClient: PrismaClient,
    userId: string,
    projectId: string,
    includeFiles?: false,
): Promise<Project | null>;

declare function findOwnedProject(
    prismaClient: PrismaClient,
    userId: string,
    projectId: string,
    includeFiles: true,
): Promise<ProjectWithFiles | null>;

declare function findProjectFile(
    prismaClient: PrismaClient,
    projectId: string,
    fileId: string,
): Promise<File | null>;

declare const authorizationPolicy: {
    findOwnedProject: typeof findOwnedProject;
    findProjectFile: typeof findProjectFile;
};

export = authorizationPolicy;
