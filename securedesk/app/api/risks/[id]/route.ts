import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { prisma } from '@/lib/prisma'
import { z } from 'zod'
import { NextResponse } from 'next/server'

const updateSchema = z.object({
  title: z.string().min(3).max(200).optional(),
  description: z.string().min(5).optional(),
  threat: z.string().optional().nullable(),
  vulnerability: z.string().optional().nullable(),
  category: z.enum(['CONFIDENTIALITY', 'INTEGRITY', 'AVAILABILITY', 'PHYSICAL', 'LEGAL', 'OTHER']).optional(),
  probability: z.number().int().min(1).max(5).optional(),
  impact: z.number().int().min(1).max(5).optional(),
  treatment: z.enum(['ACCEPT', 'MITIGATE', 'TRANSFER', 'AVOID']).optional(),
  status: z.enum(['OPEN', 'IN_TREATMENT', 'ACCEPTED', 'CLOSED']).optional(),
  owner: z.string().min(2).optional(),
  mitigationPlan: z.string().optional().nullable(),
  residualProb: z.number().int().min(1).max(5).optional().nullable(),
  residualImpact: z.number().int().min(1).max(5).optional().nullable(),
  nextReviewAt: z.string().datetime().optional().nullable(),
  assetIds: z.array(z.string()).optional(),
})

export async function GET(
  _req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const session = await getServerSession(authOptions)
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  const orgId = (session.user as { organizationId?: string }).organizationId!

  const { id } = await params
  const risk = await prisma.risk.findFirst({
    where: { id, organizationId: orgId, deletedAt: null },
    include: {
      assets: { include: { asset: true } },
    },
  })

  if (!risk) return NextResponse.json({ error: 'Nie znaleziono' }, { status: 404 })
  return NextResponse.json({ data: risk })
}

export async function PATCH(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const session = await getServerSession(authOptions)
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  const orgId = (session.user as { organizationId?: string }).organizationId!

  const { id } = await params
  const existing = await prisma.risk.findFirst({
    where: { id, organizationId: orgId, deletedAt: null },
  })
  if (!existing) return NextResponse.json({ error: 'Nie znaleziono' }, { status: 404 })

  const body = await req.json()
  const parsed = updateSchema.safeParse(body)
  if (!parsed.success) return NextResponse.json({ error: parsed.error.flatten() }, { status: 400 })

  const { assetIds, ...data } = parsed.data

  const prob = data.probability ?? existing.probability
  const imp = data.impact ?? existing.impact
  const riskScore = prob * imp

  const residualProb = 'residualProb' in data ? data.residualProb : existing.residualProb
  const residualImpact = 'residualImpact' in data ? data.residualImpact : existing.residualImpact
  const residualScore = residualProb && residualImpact ? residualProb * residualImpact : null

  const updateData: Record<string, unknown> = {
    ...data,
    riskScore,
    residualScore,
    nextReviewAt: data.nextReviewAt !== undefined ? (data.nextReviewAt ? new Date(data.nextReviewAt) : null) : undefined,
  }

  if (data.status === 'CLOSED' && existing.status !== 'CLOSED') {
    updateData.closedAt = new Date()
  }

  const risk = await prisma.risk.update({ where: { id }, data: updateData })

  if (assetIds !== undefined) {
    await prisma.riskAsset.deleteMany({ where: { riskId: id } })
    if (assetIds.length > 0) {
      await prisma.riskAsset.createMany({
        data: assetIds.map(assetId => ({ riskId: id, assetId })),
      })
    }
  }

  const updated = await prisma.risk.findFirst({
    where: { id },
    include: { assets: { include: { asset: true } } },
  })

  return NextResponse.json({ data: updated })
}

export async function DELETE(
  _req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const session = await getServerSession(authOptions)
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  const orgId = (session.user as { organizationId?: string }).organizationId!

  const { id } = await params
  const existing = await prisma.risk.findFirst({
    where: { id, organizationId: orgId, deletedAt: null },
  })
  if (!existing) return NextResponse.json({ error: 'Nie znaleziono' }, { status: 404 })

  await prisma.risk.update({ where: { id }, data: { deletedAt: new Date() } })
  return NextResponse.json({ success: true })
}
