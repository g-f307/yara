CREATE TYPE "AnalysisRunState" AS ENUM (
  'REQUESTED',
  'VALIDATING',
  'QUEUED',
  'RUNNING',
  'SUCCEEDED',
  'FAILED',
  'CANCELLED'
);

CREATE TABLE "AnalysisRun" (
  "id" TEXT NOT NULL,
  "projectId" TEXT NOT NULL,
  "requestedByUserId" TEXT NOT NULL,
  "parentRunId" TEXT,
  "method" TEXT NOT NULL,
  "state" "AnalysisRunState" NOT NULL DEFAULT 'REQUESTED',
  "inputManifestJson" JSONB NOT NULL,
  "metadataVersionId" TEXT,
  "parametersJson" JSONB NOT NULL,
  "softwareVersionsJson" JSONB NOT NULL,
  "seed" INTEGER,
  "resultJson" JSONB,
  "outputManifestJson" JSONB,
  "errorCode" TEXT,
  "errorMessage" TEXT,
  "requestId" TEXT NOT NULL,
  "requestedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "startedAt" TIMESTAMP(3),
  "finishedAt" TIMESTAMP(3),
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL,
  CONSTRAINT "AnalysisRun_pkey" PRIMARY KEY ("id")
);

CREATE INDEX "AnalysisRun_projectId_requestedAt_idx" ON "AnalysisRun"("projectId", "requestedAt");
CREATE INDEX "AnalysisRun_projectId_state_idx" ON "AnalysisRun"("projectId", "state");
CREATE INDEX "AnalysisRun_parentRunId_idx" ON "AnalysisRun"("parentRunId");
CREATE INDEX "AnalysisRun_metadataVersionId_idx" ON "AnalysisRun"("metadataVersionId");
CREATE INDEX "AnalysisRun_requestedByUserId_idx" ON "AnalysisRun"("requestedByUserId");

ALTER TABLE "AnalysisRun" ADD CONSTRAINT "AnalysisRun_projectId_fkey"
  FOREIGN KEY ("projectId") REFERENCES "Project"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "AnalysisRun" ADD CONSTRAINT "AnalysisRun_requestedByUserId_fkey"
  FOREIGN KEY ("requestedByUserId") REFERENCES "User"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
ALTER TABLE "AnalysisRun" ADD CONSTRAINT "AnalysisRun_parentRunId_fkey"
  FOREIGN KEY ("parentRunId") REFERENCES "AnalysisRun"("id") ON DELETE SET NULL ON UPDATE CASCADE;
ALTER TABLE "AnalysisRun" ADD CONSTRAINT "AnalysisRun_metadataVersionId_fkey"
  FOREIGN KEY ("metadataVersionId") REFERENCES "MetadataVersion"("id") ON DELETE SET NULL ON UPDATE CASCADE;

CREATE FUNCTION prevent_terminal_analysis_run_mutation() RETURNS trigger AS $$
BEGIN
  IF OLD."state" IN ('SUCCEEDED', 'FAILED', 'CANCELLED') AND ROW(
    NEW."projectId", NEW."requestedByUserId", NEW."parentRunId", NEW."method",
    NEW."inputManifestJson", NEW."metadataVersionId", NEW."parametersJson",
    NEW."softwareVersionsJson", NEW."seed", NEW."resultJson",
    NEW."outputManifestJson", NEW."errorCode", NEW."errorMessage",
    NEW."requestId", NEW."requestedAt", NEW."startedAt", NEW."finishedAt"
  ) IS DISTINCT FROM ROW(
    OLD."projectId", OLD."requestedByUserId", OLD."parentRunId", OLD."method",
    OLD."inputManifestJson", OLD."metadataVersionId", OLD."parametersJson",
    OLD."softwareVersionsJson", OLD."seed", OLD."resultJson",
    OLD."outputManifestJson", OLD."errorCode", OLD."errorMessage",
    OLD."requestId", OLD."requestedAt", OLD."startedAt", OLD."finishedAt"
  ) THEN
    RAISE EXCEPTION 'AnalysisRun terminal é imutável';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER "AnalysisRun_terminal_immutable"
BEFORE UPDATE ON "AnalysisRun"
FOR EACH ROW EXECUTE FUNCTION prevent_terminal_analysis_run_mutation();
