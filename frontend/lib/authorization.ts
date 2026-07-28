import { auth } from "@clerk/nextjs/server";
import { prisma } from "@/lib/db";
import authorizationPolicy from "./authorization-policy.cjs";

export const AUTHENTICATION_REQUIRED_MESSAGE = "Autenticação necessária.";
export const RESOURCE_NOT_FOUND_MESSAGE = "Recurso não encontrado.";

export class AuthenticationRequiredError extends Error {
    constructor() {
        super(AUTHENTICATION_REQUIRED_MESSAGE);
        this.name = "AuthenticationRequiredError";
    }
}

export class ResourceNotFoundError extends Error {
    constructor() {
        super(RESOURCE_NOT_FOUND_MESSAGE);
        this.name = "ResourceNotFoundError";
    }
}

export async function requireAuthenticatedDbUser() {
    const { userId: clerkId } = await auth();
    if (!clerkId) {
        throw new AuthenticationRequiredError();
    }

    const user = await prisma.user.findUnique({
        where: { clerkId },
    });
    if (!user) {
        throw new AuthenticationRequiredError();
    }

    return user;
}

export async function requireOwnedProject(projectId: string) {
    const user = await requireAuthenticatedDbUser();
    const project = await authorizationPolicy.findOwnedProject(
        prisma,
        user.id,
        projectId,
    );

    if (!project) {
        throw new ResourceNotFoundError();
    }

    return project;
}

export async function requireOwnedProjectWithFiles(projectId: string) {
    const user = await requireAuthenticatedDbUser();
    const project = await authorizationPolicy.findOwnedProject(
        prisma,
        user.id,
        projectId,
        true,
    );

    if (!project) {
        throw new ResourceNotFoundError();
    }

    return project;
}

export async function requireProjectFile(projectId: string, fileId: string) {
    const project = await requireOwnedProject(projectId);
    const file = await authorizationPolicy.findProjectFile(
        prisma,
        project.id,
        fileId,
    );

    if (!file) {
        throw new ResourceNotFoundError();
    }

    return file;
}
