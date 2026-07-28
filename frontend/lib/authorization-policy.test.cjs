"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const {
    findOwnedProject,
    findProjectFile,
} = require("./authorization-policy.cjs");

function createPrismaMock() {
    const calls = {
        projects: [],
        files: [],
    };

    return {
        calls,
        client: {
            project: {
                findFirst: async (query) => {
                    calls.projects.push(query);
                    const { id, userId } = query.where;
                    if (id !== "project-a" || userId !== "user-a") return null;
                    return {
                        id,
                        userId,
                        ...(query.include?.files
                            ? { files: [{ id: "file-a", projectId: id }] }
                            : {}),
                    };
                },
            },
            file: {
                findFirst: async (query) => {
                    calls.files.push(query);
                    const { id, projectId } = query.where;
                    if (id !== "file-a" || projectId !== "project-a") return null;
                    return { id, projectId };
                },
            },
        },
    };
}

test("returns a project owned by the authenticated database user", async () => {
        const prisma = createPrismaMock();

        const project = await findOwnedProject(
            prisma.client,
            "user-a",
            "project-a",
        );

        assert.equal(project.id, "project-a");
        assert.deepEqual(prisma.calls.projects[0], {
            where: {
                id: "project-a",
                userId: "user-a",
            },
        });
});

test("returns null for a project owned by another user", async () => {
        const prisma = createPrismaMock();

        const project = await findOwnedProject(
            prisma.client,
            "user-b",
            "project-a",
        );

        assert.equal(project, null);
});

test("returns null for a nonexistent project using the same query shape", async () => {
        const prisma = createPrismaMock();

        const project = await findOwnedProject(
            prisma.client,
            "user-a",
            "missing-project",
        );

        assert.equal(project, null);
        assert.deepEqual(prisma.calls.projects[0], {
            where: {
                id: "missing-project",
                userId: "user-a",
            },
        });
});

test("includes files without removing the ownership predicate", async () => {
        const prisma = createPrismaMock();

        const project = await findOwnedProject(
            prisma.client,
            "user-a",
            "project-a",
            true,
        );

        assert.equal(project.files.length, 1);
        assert.deepEqual(prisma.calls.projects[0], {
            where: {
                id: "project-a",
                userId: "user-a",
            },
            include: {
                files: true,
            },
        });
});

test("requires a file to belong to the authorized project", async () => {
        const prisma = createPrismaMock();

        const file = await findProjectFile(
            prisma.client,
            "project-a",
            "file-a",
        );
        const foreignFile = await findProjectFile(
            prisma.client,
            "project-b",
            "file-a",
        );

        assert.equal(file.id, "file-a");
        assert.equal(foreignFile, null);
        assert.deepEqual(prisma.calls.files[0], {
            where: {
                id: "file-a",
                projectId: "project-a",
            },
        });
});
