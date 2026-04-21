import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { prisma } from '@/lib/prisma'
import { NextResponse } from 'next/server'

export async function GET() {
  const session = await getServerSession(authOptions)
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  const orgId = (session.user as { organizationId?: string }).organizationId!

  const now = new Date()
  const thirtyDaysAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)

  const [
    incidentsBySeverity,
    openCount,
    nis2Active,
    assetsOverdue,
    recentIncidents,
    incidentsLast30,
    riskOpenCount,
    riskCriticalCount,
    riskOverdueCount,
    topRisks,
    riskMatrixData,
  ] = await Promise.all([
    // Count open incidents grouped by severity
    prisma.incident.groupBy({
      by: ['severity'],
      where: { organizationId: orgId, deletedAt: null, status: { not: 'CLOSED' } },
      _count: { _all: true },
    }),

    // Total open (not closed)
    prisma.incident.count({
      where: { organizationId: orgId, deletedAt: null, status: { not: 'CLOSED' } },
    }),

    // NIS2 active incidents with timer info
    prisma.incident.findMany({
      where: { organizationId: orgId, deletedAt: null, nis2Active: true },
      select: {
        id: true,
        incidentNumber: true,
        title: true,
        severity: true,
        status: true,
        nis2StartedAt: true,
        nis2EarlyWarningSentAt: true,
        nis2ReportSentAt: true,
      },
      orderBy: { nis2StartedAt: 'asc' },
    }),

    // Assets with nextReviewAt in the past
    prisma.asset.findMany({
      where: {
        organizationId: orgId,
        deletedAt: null,
        nextReviewAt: { lt: now },
      },
      select: {
        id: true,
        assetNumber: true,
        name: true,
        type: true,
        nextReviewAt: true,
      },
      orderBy: { nextReviewAt: 'asc' },
      take: 10,
    }),

    // Recent 5 incidents
    prisma.incident.findMany({
      where: { organizationId: orgId, deletedAt: null },
      select: {
        id: true,
        incidentNumber: true,
        title: true,
        severity: true,
        status: true,
        createdAt: true,
      },
      orderBy: { createdAt: 'desc' },
      take: 5,
    }),

    // Incidents per day last 30 days
    prisma.incident.findMany({
      where: {
        organizationId: orgId,
        deletedAt: null,
        createdAt: { gte: thirtyDaysAgo },
      },
      select: { createdAt: true },
    }),

    // Risk: open + in_treatment count
    prisma.risk.count({
      where: { organizationId: orgId, deletedAt: null, status: { in: ['OPEN', 'IN_TREATMENT'] } },
    }),

    // Risk: critical (score >= 15), any non-closed status
    prisma.risk.count({
      where: { organizationId: orgId, deletedAt: null, riskScore: { gte: 15 }, status: { not: 'CLOSED' } },
    }),

    // Risk: overdue review (nextReviewAt in past, not closed)
    prisma.risk.count({
      where: { organizationId: orgId, deletedAt: null, nextReviewAt: { lt: now }, status: { not: 'CLOSED' } },
    }),

    // Top 5 highest-score open risks
    prisma.risk.findMany({
      where: { organizationId: orgId, deletedAt: null, status: { in: ['OPEN', 'IN_TREATMENT'] } },
      select: { id: true, riskNumber: true, title: true, riskScore: true, category: true, owner: true, treatment: true, status: true },
      orderBy: { riskScore: 'desc' },
      take: 5,
    }),

    // All open risks probability+impact for mini matrix
    prisma.risk.findMany({
      where: { organizationId: orgId, deletedAt: null, status: { in: ['OPEN', 'IN_TREATMENT'] } },
      select: { probability: true, impact: true },
    }),
  ])

  // Build 30-day chart data
  const dayMap: Record<string, number> = {}
  for (let i = 29; i >= 0; i--) {
    const d = new Date(now.getTime() - i * 24 * 60 * 60 * 1000)
    const key = d.toISOString().slice(0, 10)
    dayMap[key] = 0
  }
  for (const inc of incidentsLast30) {
    const key = inc.createdAt.toISOString().slice(0, 10)
    if (key in dayMap) dayMap[key]++
  }
  const chartData = Object.entries(dayMap).map(([date, count]) => ({ date, count }))

  const severityMap: Record<string, number> = {}
  for (const row of incidentsBySeverity) {
    severityMap[row.severity] = row._count?._all ?? 0
  }

  return NextResponse.json({
    data: {
      openCount,
      severityMap,
      nis2Active,
      assetsOverdue,
      recentIncidents,
      chartData,
      riskOpenCount,
      riskCriticalCount,
      riskOverdueCount,
      topRisks,
      riskMatrixData,
    },
  })
}
