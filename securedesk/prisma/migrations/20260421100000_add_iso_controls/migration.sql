-- CreateEnum
CREATE TYPE "ControlStatus" AS ENUM ('NOT_REVIEWED', 'APPLICABLE', 'PLANNED', 'EXCLUDED', 'NOT_APPLICABLE');

-- CreateTable
CREATE TABLE "IsoControl" (
    "id" TEXT NOT NULL,
    "controlNumber" TEXT NOT NULL,
    "status" "ControlStatus" NOT NULL DEFAULT 'NOT_REVIEWED',
    "justification" TEXT,
    "owner" TEXT,
    "organizationId" TEXT NOT NULL,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "IsoControl_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "IsoControl_organizationId_controlNumber_key" ON "IsoControl"("organizationId", "controlNumber");

-- AddForeignKey
ALTER TABLE "IsoControl" ADD CONSTRAINT "IsoControl_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "Organization"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
