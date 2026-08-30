CREATE TYPE "ArtifactStatus" AS ENUM ('VALID', 'REJECTED', 'FAILED');
CREATE TYPE "ArtifactKind" AS ENUM ('FEATURE_TABLE', 'TAXONOMY', 'METADATA', 'PHYLOGENETIC_TREE', 'ALPHA_VECTOR', 'DISTANCE_MATRIX', 'PCOA_ORDINATION', 'RAREFACTION_CURVE', 'UNKNOWN');
CREATE TYPE "CompatibilityStatus" AS ENUM ('COMPATIBLE', 'INCOMPATIBLE', 'AMBIGUOUS', 'UNKNOWN');

CREATE TABLE "Artifact" (
    "id" TEXT NOT NULL,
    "manifestArtifactId" TEXT NOT NULL,
    "projectId" TEXT NOT NULL,
    "fileId" TEXT,
    "physicalName" TEXT NOT NULL,
    "sha256" TEXT NOT NULL,
    "size" INTEGER NOT NULL,
    "extension" TEXT NOT NULL,
    "status" "ArtifactStatus" NOT NULL,
    "kind" "ArtifactKind" NOT NULL,
    "semanticType" TEXT,
    "format" TEXT,
    "qiimeUuid" TEXT,
    "qiimeVersion" TEXT,
    "classifierVersion" TEXT NOT NULL,
    "confidence" DOUBLE PRECISION NOT NULL,
    "selected" BOOLEAN NOT NULL DEFAULT false,
    "metadataJson" JSONB NOT NULL,
    "classifiedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    CONSTRAINT "Artifact_pkey" PRIMARY KEY ("id")
);

CREATE TABLE "ArtifactCompatibility" (
    "id" TEXT NOT NULL,
    "projectId" TEXT NOT NULL,
    "sourceArtifactId" TEXT NOT NULL,
    "targetArtifactId" TEXT NOT NULL,
    "status" "CompatibilityStatus" NOT NULL,
    "reasonCode" TEXT NOT NULL,
    "reasonMessage" TEXT NOT NULL,
    "evidenceJson" JSONB,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    CONSTRAINT "ArtifactCompatibility_pkey" PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX "Artifact_manifestArtifactId_key" ON "Artifact"("manifestArtifactId");
CREATE UNIQUE INDEX "Artifact_fileId_key" ON "Artifact"("fileId");
CREATE INDEX "Artifact_projectId_kind_idx" ON "Artifact"("projectId", "kind");
CREATE INDEX "Artifact_projectId_selected_idx" ON "Artifact"("projectId", "selected");
CREATE UNIQUE INDEX "ArtifactCompatibility_sourceArtifactId_targetArtifactId_reasonCode_key" ON "ArtifactCompatibility"("sourceArtifactId", "targetArtifactId", "reasonCode");
CREATE INDEX "ArtifactCompatibility_projectId_status_idx" ON "ArtifactCompatibility"("projectId", "status");

ALTER TABLE "Artifact" ADD CONSTRAINT "Artifact_projectId_fkey" FOREIGN KEY ("projectId") REFERENCES "Project"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "Artifact" ADD CONSTRAINT "Artifact_fileId_fkey" FOREIGN KEY ("fileId") REFERENCES "File"("id") ON DELETE SET NULL ON UPDATE CASCADE;
ALTER TABLE "ArtifactCompatibility" ADD CONSTRAINT "ArtifactCompatibility_projectId_fkey" FOREIGN KEY ("projectId") REFERENCES "Project"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "ArtifactCompatibility" ADD CONSTRAINT "ArtifactCompatibility_sourceArtifactId_fkey" FOREIGN KEY ("sourceArtifactId") REFERENCES "Artifact"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "ArtifactCompatibility" ADD CONSTRAINT "ArtifactCompatibility_targetArtifactId_fkey" FOREIGN KEY ("targetArtifactId") REFERENCES "Artifact"("id") ON DELETE CASCADE ON UPDATE CASCADE;
