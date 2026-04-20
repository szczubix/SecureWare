import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { prisma } from '@/lib/prisma'
import { generateIncidentNumber } from '@/lib/db-utils'
import { z } from 'zod'
import { NextResponse } from 'next/server'

const createSchema = z.object({
  title: z.string().min(3).max(200),
  description: z.string().min(10),
  severity: z.enum(['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']),
  category: z.enum(['UNAUTHORIZED_ACCESS', 'DATA_LEAK', 'AVAILABILITY', 'PHISHING', 'MALWARE', 'PHYSICAL', 'OTHER']),
  reportedBy: z.string().min(2),
  nis2Active: z.boolean().optional().default(false),
  assetIds: z.array(z.string()).optional(),
})

const VALID_SORT = ['createdAt', 'severity', 'status', 'incidentNumber'] as const
type SortField = typeof VALID_SORT[number]

export async function GET(req: Request) {
  const session = await getServerSession(authOptions)
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  const orgId = (session.user as { organizationId?: string }).organizationId!

  const { searchParams } = new URL(req.url)
  const status = searchParams.get('status')
  const severity = searchParams.get('severity')
  const category = searchParams.get('category')
  const nis2 = searchParams.get('nis2')
  const search = searchParams.get('search')
  const dateFrom = searchParams.get('dateFrom')
  const dateTo = searchParams.get('dateTo')
  const noOwner = searchParams.get('noOwner')
  const overdueReview = searchParams.get('overdueReview')
  const sortBy: SortField = VALID_SORT.includes(searchParams.get('sortBy') as SortField)
    ? (searchParams.get('sortBy') as SortField)
    : 'createdAt'
  const sortDir = searchParams.get('sortDir') === 'asc' ? 'asc' : 'desc'
  const page = Math.max(1, parseInt(searchParams.get('page') || '1', 10))
  const limit = Math.min(100, Math.max(1, parseInt(searchParams.get('limit') || '25', 10)))

  const where = {
    organizationId: orgId,
    deletedAt: null,
    ...(status && { status: status as 'NEW' | 'IN_PROGRESS' | 'ANALYSIS' | 'CLOSED' }),
    ...(severity && { severity: severity as 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' }),
    ...(category && { category: category as 'UNAUTHORIZED_ACCESS' | 'DATA_LEAK' | 'AVAILABILITY' | 'PHISHING' | 'MALWARE' | 'PHYSICAL' | 'OTHER' }),
    ...(nis2 === 'true' && { nis2Active: true }),
    ...(noOwner === 'true' && { assignedTo: null }),
    ...(dateFrom || dateTo ? {
      createdAt: {
        ...(dateFrom && { gte: new Date(dateFrom) }),
        ...(dateTo && { lte: new Date(dateTo + 'T23:59:59Z') }),
      },
    } : {}),
    ...(search && {
      OR: [
        { title: { contains: search, mode: 'insensitive' as const } },
        { incidentNumber: { contains: search, mode: 'insensitive' as const } },
        { reportedBy: { contains: search, mode: 'insensitive' as const } },
      ],
    }),
  }

  const [total, incidents, stats] = await Promise.all([
    prisma.incident.count({ where }),
    prisma.incident.findMany({
      where,
      include: {
        actions: { orderBy: { createdAt: 'desc' }, take: 1 },
        _count: { select: { evidences: true } },
      },
      orderBy: { [sortBy]: sortDir },
      skip: (page - 1) * limit,
      take: limit,
    }),
    // Always return global stats (unfiltered)
    prisma.incident.groupBy({
      by: ['status'],
      where: { organizationId: orgId, deletedAt: null },
      _count: { _all: true },
    }),
  ])

  const statsByStatus: Record<string, number> = {}
  for (const row of stats) {
    statsByStatus[row.status] = row._count?._all ?? 0
  }
  const openCount = (statsByStatus['NEW'] || 0) + (statsByStatus['IN_PROGRESS'] || 0) + (statsByStatus['ANALYSIS'] || 0)

  return NextResponse.json({
    data: incidents,
    total,
    page,
    limit,
    pages: Math.ceil(total / limit),
    stats: { open: openCount, closed: statsByStatus['CLOSED'] || 0 },
  })
}

export async function POST(req: Request) {
  const session = await getServerSession(authOptions)
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  const orgId = (session.user as { organizationId?: string }).organizationId!
  const userId = (session.user as { id?: string }).id!

  const body = await req.json()
  const parsed = createSchema.safeParse(body)
  if (!parsed.success) return NextResponse.json({ error: parsed.error.flatten() }, { status: 400 })

  const { assetIds, ...data } = parsed.data
  const incidentNumber = await generateIncidentNumber(orgId)

  const incident = await prisma.incident.create({
    data: {
      ...data,
      incidentNumber,
      organizationId: orgId,
      nis2StartedAt: data.nis2Active ? new Date() : null,
      assets: assetIds?.length
        ? { create: assetIds.map((assetId) => ({ assetId })) }
        : undefined,
    },
  })

  await prisma.incidentAction.create({
    data: {
      incidentId: incident.id,
      content: 'Incydent zgłoszony i zarejestrowany w systemie.',
      authorId: userId,
      authorName: session.user?.name || session.user?.email || 'System',
    },
  })

  return NextResponse.json({ data: incident }, { status: 201 })
}
