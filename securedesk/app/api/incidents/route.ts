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

export async function GET(req: Request) {
  const session = await getServerSession(authOptions)
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  const orgId = (session.user as { organizationId?: string }).organizationId!

  const { searchParams } = new URL(req.url)
  const status = searchParams.get('status')
  const severity = searchParams.get('severity')
  const nis2 = searchParams.get('nis2')
  const search = searchParams.get('search')

  const incidents = await prisma.incident.findMany({
    where: {
      organizationId: orgId,
      deletedAt: null,
      ...(status && { status: status as 'NEW' | 'IN_PROGRESS' | 'ANALYSIS' | 'CLOSED' }),
      ...(severity && { severity: severity as 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' }),
      ...(nis2 === 'true' && { nis2Active: true }),
      ...(search && {
        OR: [
          { title: { contains: search, mode: 'insensitive' } },
          { incidentNumber: { contains: search, mode: 'insensitive' } },
          { reportedBy: { contains: search, mode: 'insensitive' } },
        ],
      }),
    },
    include: {
      actions: { orderBy: { createdAt: 'desc' }, take: 1 },
      assets: { include: { asset: true } },
      _count: { select: { evidences: true } },
    },
    orderBy: { createdAt: 'desc' },
  })

  return NextResponse.json({ data: incidents })
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
