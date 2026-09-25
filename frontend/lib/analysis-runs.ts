import "server-only";

import { randomUUID } from "node:crypto";
import { prisma } from "@/lib/db";
import { ApiClientError } from "@/lib/api";
import { requireAuthenticatedDbUser, requireOwnedProject } from "@/lib/authorization";
import runPolicy from "@/lib/analysis-run-policy.cjs";

export const ANALYSIS_METHODS = [
  "alpha",
  "beta_pcoa",
  "beta_distances",
  "taxonomy_summary",
  "taxonomy_barplot",
  "rarefaction",
  "statistics",
  "qc",
] as const;

export type AnalysisMethod = (typeof ANALYSIS_METHODS)[number];

type RunState = "REQUESTED" | "VALIDATING" | "QUEUED" | "RUNNING" | "SUCCEEDED" | "FAILED" | "CANCELLED";

function jsonValue(value: unknown): any {
  return JSON.parse(JSON.stringify(value ?? null));
}

export function canTransition(from: RunState, to: RunState) {
  return runPolicy.canTransition(from, to);
}

async function transitionRun(id: string, from: RunState, to: RunState, data: Record<string, unknown> = {}) {
  if (!canTransition(from, to)) throw new Error(`Transição inválida de ${from} para ${to}.`);
  const updated = await prisma.analysisRun.updateMany({
    where: { id, state: from },
    data: { state: to, ...data } as any,
  });
  if (updated.count !== 1) throw new Error("A execução foi alterada concorrentemente ou já foi finalizada.");
}

async function snapshotInputs(projectId: string) {
  const artifacts = await prisma.artifact.findMany({
    where: { projectId, status: "VALID" },
    orderBy: [{ selected: "desc" }, { classifiedAt: "asc" }],
    select: {
      id: true,
      manifestArtifactId: true,
      kind: true,
      semanticType: true,
      sha256: true,
      size: true,
      selected: true,
      classifierVersion: true,
    },
  });
  return artifacts;
}

async function activeMetadataVersion(projectId: string) {
  return prisma.metadataVersion.findFirst({
    where: { projectId, active: true },
    select: { id: true, backendVersionId: true, sha256: true, templateId: true, templateVersion: true },
  });
}

function publicFailure(error: unknown, fallbackRequestId: string) {
  if (error instanceof ApiClientError) {
    return { code: error.code, message: error.message.split(" Identificador de suporte:")[0], requestId: error.requestId };
  }
  return {
    code: "ANALYSIS_FAILED",
    message: "A análise não pôde ser concluída.",
    requestId: fallbackRequestId,
  };
}

export async function executeAnalysisRun<T>(options: {
  projectId: string;
  method: AnalysisMethod;
  parameters: Record<string, unknown>;
  seed?: number | null;
  parentRunId?: string | null;
  execute: () => Promise<T>;
}) {
  const [project, user] = await Promise.all([
    requireOwnedProject(options.projectId),
    requireAuthenticatedDbUser(),
  ]);
  const [inputs, metadata] = await Promise.all([
    snapshotInputs(project.id),
    activeMetadataVersion(project.id),
  ]);
  if (inputs.length === 0) throw new Error("Nenhum artefato científico válido foi encontrado para registrar a execução.");

  if (options.parentRunId) {
    const parent = await prisma.analysisRun.findFirst({
      where: { id: options.parentRunId, projectId: project.id },
      select: { id: true },
    });
    if (!parent) throw new Error("Execução original não encontrada neste projeto.");
  }

  const requestId = randomUUID();
  const run = await prisma.analysisRun.create({
    data: {
      projectId: project.id,
      requestedByUserId: user.id,
      parentRunId: options.parentRunId ?? null,
      method: options.method,
      inputManifestJson: jsonValue({ artifacts: inputs, metadata }),
      metadataVersionId: metadata?.id ?? null,
      parametersJson: jsonValue(options.parameters),
      softwareVersionsJson: jsonValue({ yara: "0.1.0", node: process.version, rules: "analysis-run-1.0.0" }),
      seed: options.seed ?? null,
      requestId,
    },
  });

  try {
    await transitionRun(run.id, "REQUESTED", "VALIDATING");
    await transitionRun(run.id, "VALIDATING", "QUEUED");
    await transitionRun(run.id, "QUEUED", "RUNNING", { startedAt: new Date() });
    const response: any = await options.execute();
    const metadataBackendId = response?.data?.metadata_version_id;
    if (metadataBackendId && metadata && metadata.backendVersionId !== metadataBackendId) {
      throw new Error("A versão de metadata utilizada diverge do snapshot registrado.");
    }
    await transitionRun(run.id, "RUNNING", "SUCCEEDED", {
      resultJson: jsonValue(response),
      outputManifestJson: jsonValue({ plotly: Boolean(response?.plotly_spec), metadata_version_id: metadataBackendId ?? null }),
      finishedAt: new Date(),
    });
    return { response, runId: run.id };
  } catch (error) {
    const failure = publicFailure(error, requestId);
    await transitionRun(run.id, "RUNNING", "FAILED", {
      errorCode: failure.code,
      errorMessage: failure.message,
      requestId: failure.requestId,
      finishedAt: new Date(),
    });
    throw error;
  }
}

export async function listOwnedAnalysisRuns(projectId: string) {
  const project = await requireOwnedProject(projectId);
  return prisma.analysisRun.findMany({
    where: { projectId: project.id },
    orderBy: { requestedAt: "desc" },
    include: { metadataVersion: { select: { backendVersionId: true, sha256: true } } },
  });
}

export async function getOwnedAnalysisRun(projectId: string, runId: string) {
  const project = await requireOwnedProject(projectId);
  return prisma.analysisRun.findFirst({
    where: { id: runId, projectId: project.id },
    include: { metadataVersion: { select: { backendVersionId: true, sha256: true } } },
  });
}
