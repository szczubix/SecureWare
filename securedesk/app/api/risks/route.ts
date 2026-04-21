import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { prisma } from '@/lib/prisma'
import { generateRiskNumber } from '@/lib/db-utils'
import { z } from 'zod'
import { NextResponse } from 'next/server'

const createSchema = z.object({
  title: z.string().min(3).max(200),
  description: z.string().min(5),
  threat: z.string().optional(),
  vulnerability: z.string().optional(),
  category: z.enum(['CONFIDENTIALITY', 'INTEGRITY', 'AVAILABILITY', 'PHYSICAL', 'LEGAL', 'OTHER']),
  probability: z.number().int().min(1).max(5),
  impact: z.number().int().min(1).max(5),
  treatment: z.enum(['ACCEPT', 'MITIGATE', 'TRANSFER', 'AVOID']).optional(),
  owner: z.string().min(2),
  mitigationPlan: z.string().optional(),
  residualProb: z.number().int().min(1).max(5).optional().nullable(),
  residualImpact: z.number().int().min(1).max(5).optional().nullable(),
  nextReviewAt: z.string().datetime().optional().nullable(),
  assetIds: z.array(z.string()).optional(),
})

const VALID_SORT = ['createdAt', 'riskScore', 'residualScore', 'status', 'riskNumber'] as const
type SortField = typeof VALID_SORT[number]

export async function GET(req: Request) {
  const session = await getServerSession(authOptions)
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  const orgId = (session.user as { organizationId?: string }).organizationId!

  const { searchParams } = new URL(req.url)
  const status = searchParams.get('status')
  const category = searchParams.get('category')
  const treatment = searchParams.get('treatment')
  const search = searchParams.get('search')
  const minScore = searchParams.get('minScore')
  const sortBy: SortField = VALID_SORT.includes(searchParams.get('sortBy') as SortField)
    ? (searchParams.get('sortBy') as SortField)
    : 'riskScore'
  const sortDir = searchParams.get('sortDir') === 'asc' ? 'asc' : 'desc'
  const page = Math.max(1, parseInt(searchParams.get('page') || '1', 10))
  const limit = Math.min(100, Math.max(1, parseInt(searchParams.get('limit') || '25', 10)))

  const where = {
    organizationId: orgId,
    deletedAt: null,
    ...(status && { status: status as never }),
    ...(category && { category: category as never }),
    ...(treatment && { treatment: treatment as never }),
    ...(minScore && { riskScore: { gte: parseInt(minScore, 10) } }),
    ...(search && {
      OR: [
        { title: { contains: search, mode: 'insensitive' as const } },
        { riskNumber: { contains: search, mode: 'insensitive' as const } },
        { owner: { contains: search, mode: 'insensitive' as const } },
        { threat: { contains: search, mode: 'insensitive' as const } },
      ],
    }),
  }

  const [total, risks, globalStats] = await Promise.all([
    prisma.risk.count({ where }),
    prisma.risk.findMany({
      where,
      include: {
        assets: { include: { asset: { select: { id: true, assetNumber: true, name: true } } } },
      },
      orderBy: { [sortBy]: sortDir },
      skip: (page - 1) * limit,
      take: limit,
    }),
    // Always return global stats (unfiltered)
    Promise.all([
      prisma.risk.count({ where: { organizationId: orgId, deletedAt: null } }),
      prisma.risk.count({ where: { organizationId: orgId, deletedAt: null, status: { in: ['OPEN', 'IN_TREATMENT'] } } }),
      prisma.risk.count({ where: { organizationId: orgId, deletedAt: null, riskScore: { gte: 15 } } }),
      prisma.risk.count({ where: { organizationId: orgId, deletedAt: null, nextReviewAt: { lt: new Date() } } }),
    ]),
  ])

  const [totalAll, openCount, highCount, overdueCount] = globalStats

  return NextResponse.json({
    data: risks,
    total,
    page,
    limit,
    pages: Math.ceil(total / limit),
    stats: { total: totalAll, open: openCount, high: highCount, overdue: overdueCount },
  })
}

export async function POST(req: Request) {
  const session = await getServerSession(authOptions)
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  const orgId = (session.user as { organizationId?: string }).organizationId!

  const body = await req.json()
  const parsed = createSchema.safeParse(body)
  if (!parsed.success) return NextResponse.json({ error: parsed.error.flatten() }, { status: 400 })

  const { assetIds, residualProb, residualImpact, ...data } = parsed.data
  const riskNumber = await generateRiskNumber(orgId)

  const riskScore = data.probability * data.impact
  const residualScore = residualProb && residualImpact ? residualProb * residualImpact : null

  const risk = await prisma.risk.create({
    data: {
      ...data,
      riskNumber,
      organizationId: orgId,
      riskScore,
      residualProb: residualProb ?? null,
      residualImpact: residualImpact ?? null,
      residualScore,
      nextReviewAt: data.nextReviewAt ? new Date(data.nextReviewAt) : null,
      assets: assetIds?.length
        ? { create: assetIds.map(assetId => ({ assetId })) }
        : undefined,
    },
  })

  return NextResponse.json({ data: risk }, { status: 201 })
}
