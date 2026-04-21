import { prisma } from './prisma'

export async function generateIncidentNumber(organizationId: string): Promise<string> {
  const year = new Date().getFullYear()
  const result = await prisma.$transaction(async (tx) => {
    const count = await tx.incident.count({
      where: { organizationId, incidentNumber: { startsWith: `INC-${year}-` } },
    })
    return `INC-${year}-${String(count + 1).padStart(3, '0')}`
  })
  return result
}

export async function generateAssetNumber(organizationId: string): Promise<string> {
  const result = await prisma.$transaction(async (tx) => {
    const count = await tx.asset.count({ where: { organizationId } })
    return `AST-${String(count + 1).padStart(3, '0')}`
  })
  return result
}

export async function generateRiskNumber(organizationId: string): Promise<string> {
  const year = new Date().getFullYear()
  const result = await prisma.$transaction(async (tx) => {
    const count = await tx.risk.count({
      where: { organizationId, riskNumber: { startsWith: `RSK-${year}-` } },
    })
    return `RSK-${year}-${String(count + 1).padStart(3, '0')}`
  })
  return result
}
