"use strict";

const assert = require("node:assert/strict");
const { randomUUID } = require("node:crypto");
const { PrismaClient } = require("@prisma/client");

const prisma = new PrismaClient();

async function main() {
  const suffix = randomUUID();
  const user = await prisma.user.create({
    data: { clerkId: `migration-${suffix}`, email: `migration-${suffix}@example.invalid` },
  });
  const project = await prisma.project.create({ data: { name: "Projeto legado", userId: user.id } });

  try {
    const legacy = await prisma.analysisSummary.create({
      data: { projectId: project.id, type: "alpha", metric: "shannon", resultJson: { mean: 1.5 } },
    });
    assert.equal(legacy.projectId, project.id, "AnalysisSummary legado deve continuar disponível");

    const original = await prisma.analysisRun.create({
      data: {
        projectId: project.id,
        requestedByUserId: user.id,
        method: "alpha",
        state: "SUCCEEDED",
        inputManifestJson: { artifacts: [{ id: "artifact-1", sha256: "abc" }] },
        parametersJson: { metric: "shannon" },
        softwareVersionsJson: { yara: "test" },
        resultJson: { data: { mean: 1.5 } },
        outputManifestJson: {},
        requestId: randomUUID(),
        startedAt: new Date(),
        finishedAt: new Date(),
      },
    });

    await assert.rejects(
      prisma.analysisRun.update({ where: { id: original.id }, data: { resultJson: { changed: true } } }),
      /AnalysisRun terminal.*imutável/,
    );

    const reproduction = await prisma.analysisRun.create({
      data: {
        projectId: project.id,
        requestedByUserId: user.id,
        parentRunId: original.id,
        method: original.method,
        inputManifestJson: original.inputManifestJson,
        parametersJson: { metric: "simpson" },
        softwareVersionsJson: original.softwareVersionsJson,
        requestId: randomUUID(),
      },
    });
    assert.equal(reproduction.parentRunId, original.id);

    const otherProject = await prisma.project.create({ data: { name: "Outro projeto", userId: user.id } });
    const crossProject = await prisma.analysisRun.findFirst({ where: { id: original.id, projectId: otherProject.id } });
    assert.equal(crossProject, null, "consulta escopada não pode expor run de outro projeto");
  } finally {
    await prisma.project.deleteMany({ where: { userId: user.id } });
    await prisma.user.delete({ where: { id: user.id } });
  }
}

main()
  .then(() => console.log("analysis-run migration integration: ok"))
  .finally(() => prisma.$disconnect());
