-- CreateEnum
CREATE TYPE "RiskCategory" AS ENUM ('CONFIDENTIALITY', 'INTEGRITY', 'AVAILABILITY', 'PHYSICAL', 'LEGAL', 'OTHER');

-- CreateEnum
CREATE TYPE "RiskTreatment" AS ENUM ('ACCEPT', 'MITIGATE', 'TRANSFER', 'AVOID');

-- CreateEnum
CREATE TYPE "RiskStatus" AS ENUM ('OPEN', 'IN_TREATMENT', 'ACCEPTED', 'CLOSED');

-- CreateTable
CREATE TABLE "Risk" (
    "id" TEXT NOT NULL,
    "riskNumber" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "threat" TEXT,
    "vulnerability" TEXT,
    "category" "RiskCategory" NOT NULL DEFAULT 'OTHER',
    "probability" INTEGER NOT NULL,
    "impact" INTEGER NOT NULL,
    "riskScore" INTEGER NOT NULL,
    "treatment" "RiskTreatment" NOT NULL DEFAULT 'MITIGATE',
    "status" "RiskStatus" NOT NULL DEFAULT 'OPEN',
    "owner" TEXT NOT NULL,
    "mitigationPlan" TEXT,
    "residualProb" INTEGER,
    "residualImpact" INTEGER,
    "residualScore" INTEGER,
    "nextReviewAt" TIMESTAMP(3),
    "closedAt" TIMESTAMP(3),
    "organizationId" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "Risk_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "RiskAsset" (
    "riskId" TEXT NOT NULL,
    "assetId" TEXT NOT NULL,

    CONSTRAINT "RiskAsset_pkey" PRIMARY KEY ("riskId","assetId")
);

-- AddForeignKey
ALTER TABLE "Risk" ADD CONSTRAINT "Risk_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "Organization"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "RiskAsset" ADD CONSTRAINT "RiskAsset_riskId_fkey" FOREIGN KEY ("riskId") REFERENCES "Risk"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "RiskAsset" ADD CONSTRAINT "RiskAsset_assetId_fkey" FOREIGN KEY ("assetId") REFERENCES "Asset"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
