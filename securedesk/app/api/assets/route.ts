import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { prisma } from '@/lib/prisma'
import { generateAssetNumber } from '@/lib/db-utils'
import { z } from 'zod'
import { NextResponse } from 'next/server'

const createSchema = z.object({
  name: z.string().min(2).max(200),
  type: z.enum(['HARDWARE', 'SOFTWARE', 'DATA', 'CLOUD_SERVICE', 'INFRASTRUCTURE', 'OTHER']),
  classification: z.enum(['PUBLIC', 'INTERNAL', 'CONFIDENTIAL', 'RESTRICTED']),
  description: z.string().optional(),
  location: z.string().optional(),
  businessOwner: z.string().optional(),
  technicalOwner: z.string().optional(),
  nextReviewAt: z.string().datetime().optional().nullable(),
})

const VALID_SORT = ['createdAt', 'name', 'type', 'classification', 'nextReviewAt', 'assetNumber'] as const
type SortField = typeof VALID_SORT[number]

export async function GET(req: Request) {
  const session = await getServerSession(authOptions)
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  const orgId = (session.user as { organizationId?: string }).organizationId!

  const { searchParams } = new URL(req.url)
  const type = searchParams.get('type')
  const classification = searchParams.get('classification')
  const noOwner = searchParams.get('noOwner')
  const overdueReview = searchParams.get('overdueReview')
  const search = searchParams.get('search')
  const sortBy: SortField = VALID_SORT.includes(searchParams.get('sortBy') as SortField)
    ? (searchParams.get('sortBy') as SortField)
    : 'createdAt'
  const sortDir = searchParams.get('sortDir') === 'asc' ? 'asc' : 'desc'
  const page = Math.max(1, parseInt(searchParams.get('page') || '1', 10))
  const limit = Math.min(100, Math.max(1, parseInt(searchParams.get('limit') || '25', 10)))

  const where = {
    organizationId: orgId,
    deletedAt: null,
    ...(type && { type: type as 'HARDWARE' | 'SOFTWARE' | 'DATA' | 'CLOUD_SERVICE' | 'INFRASTRUCTURE' | 'OTHER' }),
    ...(classification && { classification: classification as 'PUBLIC' | 'INTERNAL' | 'CONFIDENTIAL' | 'RESTRICTED' }),
    ...(noOwner === 'true' && { businessOwner: null, technicalOwner: null }),
    ...(overdueReview === 'true' && { nextReviewAt: { lt: new Date() } }),
    ...(search && {
      OR: [
        { name: { contains: search, mode: 'insensitive' as const } },
        { assetNumber: { contains: search, mode: 'insensitive' as const } },
        { location: { contains: search, mode: 'insensitive' as const } },
        { businessOwner: { contains: search, mode: 'insensitive' as const } },
        { technicalOwner: { contains: search, mode: 'insensitive' as const } },
      ],
    }),
  }

  const [total, assets, globalStats] = await Promise.all([
    prisma.asset.count({ where }),
    prisma.asset.findMany({
      where,
      include: { _count: { select: { incidents: true } } },
      orderBy: { [sortBy]: sortDir },
      skip: (page - 1) * limit,
      take: limit,
    }),
    Promise.all([
      prisma.asset.count({ where: { organizationId: orgId, deletedAt: null } }),
      prisma.asset.count({ where: { organizationId: orgId, deletedAt: null, classification: 'RESTRICTED' } }),
      prisma.asset.count({ where: { organizationId: orgId, deletedAt: null, businessOwner: null, technicalOwner: null } }),
      prisma.asset.count({ where: { organizationId: orgId, deletedAt: null, nextReviewAt: { lt: new Date() } } }),
    ]),
  ])

  const [totalAll, restricted, noOwnerCount, overdueCount] = globalStats

  return NextResponse.json({
    data: assets,
    total,
    page,
    limit,
    pages: Math.ceil(total / limit),
    stats: { total: totalAll, restricted, noOwner: noOwnerCount, overdueReview: overdueCount },
  })
}

export async function POST(req: Request) {
  const session = await getServerSession(authOptions)
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  const orgId = (session.user as { organizationId?: string }).organizationId!

  const body = await req.json()
  const parsed = createSchema.safeParse(body)
  if (!parsed.success) return NextResponse.json({ error: parsed.error.flatten() }, { status: 400 })

  const assetNumber = await generateAssetNumber(orgId)

  const asset = await prisma.asset.create({
    data: {
      ...parsed.data,
      assetNumber,
      organizationId: orgId,
      nextReviewAt: parsed.data.nextReviewAt ? new Date(parsed.data.nextReviewAt) : null,
    },
  })

  return NextResponse.json({ data: asset }, { status: 201 })
}
