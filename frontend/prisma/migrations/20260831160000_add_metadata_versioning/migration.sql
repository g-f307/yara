CREATE TYPE "MetadataSeverity" AS ENUM ('BLOCKING', 'WARNING', 'INFO');

CREATE TABLE "MetadataVersion" (
    "id" TEXT NOT NULL,
    "backendVersionId" TEXT NOT NULL,
    "projectId" TEXT NOT NULL,
    "artifactId" TEXT NOT NULL,
    "parentVersionId" TEXT,
    "sha256" TEXT NOT NULL,
    "schemaJson" JSONB NOT NULL,
    "source" TEXT NOT NULL,
    "templateId" TEXT NOT NULL,
    "templateVersion" TEXT NOT NULL,
    "createdByUserId" TEXT,
    "active" BOOLEAN NOT NULL DEFAULT false,
    "createdAt" TIMESTAMP(3) NOT NULL,
    CONSTRAINT "MetadataVersion_pkey" PRIMARY KEY ("id")
);

CREATE TABLE "MetadataValidation" (
    "id" TEXT NOT NULL,
    "metadataVersionId" TEXT NOT NULL,
    "rulesVersion" TEXT NOT NULL,
    "severity" "MetadataSeverity" NOT NULL,
    "code" TEXT NOT NULL,
    "columnName" TEXT,
    "affectedSamplesJson" JSONB NOT NULL,
    "message" TEXT NOT NULL,
    "suggestion" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "MetadataValidation_pkey" PRIMARY KEY ("id")
);

CREATE TABLE "MetadataTemplate" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "version" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    CONSTRAINT "MetadataTemplate_pkey" PRIMARY KEY ("id")
);

CREATE TABLE "MetadataTemplateField" (
    "id" TEXT NOT NULL,
    "templateId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "dataType" TEXT NOT NULL,
    "unit" TEXT,
    "requirement" TEXT NOT NULL,
    "vocabularyJson" JSONB NOT NULL,
    "position" INTEGER NOT NULL,
    CONSTRAINT "MetadataTemplateField_pkey" PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX "MetadataVersion_backendVersionId_key" ON "MetadataVersion"("backendVersionId");
CREATE INDEX "MetadataVersion_projectId_createdAt_idx" ON "MetadataVersion"("projectId", "createdAt");
CREATE INDEX "MetadataVersion_projectId_active_idx" ON "MetadataVersion"("projectId", "active");
CREATE INDEX "MetadataVersion_artifactId_idx" ON "MetadataVersion"("artifactId");
CREATE INDEX "MetadataValidation_metadataVersionId_severity_idx" ON "MetadataValidation"("metadataVersionId", "severity");
CREATE UNIQUE INDEX "MetadataTemplateField_templateId_name_key" ON "MetadataTemplateField"("templateId", "name");
CREATE INDEX "MetadataTemplateField_templateId_position_idx" ON "MetadataTemplateField"("templateId", "position");

ALTER TABLE "MetadataVersion" ADD CONSTRAINT "MetadataVersion_projectId_fkey" FOREIGN KEY ("projectId") REFERENCES "Project"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "MetadataVersion" ADD CONSTRAINT "MetadataVersion_artifactId_fkey" FOREIGN KEY ("artifactId") REFERENCES "Artifact"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "MetadataVersion" ADD CONSTRAINT "MetadataVersion_parentVersionId_fkey" FOREIGN KEY ("parentVersionId") REFERENCES "MetadataVersion"("id") ON DELETE SET NULL ON UPDATE CASCADE;
ALTER TABLE "MetadataVersion" ADD CONSTRAINT "MetadataVersion_createdByUserId_fkey" FOREIGN KEY ("createdByUserId") REFERENCES "User"("id") ON DELETE SET NULL ON UPDATE CASCADE;
ALTER TABLE "MetadataValidation" ADD CONSTRAINT "MetadataValidation_metadataVersionId_fkey" FOREIGN KEY ("metadataVersionId") REFERENCES "MetadataVersion"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "MetadataTemplateField" ADD CONSTRAINT "MetadataTemplateField_templateId_fkey" FOREIGN KEY ("templateId") REFERENCES "MetadataTemplate"("id") ON DELETE CASCADE ON UPDATE CASCADE;
