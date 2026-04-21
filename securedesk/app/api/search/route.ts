import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { prisma } from '@/lib/prisma'
import { NextResponse } from 'next/server'

export async function GET(req: Request) {
  const session = await getServerSession(authOptions)
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  const orgId = (session.user as { organizationId?: string }).organizationId!

  const q = new URL(req.url).searchParams.get('q')?.trim()
  if (!q || q.length < 2) return NextResponse.json({ incidents: [], assets: [], risks: [] })

  const [incidents, assets, risks] = await Promise.all([
    prisma.incident.findMany({
      where: {
        organizationId: orgId,
        deletedAt: null,
        OR: [
          { title: { contains: q, mode: 'insensitive' } },
          { incidentNumber: { contains: q, mode: 'insensitive' } },
          { reportedBy: { contains: q, mode: 'insensitive' } },
          { assignedTo: { contains: q, mode: 'insensitive' } },
        ],
      },
      select: { id: true, incidentNumber: true, title: true, severity: true, status: true },
      orderBy: { createdAt: 'desc' },
      take: 5,
    }),

    prisma.asset.findMany({
      where: {
        organizationId: orgId,
        deletedAt: null,
        OR: [
          { name: { contains: q, mode: 'insensitive' } },
          { assetNumber: { contains: q, mode: 'insensitive' } },
          { description: { contains: q, mode: 'insensitive' } },
          { businessOwner: { contains: q, mode: 'insensitive' } },
        ],
      },
      select: { id: true, assetNumber: true, name: true, type: true, classification: true },
      orderBy: { createdAt: 'desc' },
      take: 5,
    }),

    prisma.risk.findMany({
      where: {
        organizationId: orgId,
        deletedAt: null,
        OR: [
          { title: { contains: q, mode: 'insensitive' } },
          { riskNumber: { contains: q, mode: 'insensitive' } },
          { owner: { contains: q, mode: 'insensitive' } },
          { threat: { contains: q, mode: 'insensitive' } },
        ],
      },
      select: { id: true, riskNumber: true, title: true, riskScore: true, status: true },
      orderBy: { riskScore: 'desc' },
      take: 5,
    }),
  ])

  return NextResponse.json({ incidents, assets, risks })
}
