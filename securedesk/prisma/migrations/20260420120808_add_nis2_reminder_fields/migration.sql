-- AlterTable
ALTER TABLE "Incident" ADD COLUMN     "reminder24hSentAt" TIMESTAMP(3),
ADD COLUMN     "reminder30dSentAt" TIMESTAMP(3),
ADD COLUMN     "reminder72hSentAt" TIMESTAMP(3);
