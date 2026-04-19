import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { prisma } from '@/lib/prisma'
import { z } from 'zod'
import { NextResponse } from 'next/server'

const updateSchema = z.object({
  name: z.string().min(2).max(200).optional(),
  type: z.enum(['HARDWARE', 'SOFTWARE', 'DATA', 'CLOUD_SERVICE', 'INFRASTRUCTURE', 'OTHER']).optional(),
  classification: z.enum(['PUBLIC', 'INTERNAL', 'CONFIDENTIAL', 'RESTRICTED']).optional(),
  description: z.string().optional(),
  location: z.string().optional(),
  businessOwner: z.string().optional().nullable(),
  technicalOwner: z.string().optional().nullable(),
  nextReviewAt: z.string().datetime().optional().nullable(),
})

export async function GET(
  _req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const session = await getServerSession(authOptions)
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  const orgId = (session.user as { organizationId?: string }).organizationId!

  const { id } = await params

  const asset = await prisma.asset.findFirst({
    where: { id, organizationId: orgId, deletedAt: null },
    include: {
      history: { orderBy: { createdAt: 'desc' } },
      incidents: { include: { incident: true } },
    },
  })

  if (!asset) return NextResponse.json({ error: 'Nie znaleziono' }, { status: 404 })
  return NextResponse.json({ data: asset })
}

export async function PATCH(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const session = await getServerSession(authOptions)
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  const orgId = (session.user as { organizationId?: string }).organizationId!

  const { id } = await params

  const existing = await prisma.asset.findFirst({
    where: { id, organizationId: orgId, deletedAt: null },
  })
  if (!existing) return NextResponse.json({ error: 'Nie znaleziono' }, { status: 404 })

  const body = await req.json()
  const parsed = updateSchema.safeParse(body)
  if (!parsed.success) return NextResponse.json({ error: parsed.error.flatten() }, { status: 400 })

  const changedBy = session.user?.name || session.user?.email || ''
  const historyEntries: { field: string; oldValue: string | null; newValue: string | null; changedBy: string; assetId: string }[] = []

  for (const [field, newValue] of Object.entries(parsed.data)) {
    const oldValue = (existing as Record<string, unknown>)[field]
    if (oldValue !== newValue) {
      historyEntries.push({
        field,
        oldValue: oldValue != null ? String(oldValue) : null,
        newValue: newValue != null ? String(newValue) : null,
        changedBy,
        assetId: id,
      })
    }
  }

  const updateData: Record<string, unknown> = { ...parsed.data }
  if (parsed.data.nextReviewAt) {
    updateData.nextReviewAt = new Date(parsed.data.nextReviewAt)
  }

  const asset = await prisma.asset.update({ where: { id }, data: updateData })

  if (historyEntries.length > 0) {
    await prisma.assetHistory.createMany({ data: historyEntries })
  }

  return NextResponse.json({ data: asset })
}

export async function DELETE(
  _req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const session = await getServerSession(authOptions)
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  const orgId = (session.user as { organizationId?: string }).organizationId!

  const { id } = await params

  const existing = await prisma.asset.findFirst({
    where: { id, organizationId: orgId, deletedAt: null },
  })
  if (!existing) return NextResponse.json({ error: 'Nie znaleziono' }, { status: 404 })

  await prisma.asset.update({ where: { id }, data: { deletedAt: new Date() } })
  return NextResponse.json({ success: true })
}
