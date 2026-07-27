"use strict";

async function findOwnedProject(prismaClient, userId, projectId, includeFiles = false) {
    return prismaClient.project.findFirst({
        where: {
            id: projectId,
            userId,
        },
        ...(includeFiles
            ? {
                include: {
                    files: true,
                },
            }
            : {}),
    });
}

async function findProjectFile(prismaClient, projectId, fileId) {
    return prismaClient.file.findFirst({
        where: {
            id: fileId,
            projectId,
        },
    });
}

module.exports = {
    findOwnedProject,
    findProjectFile,
};
